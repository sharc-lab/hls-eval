#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "heat-3d.h"
#include "hls_eval_check.h"


t_ap_fixed A[ 20 + 0][20 + 0][20 + 0];
t_ap_fixed B[ 20 + 0][20 + 0][20 + 0];


void init_array (int n,
		 t_ap_fixed A[ 20 + 0][20 + 0][20 + 0],
		 t_ap_fixed B[ 20 + 0][20 + 0][20 + 0])
{
  int i, j, k;

  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      for (k = 0; k < n; k++)
        A[i][j][k] = B[i][j][k] = (t_ap_fixed) (i + j + (n-k))* 10 / (n);
}


void print_array(int n,
		 t_ap_fixed A[ 20 + 0][20 + 0][20 + 0])

{
  int i, j, k;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "A");
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      for (k = 0; k < n; k++) {
         if ((i * n * n + j * n + k) % 20 == 0) fprintf(stderr, "\n");
         fprintf(stderr, "%0.6lf ", (float)A[i][j][k]);
      }
  fprintf(stderr, "\nend   dump: %s\n", "A");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n, t_ap_fixed A[ 20 + 0][20 + 0][20 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j, k;
  auto it = golden.find("A");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "A");
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      for (k = 0; k < n; k++)
	checker.add((float)A[i][j][k]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 20;
  int tsteps = 40;


  init_array (n, A, B);


  kernel_heat_3d ( A, B);


  print_array(n, A);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, A, golden);

  return ok ? 0 : 1;
}