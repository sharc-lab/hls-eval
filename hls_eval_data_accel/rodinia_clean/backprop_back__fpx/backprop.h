#ifndef _BACKPROP_H_
#define _BACKPROP_H_

#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;

#define BIGRND 0x7fffffff


#define ETA 0.3       //eta value
#define MOMENTUM 0.3  //momentum value
#define NUM_THREAD 8 //OpenMP threads

typedef struct {
  int input_n;                  /* number of input units */
  int hidden_n;                 /* number of hidden units */
  int output_n;                 /* number of output units */

  fixed_t *input_units;          /* the input units */
  fixed_t *hidden_units;         /* the hidden units */
  fixed_t *output_units;         /* the output units */

  fixed_t *hidden_delta;         /* storage for hidden unit error */
  fixed_t *output_delta;         /* storage for output unit error */

  fixed_t *target;               /* storage for target vector */

  fixed_t **input_weights;       /* weights from input to hidden layer */
  fixed_t **hidden_weights;      /* weights from hidden to output layer */

                                /*** The next two are for momentum ***/
  fixed_t **input_prev_weights;  /* previous change on input to hidden wgt */
  fixed_t **hidden_prev_weights; /* previous change on hidden to output wgt */
} BPNN;

#endif
