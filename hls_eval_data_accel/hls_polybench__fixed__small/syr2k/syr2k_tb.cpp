#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "syr2k.h"
#include "hls_eval_check.h"


t_ap_fixed C[ 80 + 0][80 + 0];
t_ap_fixed A[ 80 + 0][60 + 0];
t_ap_fixed B[ 80 + 0][60 + 0];


void init_array(int n, int m,
		t_ap_fixed *alpha,
		t_ap_fixed *beta,
		t_ap_fixed C[ 80 + 0][80 + 0],
		t_ap_fixed A[ 80 + 0][60 + 0],
		t_ap_fixed B[ 80 + 0][60 + 0])
{
  int i, j;

  *alpha = (t_ap_fixed(1.5));
  *beta = (t_ap_fixed(1.2));
  for (i = 0; i < n; i++)
    for (j = 0; j < m; j++) {
      A[i][j] = (t_ap_fixed) ((i*j+1)%n) / n;
      B[i][j] = (t_ap_fixed) ((i*j+2)%m) / m;
    }
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++) {
      C[i][j] = (t_ap_fixed) ((i*j+3)%n) / m;
    }
}


void print_array(int n,
		 t_ap_fixed C[ 80 + 0][80 + 0])
{
  int i, j;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "C");
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++) {
	if ((i * n + j) % 20 == 0) fprintf (stderr, "\n");
	fprintf (stderr, "%0.6lf ", (float)C[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "C");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n, t_ap_fixed C[ 80 + 0][80 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j;
  auto it = golden.find("C");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "C");
  for (i = 0; i < n; i++)
    for (j = 0; j < n; j++)
      checker.add((float)C[i][j]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 80;
  int m = 60;


  t_ap_fixed alpha;
  t_ap_fixed beta;
  
  
  init_array (n, m, &alpha, &beta,
	      C,
	      A,
	      B);


  kernel_syr2k (
		alpha, beta,
		C,
		A,
		B);


  print_array(n, C);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, C, golden);

  return ok ? 0 : 1;
}