#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "symm.h"
#include "hls_eval_check.h"


t_ap_fixed C[ 60 + 0][80 + 0];
t_ap_fixed A[ 60 + 0][60 + 0];
t_ap_fixed B[ 60 + 0][80 + 0];


void init_array(int m, int n,
		t_ap_fixed *alpha,
		t_ap_fixed *beta,
		t_ap_fixed C[ 60 + 0][80 + 0],
		t_ap_fixed A[ 60 + 0][60 + 0],
		t_ap_fixed B[ 60 + 0][80 + 0])
{
  int i, j;

  *alpha = (t_ap_fixed(1.5));
  *beta = (t_ap_fixed(1.2));
  for (i = 0; i < m; i++)
    for (j = 0; j < n; j++) {
      C[i][j] = (t_ap_fixed) ((i+j) % 100) / m;
      B[i][j] = (t_ap_fixed) ((n+i-j) % 100) / m;
    }
  for (i = 0; i < m; i++) {
    for (j = 0; j <=i; j++)
      A[i][j] = (t_ap_fixed) ((i+j) % 100) / m;
    for (j = i+1; j < m; j++)
      A[i][j] = -999;
  }
}


void print_array(int m, int n,
		 t_ap_fixed C[ 60 + 0][80 + 0])
{
  int i, j;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "C");
  for (i = 0; i < m; i++)
    for (j = 0; j < n; j++) {
	if ((i * m + j) % 20 == 0) fprintf (stderr, "\n");
	fprintf (stderr, "%0.6lf ", (float)C[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "C");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int m, int n, t_ap_fixed C[ 60 + 0][80 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j;
  auto it = golden.find("C");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "C");
  for (i = 0; i < m; i++)
    for (j = 0; j < n; j++)
      checker.add((float)C[i][j]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int m = 60;
  int n = 80;


  t_ap_fixed alpha;
  t_ap_fixed beta;
  
  
  init_array (m, n, &alpha, &beta,
	      C,
	      A,
	      B);


  kernel_symm (
	       alpha, beta,
	       C,
	       A,
	       B);


  print_array(m, n, C);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(m, n, C, golden);

  return ok ? 0 : 1;
}