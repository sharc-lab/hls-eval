## groestl

Computes one block-compression step of the Grøstl-256 cryptographic hash function (a SHA-3
finalist), letting the caller stream a message through one 64-byte block at a time by keeping
a 512-bit chaining state internally between calls.

Top-Level Function: `groestl`

Inputs:

- `data`: the current 64-byte message block.
- `last`: 1 if this is the final block of the message, 0 otherwise.

Outputs:

- `output`: the 256-bit digest (32 bytes). Only meaningful when `last` is 1.

Behavior: internally maintains a 64-byte hash state (initialized to the standard Grøstl-256
IV). Each call XORs the message block into the state and runs the standard Grøstl compression
function — the `P` and `Q` AES-derived permutations, each 10 rounds combining an
AddRoundConstant step, an AES S-box byte substitution, a cyclic byte-shift (ShiftBytes), and a
MixBytes diffusion step over the $8\times8$ byte state — to produce the next chaining state.
On the final block (`last` = 1), the standard Grøstl output transformation
($P(\text{state}) \oplus \text{state}$) is additionally applied and its upper 32 bytes are
written to `output`; the internal state is reset for the next message.

An implementation must match the official Grøstl specification's round constants, S-box, and
diffusion matrix to reproduce correct digests.
