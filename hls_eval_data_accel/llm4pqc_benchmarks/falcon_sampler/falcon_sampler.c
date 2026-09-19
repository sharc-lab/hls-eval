/* Standalone reconstruction; see README.md and sources.json. */
/*
 * Falcon signature verification.
 *
 * ==========================(LICENSE BEGIN)============================
 *
 * Copyright (c) 2017-2019  Falcon Project
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * ===========================(LICENSE END)=============================
 *
 * @author   Thomas Pornin <thomas.pornin@nccgroup.com>
 */

/*
 * This file used to pull in config.h/inner.h/fpr.h from the full Falcon
 * reference tree. Those headers declare the entire Falcon API (keygen,
 * signing, verification, FFT, SHAKE256, encode/decode, ...); this kernel
 * only ever needs the PRNG plumbing and the small slice of the 'fpr'
 * (integer-emulated IEEE-754 binary64) support code that the Gaussian
 * sampler itself calls. Everything below is that slice, folded in
 * directly and with the unused 90% of those headers dropped -- see
 * kernel_description.md for the original provenance.
 */

#include <stdint.h>
#include <string.h>

/* ====================================================================== */
/*
 * FALCON_FPEMU support code, extracted verbatim from the upstream Falcon
 * reference implementation's fpr.c/fpr.h (Falcon-impl-20211101), trimmed
 * to the 'fpr' functions and constants this kernel actually calls
 * (fpr_scaled/fpr_of, fpr_add/fpr_sub, fpr_mul/fpr_sqr, fpr_half,
 * fpr_floor, fpr_trunc, fpr_expm_p63, and the fpr_log2/fpr_inv_log2/
 * fpr_inv_2sqrsigma0/fpr_ptwo63 constants). See kernel_description.md.
 */
typedef uint64_t fpr;

/*
 * Right-shift/left-shift a 64-bit value by a possibly secret shift count
 * (see the original fpr.c for the constant-time rationale). Shift count
 * n MUST be in the 0..63 range.
 */
static inline uint64_t
fpr_ursh(uint64_t x, int n)
{
	x ^= (x ^ (x >> 32)) & -(uint64_t)(n >> 5);
	return x >> (n & 31);
}

static inline int64_t
fpr_irsh(int64_t x, int n)
{
	x ^= (x ^ (x >> 32)) & -(int64_t)(n >> 5);
	return x >> (n & 31);
}

static inline uint64_t
fpr_ulsh(uint64_t x, int n)
{
	x ^= (x ^ (x << 32)) & -(uint64_t)(n >> 5);
	return x << (n & 31);
}

/*
 * Normalize a provided unsigned integer to the 2^63..2^64-1 range by
 * left-shifting it if necessary. The exponent e is adjusted accordingly
 * (i.e. if the value was left-shifted by n bits, then n is subtracted
 * from e). If source m is 0, then it remains 0, but e is altered.
 * Both m and e must be simple variables (no expressions allowed).
 */
#define FPR_NORM64(m, e)   do { \
		uint32_t nt; \
 \
		(e) -= 63; \
 \
		nt = (uint32_t)((m) >> 32); \
		nt = (nt | -nt) >> 31; \
		(m) ^= ((m) ^ ((m) << 32)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt << 5); \
 \
		nt = (uint32_t)((m) >> 48); \
		nt = (nt | -nt) >> 31; \
		(m) ^= ((m) ^ ((m) << 16)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt << 4); \
 \
		nt = (uint32_t)((m) >> 56); \
		nt = (nt | -nt) >> 31; \
		(m) ^= ((m) ^ ((m) <<  8)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt << 3); \
 \
		nt = (uint32_t)((m) >> 60); \
		nt = (nt | -nt) >> 31; \
		(m) ^= ((m) ^ ((m) <<  4)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt << 2); \
 \
		nt = (uint32_t)((m) >> 62); \
		nt = (nt | -nt) >> 31; \
		(m) ^= ((m) ^ ((m) <<  2)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt << 1); \
 \
		nt = (uint32_t)((m) >> 63); \
		(m) ^= ((m) ^ ((m) <<  1)) & ((uint64_t)nt - 1); \
		(e) += (int)(nt); \
	} while (0)

/*
 * Expectations:
 *   s = 0 or 1
 *   exponent e is "arbitrary" and unbiased
 *   2^54 <= m < 2^55
 * Numerical value is (-1)^2 * m * 2^e
 *
 * Exponents which are too low lead to value zero. If the exponent is
 * too large, the returned value is indeterminate.
 *
 * If m = 0, then a zero is returned (using the provided sign).
 * If e < -1076, then a zero is returned (regardless of the value of m).
 * If e >= -1076 and e != 0, m must be within the expected range
 * (2^54 to 2^55-1).
 */
