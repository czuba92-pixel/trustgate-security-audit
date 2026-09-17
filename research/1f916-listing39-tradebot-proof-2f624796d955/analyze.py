#!/usr/bin/env python3
import argparse,csv,gzip,hashlib,json,math,pathlib
from datetime import datetime,timezone,timedelta
from fractions import Fraction

START_MS=int(datetime(2026,8,12,21,33,32,tzinfo=timezone.utc).timestamp()*1000)
CUTOFF_MS=int(datetime(2026,9,3,0,0,0,tzinfo=timezone.utc).timestamp()*1000)
DAY=86400000

def ms(v):
    if isinstance(v,(int,float)):
        x=int(v); return x if x>10_000_000_000 else x*1000
    if isinstance(v,str):
        s=v.replace('Z','+00:00'); return int(datetime.fromisoformat(s).timestamp()*1000)
    raise ValueError(f'unsupported timestamp {v!r}')

def wilson(k,n,z=1.959963984540054):
    if n<=0:return [None,None]
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def newcombe(k1,n1,k2,n2):
    p1=k1/n1; p2=k2/n2; l1,u1=wilson(k1,n1); l2,u2=wilson(k2,n2); d=p1-p2
    lo=d-math.sqrt((p1-l1)**2+(u2-p2)**2)
    hi=d+math.sqrt((u1-p1)**2+(p2-l2)**2)
    return [lo,hi]

def largest_gap(delays, cohort_delays=None):
    xs=sorted(delays)
    pairs=[]; best=None
    for a,b in zip(xs,xs[1:]):
        if a<=0 or b<=a: continue
        r=Fraction(b,a)
        if best is None or r>best: best=r; pairs=[(a,b)]
        elif r==best:pairs.append((a,b))
    if not pairs: raise RuntimeError('no natural positive ratio gap')
    thresholds=sorted({a for a,b in pairs})
    if len(thresholds)>1 and cohort_delays is not None:
        assignments=[tuple(d<=t for d in cohort_delays) for t in thresholds]
        if len(set(assignments))>1: raise RuntimeError(f'ambiguous tied max gaps induce different assignments: {pairs}')
    a,b=pairs[0]
    return {'lower_ms':a,'upper_ms':b,'ratio':float(Fraction(b,a)),'ties':[list(x) for x in pairs]}

