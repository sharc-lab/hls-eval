## skein

Computes one block step of the Skein-512-256 cryptographic hash function (a SHA-3 finalist,
built on the Threefish-512 tweakable block cipher inside Skein's UBI chaining mode), letting
the caller stream a message through one 64-byte block at a time by keeping the chaining
key/state internally between calls.

Top-Level Function: `skein`

Inputs:

- `data`: the current message block, 8 64-bit words (64 bytes).
- `firstBlock`: 1 if this is the first block of a new message (initialize the key schedule
  from the standard Skein-512-256 IV/key instead of the carried-over key state).
- `lastBlock`: 1 if this is the final block of the message.
- `size`: the number of message bytes contained in this block, used to advance the internal
  running byte-position counter (the UBI tweak).

Outputs:

- `output`: the 256-bit digest, 4 64-bit words. Only meaningful when `lastBlock` is 1.

Behavior: encrypts the running chaining value with Threefish-512, keyed by the current key
schedule and a tweak value derived from the running byte counter together with the
`firstBlock`/`lastBlock` flags (per the Skein Unique Block Iteration construction), then
combines the ciphertext with the input block (Matyas-Meyer-Oseas style: ciphertext XOR block)
to form the new chaining/key state retained for the next call. On the final block, the
standard Skein output-transform finalization is additionally applied and the digest is read
from the resulting state.

An implementation must match the official Skein specification's Threefish round function, key
schedule, and tweak/UBI construction to reproduce correct digests.