static inline fpr
FPR(int s, int e, uint64_t m)
{
	fpr x;
	uint32_t t;
	unsigned f;

	/*
	 * If e >= -1076, then the value is "normal"; otherwise, it
	 * should be a subnormal, which we clamp down to zero.
	 */
	e += 1076;
	t = (uint32_t)e >> 31;
	m &= (uint64_t)t - 1;

	/*
	 * If m = 0 then we want a zero; make e = 0 too, but conserve
	 * the sign.
	 */
	t = (uint32_t)(m >> 54);
	e &= -(int)t;

	/*
	 * The 52 mantissa bits come from m. Value m has its top bit set
	 * (unless it is a zero); we leave it "as is": the top bit will
	 * increment the exponent by 1, except when m = 0, which is
	 * exactly what we want.
	 */
	x = (((uint64_t)s << 63) | (m >> 2)) + ((uint64_t)(uint32_t)e << 52);

	/*
	 * Rounding: if the low three bits of m are 011, 110 or 111,
	 * then the value should be incremented to get the next
	 * representable value. This implements the usual
	 * round-to-nearest rule (with preference to even values in case
	 * of a tie). Note that the increment may make a carry spill
	 * into the exponent field, which is again exactly what we want
	 * in that case.
	 */
	f = (unsigned)m & 7U;
	x += (0xC8U >> f) & 1;
	return x;
}

static const fpr fpr_inv_2sqrsigma0 = 4594603506513722306;
static const fpr fpr_log2 = 4604418534313441775;
static const fpr fpr_inv_log2 = 4609176140021203710;
static const fpr fpr_ptwo63 = 4890909195324358656;

fpr
fpr_scaled(int64_t i, int sc)
{
	/*
	 * To convert from int to float, we have to do the following:
	 *  1. Get the absolute value of the input, and its sign
	 *  2. Shift right or left the value as appropriate
	 *  3. Pack the result
	 *
	 * We can assume that the source integer is not -2^63.
	 */
	int s, e;
	uint32_t t;
	uint64_t m;

	/*
	 * Extract sign bit.
	 * We have: -i = 1 + ~i
	 */
	s = (int)((uint64_t)i >> 63);
	i ^= -(int64_t)s;
	i += s;

	/*
	 * For now we suppose that i != 0.
	 * Otherwise, we set m to i and left-shift it as much as needed
	 * to get a 1 in the top bit. We can do that in a logarithmic
	 * number of conditional shifts.
	 */
	m = (uint64_t)i;
	e = 9 + sc;
	FPR_NORM64(m, e);

	/*
	 * Now m is in the 2^63..2^64-1 range. We must divide it by 512;
	 * if one of the dropped bits is a 1, this should go into the
	 * "sticky bit".
	 */
	m |= ((uint32_t)m & 0x1FF) + 0x1FF;
	m >>= 9;

	/*
	 * Corrective action: if i = 0 then all of the above was
	 * incorrect, and we clamp e and m down to zero.
	 */
	t = (uint32_t)((uint64_t)(i | -i) >> 63);
	m &= -(uint64_t)t;
	e &= -(int)t;

	/*
	 * Assemble back everything. The FPR() function will handle cases
	 * where e is too low.
	 */
	return FPR(s, e, m);
}

static inline fpr
fpr_of(int64_t i)
{
	return fpr_scaled(i, 0);
}

