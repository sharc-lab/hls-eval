## BLAKE32

Computes one block-compression step of the BLAKE-256 cryptographic hash function (a SHA-3
finalist), letting the caller stream a message through one 512-bit block at a time by keeping
the running hash chain value internally between calls.

Top-Level Function: `BLAKE32`

Inputs:

- `data`, `data_reg`: two identical copies of the current 512-bit message block, given as 16
  32-bit words each (the duplicate exists only so the block can be read from two ports).
- `last`: 1 if this is the final block of the message, 0 otherwise.
- `size`: the number of bits hashed so far including this block; passing 0 resets the
  internal running bit counter, which starts a new message.

Outputs:

- `output`: the 256-bit digest (8 32-bit words). Only meaningful when `last` is 1.

Behavior: internally maintains an 8-word chaining hash value (initialized to the standard
BLAKE-256 IV) and a running bit counter. Each call runs the standard BLAKE-256 compression
function — 14 rounds, each a column step followed by a diagonal step of the BLAKE `G` mixing
function, using the standard round constants and the standard per-round message-word
permutation schedule — over the current chaining value, the message block, and the bit
counter, producing a new chaining value. If `last` is 1, that value is written to `output` as
the digest and the internal chaining value/counter are reset to their initial state for the
next message; otherwise the new chaining value is retained as the input for the next block.

An implementation must match the official BLAKE (BLAKE-256) specification's round function,
constants, and message schedule to reproduce correct digests.
