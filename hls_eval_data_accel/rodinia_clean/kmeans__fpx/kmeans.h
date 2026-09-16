#ifndef KMEANS_H
#define KMEANS_H

#include <iostream>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;

#define FLT_MAX 3.40282347e+38

#define NPOINTS (819200/2)
#define NFEATURES 34
#define NCLUSTERS 5
#define TILE_SIZE 4096

const int WIDTH_FACTOR = 16;

const int NUM_TILES = NPOINTS/TILE_SIZE;

// void workload(fixed_t feature[NPOINTS * NFEATURES], /* [npoints][nfeatures] */
// 			  fixed_t clusters[NCLUSTERS * NFEATURES], /* [n_clusters][n_features] */
// 			  int membership[NPOINTS]);

struct bench_args_t {
	fixed_t FEATURE[NPOINTS*NFEATURES];
	fixed_t CLUSTER[NCLUSTERS*NFEATURES];
	int MEMBERSHIP[NPOINTS];
};

#endif