fpr
fpr_add(fpr x, fpr y)
{
	uint64_t m, xu, yu, za;
	uint32_t cs;
	int ex, ey, sx, sy, cc;

	/*
	 * Make sure that the first operand (x) has the larger absolute
	 * value. This guarantees that the exponent of y is less than
	 * or equal to the exponent of x, and, if they are equal, then
	 * the mantissa of y will not be greater than the mantissa of x.
	 *
	 * After this swap, the result will have the sign x, except in
	 * the following edge case: abs(x) = abs(y), and x and y have
	 * opposite sign bits; in that case, the result shall be +0
	 * even if the sign bit of x is 1. To handle this case properly,
	 * we do the swap is abs(x) = abs(y) AND the sign of x is 1.
	 */
	m = ((uint64_t)1 << 63) - 1;
	za = (x & m) - (y & m);
	cs = (uint32_t)(za >> 63)
		| ((1U - (uint32_t)(-za >> 63)) & (uint32_t)(x >> 63));
	m = (x ^ y) & -(uint64_t)cs;
	x ^= m;
	y ^= m;

	/*
	 * Extract sign bits, exponents and mantissas. The mantissas are
	 * scaled up to 2^55..2^56-1, and the exponent is unbiased. If
	 * an operand is zero, its mantissa is set to 0 at this step, and
	 * its exponent will be -1078.
	 */
	ex = (int)(x >> 52);
	sx = ex >> 11;
	ex &= 0x7FF;
	m = (uint64_t)(uint32_t)((ex + 0x7FF) >> 11) << 52;
	xu = ((x & (((uint64_t)1 << 52) - 1)) | m) << 3;
	ex -= 1078;
	ey = (int)(y >> 52);
	sy = ey >> 11;
	ey &= 0x7FF;
	m = (uint64_t)(uint32_t)((ey + 0x7FF) >> 11) << 52;
	yu = ((y & (((uint64_t)1 << 52) - 1)) | m) << 3;
	ey -= 1078;

	/*
	 * x has the larger exponent; hence, we only need to right-shift y.
	 * If the shift count is larger than 59 bits then we clamp the
	 * value to zero.
	 */
	cc = ex - ey;
	yu &= -(uint64_t)((uint32_t)(cc - 60) >> 31);
	cc &= 63;

	/*
	 * The lowest bit of yu is "sticky".
	 */
	m = fpr_ulsh(1, cc) - 1;
	yu |= (yu & m) + m;
	yu = fpr_ursh(yu, cc);

	/*
	 * If the operands have the same sign, then we add the mantissas;
	 * otherwise, we subtract the mantissas.
	 */
	xu += yu - ((yu << 1) & -(uint64_t)(sx ^ sy));

	/*
	 * The result may be smaller, or slightly larger. We normalize
	 * it to the 2^63..2^64-1 range (if xu is zero, then it stays
	 * at zero).
	 */
	FPR_NORM64(xu, ex);

	/*
	 * Scale down the value to 2^54..s^55-1, handling the last bit
	 * as sticky.
	 */
	xu |= ((uint32_t)xu & 0x1FF) + 0x1FF;
	xu >>= 9;
	ex += 9;

	/*
	 * In general, the result has the sign of x. However, if the
	 * result is exactly zero, then the following situations may
	 * be encountered:
	 *   x > 0, y = -x   -> result should be +0
	 *   x < 0, y = -x   -> result should be +0
	 *   x = +0, y = +0  -> result should be +0
	 *   x = -0, y = +0  -> result should be +0
	 *   x = +0, y = -0  -> result should be +0
	 *   x = -0, y = -0  -> result should be -0
	 *
	 * But at the conditional swap step at the start of the
	 * function, we ensured that if abs(x) = abs(y) and the
	 * sign of x was 1, then x and y were swapped. Thus, the
	 * two following cases cannot actually happen:
	 *   x < 0, y = -x
	 *   x = -0, y = +0
	 * In all other cases, the sign bit of x is conserved, which
	 * is what the FPR() function does. The FPR() function also
	 * properly clamps values to zero when the exponent is too
	 * low, but does not alter the sign in that case.
	 */
	return FPR(sx, ex, xu);
}

static inline fpr
fpr_sub(fpr x, fpr y)
{
	y ^= (uint64_t)1 << 63;
	return fpr_add(x, y);
}

static inline fpr
fpr_half(fpr x)
{
	/*
	 * To divide a value by 2, we just have to subtract 1 from its
	 * exponent, but we have to take care of zero.
	 */
	uint32_t t;

	x -= (uint64_t)1 << 52;
	t = (((uint32_t)(x >> 52) & 0x7FF) + 1) >> 11;
	x &= (uint64_t)t - 1;
	return x;
}

