## keccak

Computes one absorb step of the Keccak sponge construction (the SHA-3/Keccak-256 hash family,
with rate 1088 bits and capacity 512 bits), letting the caller stream a message through one
1088-bit block at a time by keeping the 1600-bit permutation state internally between calls.

Top-Level Function: `keccak`

Inputs:

- `data`: the current message block, 17 64-bit words (1088 bits, the sponge's "rate").
- `last`: 1 if this is the final block of the message, 0 otherwise.

Outputs:

- `output`: the 256-bit digest, 4 64-bit words. Only meaningful when `last` is 1.

Behavior: internally maintains a 25-lane (1600-bit) permutation state, initialized to all
zero. Each call XORs the message block into the first 17 lanes of the state, then runs the
standard 24-round Keccak-$f[1600]$ permutation (the theta, rho, pi, chi, and iota steps, with
the standard round constants) to produce the new state, which is retained for the next call.
On the final block, the digest is read from the first 4 lanes of the state after the
permutation.

An implementation must match the official Keccak/SHA-3 specification's round function and
round constants to reproduce correct digests.
