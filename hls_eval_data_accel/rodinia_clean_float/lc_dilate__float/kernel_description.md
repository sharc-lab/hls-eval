## lc_dilate

Grayscale morphological dilation of a `GRID_ROWS`$\times$`GRID_COLS` image with a fixed 5x5
structuring element, as used in the Rodinia leukocyte-tracking benchmark's image
preprocessing stage.

It takes the following as input,

- `img`: the image, supplied as a $(\text{GRID\_ROWS}+2\cdot\text{MAX\_RADIUS})\times\text{GRID\_COLS}$
  buffer with the real `GRID_ROWS`$\times$`GRID_COLS` image occupying the middle rows (offset
  by `MAX_RADIUS` $=2$ rows from the top of the buffer).

and gives the following as output:

- `result`: `GRID_ROWS`$\times$`GRID_COLS` array, the dilated image.

For every output pixel $(i,j)$:

$$
result(i,j) = \max_{(m,n)\,:\, strel(m,n) \neq 0} \; img\big(i - 2 + m,\; j - 2 + n\big)
$$

where $strel$ is the fixed 5x5 structuring element (rows/cols 0-4, 1 = included in the max):

```
0 0 1 0 0
0 1 1 1 0
1 1 1 1 1
0 1 1 1 0
0 0 1 0 0
```

and any $(m,n)$ whose corresponding image coordinate falls outside the real
`GRID_ROWS`$\times$`GRID_COLS` image is excluded from the max entirely (not treated as zero).