fpr
fpr_mul(fpr x, fpr y)
{
	uint64_t xu, yu, w, zu, zv;
	uint32_t x0, x1, y0, y1, z0, z1, z2;
	int ex, ey, d, e, s;

	/*
	 * Extract absolute values as scaled unsigned integers. We
	 * don't extract exponents yet.
	 */
	xu = (x & (((uint64_t)1 << 52) - 1)) | ((uint64_t)1 << 52);
	yu = (y & (((uint64_t)1 << 52) - 1)) | ((uint64_t)1 << 52);

	/*
	 * We have two 53-bit integers to multiply; we need to split
	 * each into a lower half and a upper half. Moreover, we
	 * prefer to have lower halves to be of 25 bits each, for
	 * reasons explained later on.
	 */
	x0 = (uint32_t)xu & 0x01FFFFFF;
	x1 = (uint32_t)(xu >> 25);
	y0 = (uint32_t)yu & 0x01FFFFFF;
	y1 = (uint32_t)(yu >> 25);
	w = (uint64_t)x0 * (uint64_t)y0;
	z0 = (uint32_t)w & 0x01FFFFFF;
	z1 = (uint32_t)(w >> 25);
	w = (uint64_t)x0 * (uint64_t)y1;
	z1 += (uint32_t)w & 0x01FFFFFF;
	z2 = (uint32_t)(w >> 25);
	w = (uint64_t)x1 * (uint64_t)y0;
	z1 += (uint32_t)w & 0x01FFFFFF;
	z2 += (uint32_t)(w >> 25);
	zu = (uint64_t)x1 * (uint64_t)y1;
	z2 += (z1 >> 25);
	z1 &= 0x01FFFFFF;
	zu += z2;

	/*
	 * Since xu and yu are both in the 2^52..2^53-1 range, the
	 * product is in the 2^104..2^106-1 range. We first reassemble
	 * it and round it into the 2^54..2^56-1 range; the bottom bit
	 * is made "sticky". Since the low limbs z0 and z1 are 25 bits
	 * each, we just take the upper part (zu), and consider z0 and
	 * z1 only for purposes of stickiness.
	 * (This is the reason why we chose 25-bit limbs above.)
	 */
	zu |= ((z0 | z1) + 0x01FFFFFF) >> 25;

	/*
	 * We normalize zu to the 2^54..s^55-1 range: it could be one
	 * bit too large at this point. This is done with a conditional
	 * right-shift that takes into account the sticky bit.
	 */
	zv = (zu >> 1) | (zu & 1);
	w = zu >> 55;
	zu ^= (zu ^ zv) & -w;

	/*
	 * Get the aggregate scaling factor:
	 *
	 *   - Each exponent is biased by 1023.
	 *
	 *   - Integral mantissas are scaled by 2^52, hence an
	 *     extra 52 bias for each exponent.
	 *
	 *   - However, we right-shifted z by 50 bits, and then
	 *     by 0 or 1 extra bit (depending on the value of w).
	 *
	 * In total, we must add the exponents, then subtract
	 * 2 * (1023 + 52), then add 50 + w.
	 */
	ex = (int)((x >> 52) & 0x7FF);
	ey = (int)((y >> 52) & 0x7FF);
	e = ex + ey - 2100 + (int)w;

	/*
	 * Sign bit is the XOR of the operand sign bits.
	 */
	s = (int)((x ^ y) >> 63);

	/*
	 * Corrective actions for zeros: if either of the operands is
	 * zero, then the computations above were wrong. Test for zero
	 * is whether ex or ey is zero. We just have to set the mantissa
	 * (zu) to zero, the FPR() function will normalize e.
	 */
	d = ((ex + 0x7FF) & (ey + 0x7FF)) >> 11;
	zu &= -(uint64_t)d;

	/*
	 * FPR() packs the result and applies proper rounding.
	 */
	return FPR(s, e, zu);
}

static inline fpr
fpr_sqr(fpr x)
{
	return fpr_mul(x, x);
}

static inline int64_t
fpr_floor(fpr x)
{
	uint64_t t;
	int64_t xi;
	int e, cc;

	/*
	 * We extract the integer as a _signed_ 64-bit integer with
	 * a scaling factor. Since we assume that the value fits
	 * in the -(2^63-1)..+(2^63-1) range, we can left-shift the
	 * absolute value to make it in the 2^62..2^63-1 range: we
	 * will only need a right-shift afterwards.
	 */
	e = (int)(x >> 52) & 0x7FF;
	t = x >> 63;
	xi = (int64_t)(((x << 10) | ((uint64_t)1 << 62))
		& (((uint64_t)1 << 63) - 1));
	xi = (xi ^ -(int64_t)t) + (int64_t)t;
	cc = 1085 - e;

	/*
	 * We perform an arithmetic right-shift on the value. This
	 * applies floor() semantics on both positive and negative values
	 * (rounding toward minus infinity).
	 */
	xi = fpr_irsh(xi, cc & 63);

	/*
	 * If the true shift count was 64 or more, then we should instead
	 * replace xi with 0 (if nonnegative) or -1 (if negative). Edge
	 * case: -0 will be floored to -1, not 0 (whether this is correct
	 * is debatable; in any case, the other functions normalize zero
	 * to +0).
	 *
	 * For an input of zero, the non-shifted xi was incorrect (we used
	 * a top implicit bit of value 1, not 0), but this does not matter
	 * since this operation will clamp it down.
	 */
	xi ^= (xi ^ -(int64_t)t) & -(int64_t)((uint32_t)(63 - cc) >> 31);
	return xi;
}

static inline int64_t
fpr_trunc(fpr x)
{
	uint64_t t, xu;
	int e, cc;

	/*
	 * Extract the absolute value. Since we assume that the value
	 * fits in the -(2^63-1)..+(2^63-1) range, we can left-shift
	 * the absolute value into the 2^62..2^63-1 range, and then
	 * do a right shift afterwards.
	 */
	e = (int)(x >> 52) & 0x7FF;
	xu = ((x << 10) | ((uint64_t)1 << 62)) & (((uint64_t)1 << 63) - 1);
	cc = 1085 - e;
	xu = fpr_ursh(xu, cc & 63);

	/*
	 * If the exponent is too low (cc > 63), then the shift was wrong
	 * and we must clamp the value to 0. This also covers the case
	 * of an input equal to zero.
	 */
	xu &= -(uint64_t)((uint32_t)(cc - 64) >> 31);

	/*
	 * Apply back the sign, if the source value is negative.
	 */
	t = x >> 63;
	xu = (xu ^ -t) + t;
	return *(int64_t *)&xu;
}

