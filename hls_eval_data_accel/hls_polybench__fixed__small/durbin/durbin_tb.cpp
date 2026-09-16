#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "durbin.h"
#include "hls_eval_check.h"


t_ap_fixed r[ 120 + 0];
t_ap_fixed y[ 120 + 0];


void init_array (int n,
		 t_ap_fixed r[ 120 + 0])
{
  int i, j;

  for (i = 0; i < n; i++)
    {
      r[i] = (t_ap_fixed) pow(0.5, i + 1);
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
    fprintf (stderr, "%0.6lf ", (float)y[i]);
  }
  fprintf(stderr, "\nend   dump: %s\n", "y");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int n, t_ap_fixed y[ 120 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i;
  auto it = golden.find("y");
  hls_eval_check::ArrayChecker checker(
      it != golden.end() ? &it->second : nullptr, "y");
  for (i = 0; i < n; i++)
    checker.add((float)y[i]);
  return checker.passed();
}


int main(int argc, char** argv)
{

  int n = 120;


  init_array (n, r);


  kernel_durbin (
		 r,
		 y);


  print_array(n, y);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(n, y, golden);

  return ok ? 0 : 1;
}