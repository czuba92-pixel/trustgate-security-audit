#!/usr/bin/env python3
import argparse, gzip, hashlib, json, pathlib, time, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE='https://1f916.ai'
UA='tradebot-proof-2f624796d955/listing39-independent-replication-v1'

def fetch(path, params, page_dir, label, index, pause=0.18):
    q=urllib.parse.urlencode(params)
    url=BASE+path+('?' + q if q else '')
    req=urllib.request.Request(url, headers={'User-Agent':UA,'Accept':'application/json'})
    last=None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                status=r.status; raw=r.read()
            if status != 200: raise RuntimeError(f'HTTP {status} {url}')
            data=json.loads(raw)
            sha=hashlib.sha256(raw).hexdigest()
            page_dir.mkdir(parents=True,exist_ok=True)
            fn=page_dir/f'{label}-{index:04d}.json.gz'
            with gzip.open(fn,'wb',compresslevel=9) as g:g.write(raw)
            time.sleep(pause)
            return data, {'label':label,'index':index,'url':url,'sha256':sha,'bytes':len(raw),'file':str(fn.name)}
        except Exception as e:
            last=e
            if attempt==3: raise
            time.sleep(0.6*(attempt+1))
    raise last

def add_unique(dst, rows, key, label):
    for row in rows:
        if not isinstance(row,dict) or key not in row: raise RuntimeError(f'{label}: missing {key}')
        k=row[key]
        if k in dst:
            if dst[k] != row: raise RuntimeError(f'{label}: conflicting duplicate {key}={k}')
        else: dst[k]=row

def collect_paged(path, params, rows_key, key, cursor_key, label, page_dir, manifest):
    out={}; cursor=params.get('since',0); totals=[]; idx=0; seen=set()
    while True:
        p=dict(params); p['since']=cursor
        data,m=fetch(path,p,page_dir,label,idx); manifest.append(m); idx+=1
        rows=data.get(rows_key)
        if not isinstance(rows,list): raise RuntimeError(f'{label}: {rows_key} not list')
        add_unique(out,rows,key,label)
        total=data.get('total')
        if isinstance(total,int): totals.append(total)
        more=bool(data.get('has_more'))
        if not more:
            # Same response must reconcile its declared total.
            if isinstance(total,int) and len(out)!=total:
                # The source can move while walking. Perform one incremental continuation;
                # only accept when a later terminal response reconciles exactly.
                nxt=data.get(cursor_key)
                if nxt is None: raise RuntimeError(f'{label}: terminal total mismatch {len(out)} != {total}, no cursor')
                if nxt==cursor: raise RuntimeError(f'{label}: terminal total mismatch with stalled cursor')
                cursor=nxt
                if cursor in seen: raise RuntimeError(f'{label}: cursor loop')
                seen.add(cursor)
                continue
            return list(out.values()), {'pages':idx,'declared_totals':totals,'final_total':total,'collected':len(out)}
        nxt=data.get(cursor_key)
        if nxt is None or nxt==cursor: raise RuntimeError(f'{label}: invalid next cursor {nxt}')
        if nxt in seen: raise RuntimeError(f'{label}: cursor loop {nxt}')
        seen.add(nxt); cursor=nxt

def collect_changes(page_dir,manifest):
    posts={}; comments={}; idx=0
    ps='init'; cs='init'; snapshot_meta=None
    while True:
        params={'since':'0','posts_since':ps,'comments_since':cs,'nulls_since':'done'}
        data,m=fetch('/api/changes',params,page_dir,'changes',idx); manifest.append(m); idx+=1
        if data.get('next_nulls_since')!='done': raise RuntimeError('changes: nulls stream not durably silenced')
        more=set(data.get('has_more_streams') or [])
        covers=set(data.get('continuation_covers') or [])
        if not more.issubset(covers): raise RuntimeError(f'changes: lossy continuation more={more} covers={covers}')
        add_unique(posts,data.get('posts') or [],'id','posts')
        add_unique(comments,data.get('comments') or [],'id','comments')
        nps=data.get('next_posts_since'); ncs=data.get('next_comments_since')
        if idx==1:
            snapshot_meta={'now':data.get('now'),'now_utc':data.get('now_utc'),'first_next_posts_since':nps,'first_next_comments_since':ncs,'cursor_note_sha256':hashlib.sha256(str(data.get('cursor_note','')).encode()).hexdigest()}
        if not data.get('has_more'):
            return list(posts.values()),list(comments.values()),{'pages':idx,'posts':len(posts),'comments':len(comments),'snapshot':snapshot_meta,'final_posts_cursor':nps,'final_comments_cursor':ncs}
        if nps is None or ncs is None: raise RuntimeError('changes: missing lossless cursor')
        if nps==ps and ncs==cs: raise RuntimeError('changes: both cursors stalled')
        ps,cs=nps,ncs
        if idx>1000: raise RuntimeError('changes: page guard exceeded')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='snapshot.json.gz'); ap.add_argument('--pages',default='data/pages')
    a=ap.parse_args(); root=pathlib.Path(__file__).resolve().parent; page_dir=root/a.pages
    manifest=[]; started=datetime.now(timezone.utc).isoformat()
    citizens,cmeta=collect_paged('/api/citizens',{},'citizens','citizen_id','next_since','citizens',page_dir,manifest)
    events,emeta=collect_paged('/api/events',{'kind':'key-bind'},'events','id','next_since','keybind',page_dir,manifest)
    posts,comments,chmeta=collect_changes(page_dir,manifest)
    stats,sm=fetch('/api/stats',{},page_dir,'stats',0,pause=0); manifest.append(sm)
    society=(stats.get('society') or {})
    # Reconcile exact snapshot row counts where the stats snapshot agrees with our change snapshot.
    stats_reconciliation={
      'citizens_stats':society.get('citizens'),'citizens_collected':len(citizens),
      'posts_stats':society.get('posts'),'posts_collected':len(posts),
      'comments_stats':society.get('comments'),'comments_collected':len(comments),
      'keybind_endpoint_total':emeta.get('final_total'),'keybind_collected':len(events),
    }
    # Census/events are required exact against their own terminal total. Changes are snapshot-bounded;
    # accept stats equality when the independently sampled stats did not move past the snapshot.
    if cmeta.get('final_total')!=len(citizens): raise RuntimeError('citizens final total mismatch')
    if emeta.get('final_total')!=len(events): raise RuntimeError('key-bind final total mismatch')
    # If stats are different because source moved, record rather than fabricate equality.
    payload={
      'schema':1,'source':BASE,'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
      'citizens':citizens,'keybind_events':events,'posts':posts,'comments':comments,
      'collection':{'citizens':cmeta,'keybind':emeta,'changes':chmeta,'stats_reconciliation':stats_reconciliation,'page_manifest':manifest},
      'stats':stats,
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    out=root/a.out
    with gzip.open(out,'wb',compresslevel=9) as g:g.write(raw)
    digest=hashlib.sha256(raw).hexdigest()
    state={'status':'COLLECTED','snapshot_uncompressed_sha256':digest,'snapshot_gzip':out.name,'counts':{'citizens':len(citizens),'keybind_events':len(events),'posts':len(posts),'comments':len(comments)},'collection':payload['collection'],'finished_at_utc':payload['finished_at_utc']}
    (root/'collection_state.json').write_text(json.dumps(state,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'COLLECTED','sha256':digest,'counts':state['counts'],'pages':{'citizens':cmeta['pages'],'keybind':emeta['pages'],'changes':chmeta['pages']},'stats_reconciliation':stats_reconciliation},sort_keys=True))
if __name__=='__main__': main()
