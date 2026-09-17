## kmeans

Assigns each of a set of points to its nearest cluster center by squared Euclidean distance,
i.e. one "assignment" step of the k-means clustering algorithm, as in the Rodinia `kmeans`
benchmark.

It takes the following as inputs,

- `feature`: `NPOINTS`$\times$`NFEATURES` array (row-major), the coordinates of every point.
- `clusters`: `NCLUSTERS`$\times$`NFEATURES` array (row-major), the coordinates of every
  candidate cluster center.

and gives the following as output:

- `membership`: vector of length `NPOINTS`, the index of the nearest cluster center for each
  point.

For every point $i$:

$$
membership(i) = \operatorname*{arg\,min}_{j=0,\ldots,NCLUSTERS-1} \; \sum_{k=0}^{NFEATURES-1} \big(feature(i,k) - clusters(j,k)\big)^2
$$

Ties are broken toward the lowest-numbered cluster whose distance is strictly less than all
clusters considered before it (i.e. the first cluster to achieve the minimum wins).
