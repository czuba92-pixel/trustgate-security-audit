/* SPDX-License-Identifier: MIT
 * NEXUS Telegraph comparator — standalone wasm32-unknown-unknown.
 * The arithmetic intentionally mirrors telegraph-wasm-baseline's
 * pkg/scoring/comparator/reference.go, including saturating i64 products
 * and wrapping i64 subtraction. No host imports, network, filesystem or state.
 */
#include <stdint.h>
#include <limits.h>

static uint8_t spec_bytes[16];

__attribute__((visibility("default")))
int32_t imw_alloc(int32_t count) {
  if (count < 0 || count > (int32_t)sizeof(spec_bytes)) return 0;
  return (int32_t)(uintptr_t)spec_bytes;
}
__attribute__((visibility("default")))
void imw_free(int32_t ptr, int32_t count) { (void)ptr; (void)count; }

static uint64_t read_u64_le(const uint8_t *p) {
  uint64_t value=0;
  for (int k=7;k>=0;--k) value=(value<<8)|p[k];
  return value;
}
static int64_t wrapped_sub(int64_t a, int64_t b) {
  return (int64_t)((uint64_t)a-(uint64_t)b);
}
static int64_t wrapped_abs(int64_t v) {
  if (v>=0) return v;
  return (int64_t)(0ULL-(uint64_t)v); /* MIN_INT64 remains MIN_INT64 */
}
static int64_t sat_mul(int64_t a, int64_t b) {
  if (!a || !b) return 0;
  if (a>0) {
    if(b>0 && a>INT64_MAX/b) return INT64_MAX;
    if(b<0 && b<INT64_MIN/a) return INT64_MIN;
  } else {
    if(b>0 && a<INT64_MIN/b) return INT64_MIN;
    if(b<0 && a<INT64_MAX/b) return INT64_MAX;
  }
  return a*b;
}
/* Multiply a 64-bit unsigned value by 10000 without a compiler-rt i128 call. */
static void mul_10000(uint64_t x, uint64_t *hi, uint64_t *lo) {
  uint64_t low=(x&0xffffffffULL)*10000ULL;
  uint64_t high=(x>>32)*10000ULL;
  *lo=low+(high<<32);
  *hi=(high>>32)+(*lo<low);
}
static uint64_t div_128_by_64_sat(uint64_t hi, uint64_t lo, uint64_t d) {
  uint64_t rem=0, q=0;
  for(int i=127;i>=0;--i) {
    uint64_t bit=(i>=64 ? (hi>>(i-64)) : (lo>>i))&1ULL;
    uint64_t carry=rem>>63;
    rem=(rem<<1)|bit;
    if(carry || rem>=d) {
      rem-=d;
      if(i>=63) return (uint64_t)INT64_MAX;
      q |= (1ULL<<i);
    }
  }
  return q>(uint64_t)INT64_MAX?(uint64_t)INT64_MAX:q;
}
static int64_t decay(int64_t err, int64_t tol) {
  if (tol<=0) return err==0 ? 10000 : 0;
  int64_t window=sat_mul(tol,2);
  if (err>=window) return 0;
  int64_t remaining=wrapped_sub(window,err);
  return sat_mul(10000,remaining)/window;
}
__attribute__((visibility("default")))
int64_t imw_score_deterministic(int64_t truth, int64_t miner, int32_t spec_ptr) {
  if(spec_ptr!=(int32_t)(uintptr_t)spec_bytes) return -1;
  int64_t code=(int64_t)read_u64_le(spec_bytes);
  int64_t tolerance=(int64_t)read_u64_le(spec_bytes+8);
  int32_t kind=(int32_t)code;
  int64_t diff=wrapped_abs(wrapped_sub(miner,truth));
  if(kind==1) return decay(diff,tolerance);
  if(kind==2){
    int64_t den=wrapped_abs(truth);
    if(den<1)den=1;
    /* Saturation and sign exactly follow the official i128 reference rule. */
    uint64_t magnitude=(uint64_t)(diff<0?0ULL-(uint64_t)diff:(uint64_t)diff);
    uint64_t hi,lo;
    mul_10000(magnitude,&hi,&lo);
    uint64_t q=div_128_by_64_sat(hi,lo,(uint64_t)den);
    int64_t relative_error= diff<0?-(int64_t)q:(int64_t)q;
    return decay(relative_error,tolerance);
  }
  return miner==truth ? 10000 : 0;
}
