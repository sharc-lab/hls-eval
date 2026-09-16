#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "mvt.h"
#include "hls_eval_check.h"


t_ap_fixed A[ 120 + 0][120 + 0];
t_ap_fixed x1[ 120 + 0];
t_ap_fixed x2[ 120 + 0];
t_ap_fixed y_1[ 120 + 0];
t_ap_fixed y_2[ 120 + 0];


void init_array(int n,
		t_ap_fixed x1[ 120 + 0],
		t_ap_fixed x2[ 120 + 0],
		t_ap_fixed y_1[ 120 + 0],
		t_ap_fixed y_2[ 120 + 0],
		t_ap_fixed A[ 120 + 0][120 + 0])
{
  int i, j;

  for (i = 0; i < n; i++)
    {
      x1[i] = (t_ap_fixed) (i % n) / n;
      x2[i] = (t_ap_fixed) ((i + 1) % n) / n;
      y_1[i] = (t_ap_fixed) ((i + 3) % n) / n;
      y_2[i] = (t_ap_fixed) ((i + 4) % n) / n;
      for (j = 0; j < n; j++)
	A[i][j] = (t_ap_fixed) (i*j % n) / n;
    }
}


void print_array(int n,
		 t_ap_fixed x1[ 120 + 0],
		 t_ap_fixed x2[ 120 + 0])

{
  int i;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "x1");
  for (i = 0; i < n; i++) {
    if (i % 20 == 0) fprintf (stderr, "\n");
    fprintf (stderr, "%0.6lf ", (float)x1[i]);
  }
  fprintf(stderr, "\nend   dump: %s\n", "x1");

  fprintf(stderr, "begin dump: %s", "x2");
  for (i = 0; i < n; i++) {
    if (i % 20 == 0) fprintf (stderr, "\n");
    fprintf (stderr, "%0.6lf ", (float)x2[i]);
  }
  fprintf(stderr, "\nend   dump: %s\n", "x2");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n,
			  t_ap_fixed x1[ 120 + 0],
			  t_ap_fixed x2[ 120 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i;
  auto it_x1 = golden.find("x1");
  hls_eval_check::ArrayChecker checker_x1(
      it_x1 != golden.end() ? &it_x1->second : nullptr, "x1");
  for (i = 0; i < n; i++)
    checker_x1.add((float)x1[i]);

  auto it_x2 = golden.find("x2");
  hls_eval_check::ArrayChecker checker_x2(
      it_x2 != golden.end() ? &it_x2->second : nullptr, "x2");
  for (i = 0; i < n; i++)
    checker_x2.add((float)x2[i]);

  bool x1_ok = checker_x1.passed();
  bool x2_ok = checker_x2.passed();
  return x1_ok && x2_ok;
}


int main(int argc, char** argv)
{

  int n = 120;


  init_array (n,
	      x1,
	      x2,
	      y_1,
	      y_2,
	      A);


  kernel_mvt (
	      x1,
	      x2,
	      y_1,
	      y_2,
	      A);


  print_array(n, x1, x2);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, x1, x2, golden);

  return ok ? 0 : 1;
}