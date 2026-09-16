#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "jacobi-1d.h"
#include "hls_eval_check.h"


t_ap_fixed A[ 120 + 0];
t_ap_fixed B[ 120 + 0];


void init_array (int n,
		 t_ap_fixed A[ 120 + 0],
		 t_ap_fixed B[ 120 + 0])
{
  int i;

  for (i = 0; i < n; i++)
      {
	A[i] = ((t_ap_fixed) i+ 2) / n;
	B[i] = ((t_ap_fixed) i+ 3) / n;
      }
}


void print_array(int n,
		 t_ap_fixed A[ 120 + 0])

{
  int i;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "A");
  for (i = 0; i < n; i++)
    {
      if (i % 20 == 0) fprintf(stderr, "\n");
      fprintf(stderr, "%0.6lf ", (float)A[i]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "A");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n, t_ap_fixed A[ 120 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i;
  auto it = golden.find("A");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "A");
  for (i = 0; i < n; i++)
    checker.add((float)A[i]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 120;
  int tsteps = 40;


  init_array (n, A, B);


  kernel_jacobi_1d( A, B);


  print_array(n, A);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, A, golden);

  return ok ? 0 : 1;
}