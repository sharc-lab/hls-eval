#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "durbin.h"


t_ap_fixed r[ 120 + 0];
t_ap_fixed y[ 120 + 0];


void init_array (int n,
		 t_ap_fixed r[ 120 + 0])
{
  int i, j;

  for (i = 0; i < n; i++)
    {
      r[i] = (n+1-i);
    }
}


void print_array(int n,
		 t_ap_fixed y[ 120 + 0])

{
  int i;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "y");
  for (i = 0; i < n; i++) {
    if (i % 20 == 0) fprintf (stderr, "\n");
    fprintf(stderr, "%s ", ap_uint<32>(y[i].range(31, 0)).to_string(16).c_str());
  }
  fprintf(stderr, "\nend   dump: %s\n", "y");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


int main(int argc, char** argv)
{

  int n = 120;


  init_array (n, r);


  kernel_durbin (
		 r,
		 y);


  print_array(n, y);


  return 0;
}