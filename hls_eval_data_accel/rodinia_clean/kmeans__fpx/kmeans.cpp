#include "kmeans.h"

extern "C"{
void workload(fixed_t feature[NPOINTS * NFEATURES],
			fixed_t clusters[NCLUSTERS * NFEATURES],
			int membership[NPOINTS])
{
#pragma HLS INTERFACE m_axi port=feature offset=slave bundle=gmem
#pragma HLS INTERFACE m_axi port=membership offset=slave bundle=gmem
#pragma HLS INTERFACE m_axi port=clusters offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=feature bundle=control
#pragma HLS INTERFACE s_axilite port=membership bundle=control
#pragma HLS INTERFACE s_axilite port=clusters bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

	UPDATE_MEMBER: for (int i = 0; i < NPOINTS; i++) {
		// FLT_MAX (3.4e38) overflows ap_fixed<32,16>'s ~32767 range; use the
		// largest representable sentinel instead so the min-search still works.
		fixed_t min_dist = fixed_t(30000.0);
		int index = 0;

		/* find the cluster center id with min distance to pt */
		MIN: for (int j = 0; j < NCLUSTERS; j++) {
			fixed_t dist = 0.0;

			DIST: for (int k = 0; k < NFEATURES; k++) {
				fixed_t diff = feature[NFEATURES * i + k] - clusters[NFEATURES * j + k];
				dist += diff * diff;
			}
			if (dist < min_dist) {
				min_dist = dist;
				index = j;
			}
		}
		/* assign the membership to object i */
		membership[i] = index;
	}
}
}