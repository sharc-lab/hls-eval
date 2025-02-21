Description:
The SHA256 update kernel is a high-level synthesis design that implements the SHA-256 hash function. The kernel is responsible for updating the hash state and processing the input data in blocks of 32 bytes. The design uses a combination of bitwise operations, rotations, and table lookups to compute the hash values.

Top-Level Function: `sha256_update`
Complete Function Signature: `void sha256_update(data_t *data_int, unsigned int *datalen_int, state_t *state, unsigned long long int *bitlen_int, data_t data[], size_t len);`

Inputs:
- `data_int`: a pointer to a 64-byte array representing the input data
- `datalen_int`: a pointer to an unsigned integer representing the length of the input data in bytes
- `state`: a pointer to an 8-element array of unsigned integers representing the current hash state
- `bitlen_int`: a pointer to an unsigned long long integer representing the total number of bits processed
- `data`: a 64-byte array representing the input data
- `len`: a size_t value representing the length of the input data in bytes

Outputs:
- None

Important Data Structures and Data Types:
- `data_t`: a 64-byte array representing the input data
- `state_t`: an 8-element array of unsigned integers representing the current hash state
- `SHA256_CTX`: a struct containing the current hash state, input data, and bit length

Sub-Components:
- `sha256_transform`: a function that updates the hash state using the input data and current hash state
- `sha256_init`: a function that initializes the hash state
- `sha256_final`: a function that finalizes the hash computation and generates the output hash value