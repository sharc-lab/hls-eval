#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "covariance.h"
#include "hls_eval_check.h"


t_ap_fixed data[ 100 + 0][80 + 0];
t_ap_fixed cov[ 80 + 0][80 + 0];
t_ap_fixed mean[ 80 + 0];


void init_array (int m, int n,
		 t_ap_fixed *float_n,
		 t_ap_fixed data[ 100 + 0][80 + 0])
{
  int i, j;

  *float_n = (t_ap_fixed)n;

  for (i = 0; i < 100; i++)
    for (j = 0; j < 80; j++)
      data[i][j] = (t_ap_fixed)(5.0 + 3.0 * sin(0.3 * i + 0.7 * j) +
                                 0.5 * cos(0.5 * i - 0.2 * j));
}


void print_array(int m,
		 t_ap_fixed cov[ 80 + 0][80 + 0])

{
  int i, j;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "cov");
  for (i = 0; i < m; i++)
    for (j = 0; j < m; j++) {
      if ((i * m + j) % 20 == 0) fprintf (stderr, "\n");
      fprintf (stderr, "%0.6lf ", (float)cov[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "cov");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int m, t_ap_fixed cov[ 80 + 0][80 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j;
  auto it = golden.find("cov");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "cov");
  for (i = 0; i < m; i++)
    for (j = 0; j < m; j++)
      checker.add((float)cov[i][j]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 100;
  int m = 80;


  t_ap_fixed float_n;
  
  
  init_array (m, n, &float_n, data);


  kernel_covariance ( float_n,
		     data,
		     cov,
		     mean);


  print_array(m, cov);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(m, cov, golden);

  return ok ? 0 : 1;
}