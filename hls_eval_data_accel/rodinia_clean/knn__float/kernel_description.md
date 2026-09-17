## knn

Computes the squared Euclidean distance from a single query point to every point in a search
space, i.e. the distance-computation stage of a k-nearest-neighbor search, as in the Rodinia
`knn` benchmark. (No sorting or top-k selection is performed by this kernel.)

It takes the following as inputs,

- `inputQuery`: vector of length `NUM_FEATURE`, the query point's coordinates.
- `searchSpace`: `NUM_PT_IN_SEARCHSPACE`$\times$`NUM_FEATURE` array (row-major), the
  coordinates of every candidate point.

and gives the following as output:

- `distance`: vector of length `NUM_PT_IN_SEARCHSPACE`.

For every candidate point $i$:

$$
distance(i) = \sum_{k=0}^{NUM\_FEATURE-1} \big(searchSpace(i,k) - inputQuery(k)\big)^2
$$
