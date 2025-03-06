typedef int flag;
typedef int int8;
typedef int int16;

typedef unsigned short int bits16;
typedef unsigned int bits32;
typedef unsigned long long int bits64;
typedef signed long long int sbits64;

typedef unsigned int float32;
typedef unsigned long long float64;

float64 roundAndPackFloat64(flag zSign, int16 zExp, bits64 zSig);