uint64_t
fpr_expm_p63(fpr x, fpr ccs)
{
	/*
	 * Polynomial approximation of exp(-x) is taken from FACCT:
	 *   https://eprint.iacr.org/2018/1234
	 * Specifically, values are extracted from the implementation
	 * referenced from the FACCT article, and available at:
	 *   https://github.com/raykzhao/gaussian
	 * Here, the coefficients have been scaled up by 2^63 and
	 * converted to integers.
	 *
	 * Tests over more than 24 billions of random inputs in the
	 * 0..log(2) range have never shown a deviation larger than
	 * 2^(-50) from the true mathematical value.
	 */
	static const uint64_t C[] = {
		0x00000004741183A3u,
		0x00000036548CFC06u,
		0x0000024FDCBF140Au,
		0x0000171D939DE045u,
		0x0000D00CF58F6F84u,
		0x000680681CF796E3u,
		0x002D82D8305B0FEAu,
		0x011111110E066FD0u,
		0x0555555555070F00u,
		0x155555555581FF00u,
		0x400000000002B400u,
		0x7FFFFFFFFFFF4800u,
		0x8000000000000000u
	};

	uint64_t z, y;
	unsigned u;
	uint32_t z0, z1, y0, y1;
	uint64_t a, b;

	y = C[0];
	z = (uint64_t)fpr_trunc(fpr_mul(x, fpr_ptwo63)) << 1;
	for (u = 1; u < (sizeof C) / sizeof(C[0]); u ++) {
		/*
		 * Compute product z * y over 128 bits, but keep only
		 * the top 64 bits.
		 *
		 * TODO: On some architectures/compilers we could use
		 * some intrinsics (__umulh() on MSVC) or other compiler
		 * extensions (unsigned __int128 on GCC / Clang) for
		 * improved speed; however, most 64-bit architectures
		 * also have appropriate IEEE754 floating-point support,
		 * which is better.
		 */
		uint64_t c;

		z0 = (uint32_t)z;
		z1 = (uint32_t)(z >> 32);
		y0 = (uint32_t)y;
		y1 = (uint32_t)(y >> 32);
		a = ((uint64_t)z0 * (uint64_t)y1)
			+ (((uint64_t)z0 * (uint64_t)y0) >> 32);
		b = ((uint64_t)z1 * (uint64_t)y0);
		c = (a >> 32) + (b >> 32);
		c += (((uint64_t)(uint32_t)a + (uint64_t)(uint32_t)b) >> 32);
		c += (uint64_t)z1 * (uint64_t)y1;
		y = C[u] - c;
	}

	/*
	 * The scaling factor must be applied at the end. Since y is now
	 * in fixed-point notation, we have to convert the factor to the
	 * same format, and do an extra integer multiplication.
	 */
	z = (uint64_t)fpr_trunc(fpr_mul(ccs, fpr_ptwo63)) << 1;
	z0 = (uint32_t)z;
	z1 = (uint32_t)(z >> 32);
	y0 = (uint32_t)y;
	y1 = (uint32_t)(y >> 32);
	a = ((uint64_t)z0 * (uint64_t)y1)
		+ (((uint64_t)z0 * (uint64_t)y0) >> 32);
	b = ((uint64_t)z1 * (uint64_t)y0);
	y = (a >> 32) + (b >> 32);
	y += (((uint64_t)(uint32_t)a + (uint64_t)(uint32_t)b) >> 32);
	y += (uint64_t)z1 * (uint64_t)y1;

	return y;
}

/* ====================================================================== */
/*
 * RNG (rng.c), trimmed to the ChaCha20-based PRNG this kernel uses: the
 * struct, the buffer refill, and the two byte/word accessors. The
 * SHAKE256-seeded prng_init()/get_seed() entry points are not part of
 * this extraction (state is caller-owned and pre-seeded; see
 * kernel_description.md), so they are not included here.
 */
typedef struct {
	union {
		uint8_t d[512]; /* MUST be 512, exactly */
		uint64_t dummy_u64;
	} buf;
	size_t ptr;
	union {
		uint8_t d[256];
		uint64_t dummy_u64;
	} state;
	int type;
} prng;

void falcon_inner_prng_refill(prng *p);

/*
 * Get a 64-bit random value from a PRNG.
 */
