## backprop_back

Computes the momentum-based weight update ("delta rule with momentum") for one layer of a
back-propagation neural network, as used in the Rodinia `backprop` benchmark's backward pass.
Given the back-propagated error signal for each output unit and the activations of the
preceding layer, it updates every connection weight between the two layers and records the
per-weight update magnitude for use as the momentum term on the next call.

It takes the following as input,

- `delta`: vector of length 17. `delta[j]` is the error signal for output unit $j = 1, \ldots, 16$
  (index 0 is unused).
- `ly`: vector of length 65537, the activation of each of the 65536 input units, indexed
  $k = 1, \ldots, 65536$. Index 0 is a fixed bias unit and is always treated as having
  activation 1, regardless of the value passed in.
- `w`: $65537 \times 17$ matrix (row-major, `w[k*17+j]`) of the current weight from input
  unit $k$ (including the bias unit $k=0$) to output unit $j$.
- `oldw`: $65537 \times 17$ matrix, the weight update computed for each connection the
  previous time this update was applied (used for the momentum term).

and gives the following as outputs, both updated in place:

- `w`: every weight incremented by its new update, $w(k,j) \mathrel{+}= \Delta w(k,j)$.
- `oldw`: replaced with the new update, $oldw(k,j) = \Delta w(k,j)$, for use as the momentum
  term next time.

The update for every output unit $j = 1, \ldots, 16$ and every input unit $k = 0, \ldots, 65536$
(with $ly(0) \equiv 1$) is:

$$
\Delta w(k,j) = \eta \cdot delta(j) \cdot ly(k) \;+\; \mu \cdot oldw(k,j)
$$

where $\eta = 0.3$ (`ETA`) is the learning rate and $\mu = 0.3$ (`MOMENTUM`) is the momentum
coefficient.
