## jh

Computes one block-compression step of the JH-256 cryptographic hash function (a SHA-3
finalist), letting the caller stream a message through one 64-byte block at a time by keeping
a 1024-bit chaining state internally between calls.

Top-Level Function: `jh`

Inputs:

- `data`: the current 64-byte message block.
- `firstBlock`: 1 if this is the first block of a new message (initialize from the standard
  JH-256 IV instead of the carried-over chaining state).
- `lastBlock`: 1 if this is the final block of the message.

Outputs:

- `output`: the 256-bit digest (32 bytes). Only meaningful when `lastBlock` is 1.

Behavior: XORs the message block into the first half of the current 1024-bit state (the
standard IV on `firstBlock`, otherwise the state carried over from the previous call), runs
the standard 42-round JH bijective permutation `E8` on the resulting 1024-bit state, then XORs
the message block again into the second half of the permuted state to obtain the new chaining
state, which is retained for the next call. On the final block, the digest is the last 32
bytes of this new state.

An implementation must match the official JH specification's round function, round constants,
and bit-permutation (grouping/degrouping) to reproduce correct digests.