static inline uint64_t
prng_get_u64(prng *p)
{
	size_t u;

	/*
	 * If there are less than 9 bytes in the buffer, we refill it.
	 * This means that we may drop the last few bytes, but this allows
	 * for faster extraction code. Also, it means that we never leave
	 * an empty buffer.
	 */
	u = p->ptr;
	if (u >= (sizeof p->buf.d) - 9) {
		falcon_inner_prng_refill(p);
		u = 0;
	}
	p->ptr = u + 8;

	/*
	 * On systems that use little-endian encoding and allow
	 * unaligned accesses, we can simply read the data where it is.
	 */
	return (uint64_t)p->buf.d[u + 0]
		| ((uint64_t)p->buf.d[u + 1] << 8)
		| ((uint64_t)p->buf.d[u + 2] << 16)
		| ((uint64_t)p->buf.d[u + 3] << 24)
		| ((uint64_t)p->buf.d[u + 4] << 32)
		| ((uint64_t)p->buf.d[u + 5] << 40)
		| ((uint64_t)p->buf.d[u + 6] << 48)
		| ((uint64_t)p->buf.d[u + 7] << 56);
}

/*
 * Get an 8-bit random value from a PRNG.
 */
static inline unsigned
prng_get_u8(prng *p)
{
	unsigned v;

	v = p->buf.d[p->ptr ++];
	if (p->ptr == sizeof p->buf.d) {
		falcon_inner_prng_refill(p);
	}
	return v;
}

/* ====================================================================== */
/*
 * Internal sampler engine (sign.c), trimmed to the entry points this
 * kernel exposes.
 *
 * sampler_context wraps around a source of random numbers (PRNG) and
 * the sigma_min value (nominally dependent on the degree).
 *
 * sampler() takes as parameters:
 *   ctx      pointer to the sampler_context structure
 *   mu       center for the distribution
 *   isigma   inverse of the distribution standard deviation
 * It returns an integer sampled along the Gaussian distribution centered
 * on mu and of standard deviation sigma = 1/isigma.
 *
 * gaussian0_sampler() takes as parameter a pointer to a PRNG, and
 * returns an integer sampled along a half-Gaussian with standard
 * deviation sigma0 = 1.8205 (center is 0, returned value is
 * nonnegative).
 */
typedef struct {
	prng p;
	fpr sigma_min;
} sampler_context;

/* ====================================================================== */