def arm_stats(rows, outcome_start_days=7, freeze_bind_at_day7=False):
    out={a:{'n':0,'k':0} for a in ['door','sought','none']}
    for r in rows:
        arm=r['arm']
        if freeze_bind_at_day7 and r['first_bind_ms'] is not None and r['first_bind_ms']>=r['registered_ms']+7*DAY:
            arm='none'
        start=r['registered_ms']+outcome_start_days*DAY; end=r['registered_ms']+14*DAY
        retained=any(start<=t<end for t in r['activity_ms'])
        out[arm]['n']+=1; out[arm]['k']+=int(retained)
    for a,v in out.items():
        v['rate']=v['k']/v['n'] if v['n'] else None; v['wilson95']=wilson(v['k'],v['n'])
    pairs={}
    for a,b in [('door','sought'),('door','none'),('sought','none')]:
        x,y=out[a],out[b]
        if not x['n'] or not y['n']:
            pairs[f'{a}_minus_{b}']={'difference':None,'newcombe95':[None,None]}
        else:
            pairs[f'{a}_minus_{b}']={'difference':x['rate']-y['rate'],'newcombe95':newcombe(x['k'],x['n'],y['k'],y['n'])}
    return {'arms':out,'pairwise':pairs}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshot',default='snapshot.json.gz'); a=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parent
    with gzip.open(root/a.snapshot,'rb') as g: raw=g.read()
    d=json.loads(raw); citizens=d['citizens']; events=d['keybind_events']; posts=d['posts']; comments=d['comments']
    by_id={int(c['citizen_id']):c for c in citizens}; by_handle={c['handle']:c for c in citizens}
    if len(by_id)!=len(citizens) or len(by_handle)!=len(citizens): raise RuntimeError('citizen identity duplicate')
    reg={h:ms(c['created_at']) for h,c in by_handle.items()}
    first_bind={}; orphan=[]; negative=[]
    for e in sorted(events,key=lambda x:int(x['id'])):
        h=e.get('citizen')
        if h not in reg: orphan.append({'event_id':e['id'],'citizen':h}); continue
        t=ms(e['created_at']); first_bind.setdefault(h,t)
    for h,t in first_bind.items():
        if t-reg[h]<0: negative.append({'handle':h,'delay_ms':t-reg[h]})
    if orphan: raise RuntimeError(f'orphan keybind events: {len(orphan)}')
    if negative: raise RuntimeError(f'negative keybind delays: {len(negative)}')
    all_delays=[t-reg[h] for h,t in first_bind.items()]
    cohort_handles=sorted(h for h,r in reg.items() if START_MS<=r<CUTOFF_MS)
    cohort_delays=[first_bind[h]-reg[h] for h in cohort_handles if h in first_bind]
    global_gap=largest_gap(all_delays,cohort_delays)
    cohort_gap=largest_gap(cohort_delays,cohort_delays)
    threshold=global_gap['lower_ms']
    activity={h:[] for h in cohort_handles}
    missing_required=[]
    for typ,rows in [('post',posts),('comment',comments)]:
        for x in rows:
            h=x.get('author'); t=x.get('created_at')
            if h is None or t is None:
                missing_required.append({'type':typ,'id':x.get('id')}); continue
            if h in activity: activity[h].append(ms(t))
    if missing_required: raise RuntimeError(f'missing required activity fields: {len(missing_required)}')
    rows=[]
    for h in cohort_handles:
        fb=first_bind.get(h); delay=None if fb is None else fb-reg[h]
        arm='none' if delay is None else ('door' if delay<=threshold else 'sought')
        rows.append({'handle':h,'registered_ms':reg[h],'first_bind_ms':fb,'delay_ms':delay,'arm':arm,'activity_ms':sorted(activity[h])})
    primary=arm_stats(rows,7,False); alternate=arm_stats(rows,8,False); exposure=arm_stats(rows,7,True)
    cthreshold=cohort_gap['lower_ms']; changed=sum(1 for r in rows if r['delay_ms'] is not None and ((r['delay_ms']<=threshold)!=(r['delay_ms']<=cthreshold)))
    coll=d['collection']; stats_rec=coll['stats_reconciliation']
    completeness={
      'citizens_endpoint_exact':coll['citizens']['final_total']==coll['citizens']['collected'],
      'keybind_endpoint_exact':coll['keybind']['final_total']==coll['keybind']['collected'],
      'changes_snapshot_posts':coll['changes']['posts'],
      'changes_snapshot_comments':coll['changes']['comments'],
      'stats_reconciliation':stats_rec,
      'stats_exact_at_sample':stats_rec.get('posts_stats')==stats_rec.get('posts_collected') and stats_rec.get('comments_stats')==stats_rec.get('comments_collected'),
      'orphan_keybinds':len(orphan),'negative_bind_delays':len(negative),'missing_activity_required_fields':len(missing_required),
    }
    result={
      'schema':1,'listing_id':39,'snapshot_uncompressed_sha256':hashlib.sha256(raw).hexdigest(),
      'population':{'start_ms':START_MS,'cutoff_ms':CUTOFF_MS,'n':len(rows)},
      'boundary':{'primary_global':global_gap,'cohort_sensitivity':cohort_gap,'cohort_assignment_changes':changed},
      'primary_days_8_14_as_reg_plus_7d_to_14d':primary,
      'alternate_reg_plus_8d_to_14d':alternate,
      'exposure_frozen_at_reg_plus_7d':exposure,
      'completeness':completeness,
      'limitations':['observational association only; onboarding path is not randomized','prior aggregate submission summaries were visible during opportunity qualification; no competitor row-level data/code/artifacts were used'],
    }
    (root/'results.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    with gzip.open(root/'cohort.csv.gz','wt',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['handle','registered_ms','first_bind_ms','delay_ms','arm','primary_retained','alternate_retained'])
        for r in rows:
            p=any(r['registered_ms']+7*DAY<=t<r['registered_ms']+14*DAY for t in r['activity_ms'])
            q=any(r['registered_ms']+8*DAY<=t<r['registered_ms']+14*DAY for t in r['activity_ms'])
            w.writerow([r['handle'],r['registered_ms'],r['first_bind_ms'],r['delay_ms'],r['arm'],int(p),int(q)])
    def pct(x):return 'NA' if x is None else f'{100*x:.2f}%'
    lines=['# Listing 39 independent replication — report','',f"Snapshot SHA-256: `{result['snapshot_uncompressed_sha256']}`",f"Population: n={len(rows)}; [2026-08-12T21:33:32Z, 2026-09-03T00:00:00Z)",'',
      f"Derived global largest bind-delay gap: {global_gap['lower_ms']} ms -> {global_gap['upper_ms']} ms ({global_gap['ratio']:.4f}x).",
      f"Cohort-only gap: {cohort_gap['lower_ms']} ms -> {cohort_gap['upper_ms']} ms ({cohort_gap['ratio']:.4f}x); cohort arm assignment changes vs primary: {changed}.",'','## Primary outcome: [registration+7d, registration+14d)','']
    for arm in ['door','sought','none']:
        v=primary['arms'][arm]; lines.append(f"- {arm}: {v['k']}/{v['n']} = {pct(v['rate'])}; Wilson 95% [{pct(v['wilson95'][0])}, {pct(v['wilson95'][1])}]")
    lines += ['','Pairwise differences (first minus second):']
    for name,v in primary['pairwise'].items():lines.append(f"- {name}: {100*v['difference']:+.2f} pp; Newcombe 95% [{100*v['newcombe95'][0]:+.2f}, {100*v['newcombe95'][1]:+.2f}] pp")
    lines += ['','## Sensitivities','', 'Alternate outcome window [registration+8d, registration+14d):']
    for arm in ['door','sought','none']:
        v=alternate['arms'][arm]; lines.append(f"- {arm}: {v['k']}/{v['n']} = {pct(v['rate'])}")
    lines += ['','Exposure frozen at registration+7d (late binders treated as none for sensitivity):']
    for arm in ['door','sought','none']:
        v=exposure['arms'][arm]; lines.append(f"- {arm}: {v['k']}/{v['n']} = {pct(v['rate'])}")
    lines += ['','## Completeness','',f"- Citizens endpoint: {coll['citizens']['collected']}/{coll['citizens']['final_total']} rows; pages={coll['citizens']['pages']}",f"- Key-bind endpoint: {coll['keybind']['collected']}/{coll['keybind']['final_total']} rows; pages={coll['keybind']['pages']}",f"- Lossless changes snapshot: posts={coll['changes']['posts']}, comments={coll['changes']['comments']}, pages={coll['changes']['pages']}",f"- Stats sampled after walk: posts={stats_rec.get('posts_stats')}, comments={stats_rec.get('comments_stats')}, citizens={stats_rec.get('citizens_stats')}",f"- Orphan key-binds={len(orphan)}, negative delays={len(negative)}, missing required activity fields={len(missing_required)}",'', '## Interpretation boundary','', 'This is an association, not a causal estimate. Registration path was not randomized. Prior aggregate submission summaries were visible before this independent walk; no competitor row-level data, code, caches, or artifacts were used. See PROTOCOL.md for pre-specified falsifiers and sensitivity rules.','']
    (root/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'status':'ANALYZED','population_n':len(rows),'global_gap':global_gap,'cohort_gap':cohort_gap,'primary':primary,'completeness':completeness},sort_keys=True))
if __name__=='__main__':main()
