#include "streamcluster.h"

extern "C" {
void workload(
    fixed_t coord[BATCH_SIZE * DIM],
    fixed_t weight[BATCH_SIZE],
    fixed_t cost[BATCH_SIZE],
    fixed_t target[DIM],
    int assign[BATCH_SIZE],
    int center_table[BATCH_SIZE],
    char switch_membership[BATCH_SIZE],
    fixed_t work_mem[MAX_WORK_MEM_SIZE],
    int num,
    fixed_t cost_of_opening_x[1],
    int numcenter
)
{
    #pragma HLS INTERFACE m_axi port=coord offset=slave bundle=gmemf
    #pragma HLS INTERFACE m_axi port=weight offset=slave bundle=gmemf
    #pragma HLS INTERFACE m_axi port=cost offset=slave bundle=gmemf
    #pragma HLS INTERFACE m_axi port=target offset=slave bundle=gmemf
    #pragma HLS INTERFACE m_axi port=assign offset=slave bundle=gmemi
    #pragma HLS INTERFACE m_axi port=center_table offset=slave bundle=gmemi
    #pragma HLS INTERFACE m_axi port=switch_membership offset=slave bundle=gmemc
    #pragma HLS INTERFACE m_axi port=work_mem offset=slave bundle=gmemf
    #pragma HLS INTERFACE m_axi port=cost_of_opening_x offset=slave bundle=gmemf
    #pragma HLS INTERFACE s_axilite port=coord bundle=control
    #pragma HLS INTERFACE s_axilite port=weight bundle=control
    #pragma HLS INTERFACE s_axilite port=cost bundle=control
    #pragma HLS INTERFACE s_axilite port=target bundle=control
    #pragma HLS INTERFACE s_axilite port=assign bundle=control
    #pragma HLS INTERFACE s_axilite port=center_table bundle=control
    #pragma HLS INTERFACE s_axilite port=switch_membership bundle=control
    #pragma HLS INTERFACE s_axilite port=work_mem bundle=control
    #pragma HLS INTERFACE s_axilite port=num bundle=control
    #pragma HLS INTERFACE s_axilite port=cost_of_opening_x bundle=control
    #pragma HLS INTERFACE s_axilite port=numcenter bundle=control
    #pragma HLS INTERFACE s_axilite port=return bundle=control


    int i, j;
    for( i = 0; i < BATCH_SIZE; i++ ) {
        fixed_t sum = 0;
        for( j = 0; j < DIM; j++ ) {
            fixed_t a = coord[i * DIM + j] - target[j];
            sum += a * a;
        }
        fixed_t current_cost = sum * weight[i] - cost[i];
        int local_center_index = center_table[assign[i]];
        if (current_cost < 0) {

            // point i would save cost just by switching to x
            // (note that i cannot be a median, 
            // or else dist(p[i], p[x]) would be 0)
      
            switch_membership[i] = 1;
            cost_of_opening_x[0] += current_cost;

        } 
        else {

            // cost of assigning i to x is at least current assignment cost of i

            // consider the savings that i's **current** median would realize
            // if we reassigned that median and all its members to x;
            // note we've already accounted for the fact that the median
            // would save z by closing; now we have to subtract from the savings
            // the extra cost of reassigning that median and its members 
            work_mem[local_center_index] -= current_cost;
        }
    }
    
    return;
}
}