void
falcon_inner_prng_refill(prng *p)
{

	static const uint32_t CW[] = {
		0x61707865, 0x3320646e, 0x79622d32, 0x6b206574
	};

	uint64_t cc;
	size_t u;

	/*
	 * State uses local endianness. Only the output bytes must be
	 * converted to little endian (if used on a big-endian machine).
	 */
	cc = *(uint64_t *)(p->state.d + 48);
	for (u = 0; u < 8; u ++) {
		uint32_t state[16];
		size_t v;
		int i;

		memcpy(&state[0], CW, sizeof CW);
		memcpy(&state[4], p->state.d, 48);
		state[14] ^= (uint32_t)cc;
		state[15] ^= (uint32_t)(cc >> 32);
		for (i = 0; i < 10; i ++) {

#define QROUND(a, b, c, d)   do { \
		state[a] += state[b]; \
		state[d] ^= state[a]; \
		state[d] = (state[d] << 16) | (state[d] >> 16); \
		state[c] += state[d]; \
		state[b] ^= state[c]; \
		state[b] = (state[b] << 12) | (state[b] >> 20); \
		state[a] += state[b]; \
		state[d] ^= state[a]; \
		state[d] = (state[d] <<  8) | (state[d] >> 24); \
		state[c] += state[d]; \
		state[b] ^= state[c]; \
		state[b] = (state[b] <<  7) | (state[b] >> 25); \
	} while (0)

			QROUND( 0,  4,  8, 12);
			QROUND( 1,  5,  9, 13);
			QROUND( 2,  6, 10, 14);
			QROUND( 3,  7, 11, 15);
			QROUND( 0,  5, 10, 15);
			QROUND( 1,  6, 11, 12);
			QROUND( 2,  7,  8, 13);
			QROUND( 3,  4,  9, 14);

#undef QROUND

		}

		for (v = 0; v < 4; v ++) {
			state[v] += CW[v];
		}
		for (v = 4; v < 14; v ++) {
			state[v] += ((uint32_t *)p->state.d)[v - 4];
		}
		state[14] += ((uint32_t *)p->state.d)[10]
			^ (uint32_t)cc;
		state[15] += ((uint32_t *)p->state.d)[11]
			^ (uint32_t)(cc >> 32);
		cc ++;

		/*
		 * We mimic the interleaving that is used in the AVX2
		 * implementation.
		 */
		for (v = 0; v < 16; v ++) {
			p->buf.d[(u << 2) + (v << 5) + 0] =
				(uint8_t)state[v];
			p->buf.d[(u << 2) + (v << 5) + 1] =
				(uint8_t)(state[v] >> 8);
			p->buf.d[(u << 2) + (v << 5) + 2] =
				(uint8_t)(state[v] >> 16);
			p->buf.d[(u << 2) + (v << 5) + 3] =
				(uint8_t)(state[v] >> 24);
		}
	}
	*(uint64_t *)(p->state.d + 48) = cc;


	p->ptr = 0;
}
int
falcon_inner_gaussian0_sampler(prng *p)
{

	static const uint32_t dist[] = {
		10745844u,  3068844u,  3741698u,
		 5559083u,  1580863u,  8248194u,
		 2260429u, 13669192u,  2736639u,
		  708981u,  4421575u, 10046180u,
		  169348u,  7122675u,  4136815u,
		   30538u, 13063405u,  7650655u,
		    4132u, 14505003u,  7826148u,
		     417u, 16768101u, 11363290u,
		      31u,  8444042u,  8086568u,
		       1u, 12844466u,   265321u,
		       0u,  1232676u, 13644283u,
		       0u,    38047u,  9111839u,
		       0u,      870u,  6138264u,
		       0u,       14u, 12545723u,
		       0u,        0u,  3104126u,
		       0u,        0u,    28824u,
		       0u,        0u,      198u,
		       0u,        0u,        1u
	};

	uint32_t v0, v1, v2, hi;
	uint64_t lo;
	size_t u;
	int z;

	/*
	 * Get a random 72-bit value, into three 24-bit limbs v0..v2.
	 */
	lo = prng_get_u64(p);
	hi = prng_get_u8(p);
	v0 = (uint32_t)lo & 0xFFFFFF;
	v1 = (uint32_t)(lo >> 24) & 0xFFFFFF;
	v2 = (uint32_t)(lo >> 48) | (hi << 16);

	/*
	 * Sampled value is z, such that v0..v2 is lower than the first
	 * z elements of the table.
	 */
	z = 0;
	for (u = 0; u < (sizeof dist) / sizeof(dist[0]); u += 3) {
		uint32_t w0, w1, w2, cc;

		w0 = dist[u + 2];
		w1 = dist[u + 1];
		w2 = dist[u + 0];
		cc = (v0 - w0) >> 31;
		cc = (v1 - w1 - cc) >> 31;
		cc = (v2 - w2 - cc) >> 31;
		z += (int)cc;
	}
	return z;

}
static int
BerExp(prng *p, fpr x, fpr ccs)
{
	int s, i;
	fpr r;
	uint32_t sw, w;
	uint64_t z;

	/*
	 * Reduce x modulo log(2): x = s*log(2) + r, with s an integer,
	 * and 0 <= r < log(2). Since x >= 0, we can use fpr_trunc().
	 */
	s = (int)fpr_trunc(fpr_mul(x, fpr_inv_log2));
	r = fpr_sub(x, fpr_mul(fpr_of(s), fpr_log2));

	/*
	 * It may happen (quite rarely) that s >= 64; if sigma = 1.2
	 * (the minimum value for sigma), r = 0 and b = 1, then we get
	 * s >= 64 if the half-Gaussian produced a z >= 13, which happens
	 * with probability about 0.000000000230383991, which is
	 * approximatively equal to 2^(-32). In any case, if s >= 64,
	 * then BerExp will be non-zero with probability less than
	 * 2^(-64), so we can simply saturate s at 63.
	 */
	sw = (uint32_t)s;
	sw ^= (sw ^ 63) & -((63 - sw) >> 31);
	s = (int)sw;

	/*
	 * Compute exp(-r); we know that 0 <= r < log(2) at this point, so
	 * we can use fpr_expm_p63(), which yields a result scaled to 2^63.
	 * We scale it up to 2^64, then right-shift it by s bits because
	 * we really want exp(-x) = 2^(-s)*exp(-r).
	 *
	 * The "-1" operation makes sure that the value fits on 64 bits
	 * (i.e. if r = 0, we may get 2^64, and we prefer 2^64-1 in that
	 * case). The bias is negligible since fpr_expm_p63() only computes
	 * with 51 bits of precision or so.
	 */
	z = ((fpr_expm_p63(r, ccs) << 1) - 1) >> s;

	/*
	 * Sample a bit with probability exp(-x). Since x = s*log(2) + r,
	 * exp(-x) = 2^-s * exp(-r), we compare lazily exp(-x) with the
	 * PRNG output to limit its consumption, the sign of the difference
	 * yields the expected result.
	 */
	i = 64;
	do {
		i -= 8;
		w = prng_get_u8(p) - ((uint32_t)(z >> i) & 0xFF);
	} while (!w && i > 0);
	return (int)(w >> 31);
}
int
falcon_inner_sampler(void *ctx, fpr mu, fpr isigma)
{
	sampler_context *spc;
	int s;
	fpr r, dss, ccs;

	spc = (sampler_context *)ctx;

	/*
	 * Center is mu. We compute mu = s + r where s is an integer
	 * and 0 <= r < 1.
	 */
	s = (int)fpr_floor(mu);
	r = fpr_sub(mu, fpr_of(s));

	/*
	 * dss = 1/(2*sigma^2) = 0.5*(isigma^2).
	 */
	dss = fpr_half(fpr_sqr(isigma));

	/*
	 * ccs = sigma_min / sigma = sigma_min * isigma.
	 */
	ccs = fpr_mul(isigma, spc->sigma_min);

	/*
	 * We now need to sample on center r.
	 */
	for (;;) {
		int z0, z, b;
		fpr x;

		/*
		 * Sample z for a Gaussian distribution. Then get a
		 * random bit b to turn the sampling into a bimodal
		 * distribution: if b = 1, we use z+1, otherwise we
		 * use -z. We thus have two situations:
		 *
		 *  - b = 1: z >= 1 and sampled against a Gaussian
		 *    centered on 1.
		 *  - b = 0: z <= 0 and sampled against a Gaussian
		 *    centered on 0.
		 */
		z0 = falcon_inner_gaussian0_sampler(&spc->p);
		b = (int)prng_get_u8(&spc->p) & 1;
		z = b + ((b << 1) - 1) * z0;

		/*
		 * Rejection sampling. We want a Gaussian centered on r;
		 * but we sampled against a Gaussian centered on b (0 or
		 * 1). But we know that z is always in the range where
		 * our sampling distribution is greater than the Gaussian
		 * distribution, so rejection works.
		 *
		 * We got z with distribution:
		 *    G(z) = exp(-((z-b)^2)/(2*sigma0^2))
		 * We target distribution:
		 *    S(z) = exp(-((z-r)^2)/(2*sigma^2))
		 * Rejection sampling works by keeping the value z with
		 * probability S(z)/G(z), and starting again otherwise.
		 * This requires S(z) <= G(z), which is the case here.
		 * Thus, we simply need to keep our z with probability:
		 *    P = exp(-x)
		 * where:
		 *    x = ((z-r)^2)/(2*sigma^2) - ((z-b)^2)/(2*sigma0^2)
		 *
		 * Here, we scale up the Bernouilli distribution, which
		 * makes rejection more probable, but makes rejection
		 * rate sufficiently decorrelated from the Gaussian
		 * center and standard deviation that the whole sampler
		 * can be said to be constant-time.
		 */
		x = fpr_mul(fpr_sqr(fpr_sub(fpr_of(z), r)), dss);
		x = fpr_sub(x, fpr_mul(fpr_of(z0 * z0), fpr_inv_2sqrsigma0));
		if (BerExp(&spc->p, x, ccs)) {
			/*
			 * Rejection sampling was centered on r, but the
			 * actual center is mu = s + r.
			 */
			return s + z;
		}
	}
}

/*
 * Under FALCON_FPEMU, 'fpr' is a raw uint64_t holding the same bit
 * pattern as an IEEE-754 binary64 'double' (see the fpr note above);
 * converting between the two is a bit-reinterpretation, not a numeric
 * cast.
 */
static fpr double_to_fpr(double d) {
    fpr u;
    memcpy(&u, &d, sizeof u);
    return u;
}

/* State is explicit, persistent, and caller-owned. Seed outside the kernel.
 * Precondition: *ptr < 512; mu in [-1024,1024]; 1 < sigma=1/isigma < 2;
 * 0 < sigma_min <= sigma. No rejection-loop cap is imposed. */
int falcon_sampler(double mu, double isigma, double sigma_min,
                   uint8_t buf[512], uint64_t ptr[1], uint8_t state[256]) {
    sampler_context ctx = {0};
    for (unsigned i=0;i<512;++i) ctx.p.buf.d[i]=buf[i];
    for (unsigned i=0;i<256;++i) ctx.p.state.d[i]=state[i];
    ctx.p.ptr=(size_t)ptr[0]; ctx.sigma_min=double_to_fpr(sigma_min);
    fpr m=double_to_fpr(mu), inv=double_to_fpr(isigma);
    int result=falcon_inner_sampler(&ctx,m,inv);
    for (unsigned i=0;i<512;++i) buf[i]=ctx.p.buf.d[i];
    for (unsigned i=0;i<256;++i) state[i]=ctx.p.state.d[i];
    ptr[0]=(uint64_t)ctx.p.ptr;
    return result;
}
