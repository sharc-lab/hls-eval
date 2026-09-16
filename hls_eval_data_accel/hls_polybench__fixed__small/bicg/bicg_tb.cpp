#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "bicg.h"
#include "hls_eval_check.h"


t_ap_fixed A[ 124 + 0][116 + 0];
t_ap_fixed s[ 116 + 0];
t_ap_fixed q[ 124 + 0];
t_ap_fixed p[ 116 + 0];
t_ap_fixed r[ 124 + 0];


void init_array (int m, int n,
		 t_ap_fixed A[ 124 + 0][116 + 0],
		 t_ap_fixed r[ 124 + 0],
		 t_ap_fixed p[ 116 + 0])
{
  int i, j;

  for (i = 0; i < m; i++)
    p[i] = (t_ap_fixed)(i % m) / m;
  for (i = 0; i < n; i++) {
    r[i] = (t_ap_fixed)(i % n) / n;
    for (j = 0; j < m; j++)
      A[i][j] = (t_ap_fixed) (i*(j+1) % n)/n;
  }
}


void print_array(int m, int n,
		 t_ap_fixed s[ 116 + 0],
		 t_ap_fixed q[ 124 + 0])

{
  int i;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "s");
  for (i = 0; i < m; i++) {
    if (i % 20 == 0) fprintf (stderr, "\n");
    fprintf (stderr, "%0.6lf ", (float)s[i]);
  }
  fprintf(stderr, "\nend   dump: %s\n", "s");
  fprintf(stderr, "begin dump: %s", "q");
  for (i = 0; i < n; i++) {
    if (i % 20 == 0) fprintf (stderr, "\n");
    fprintf (stderr, "%0.6lf ", (float)q[i]);
  }
  fprintf(stderr, "\nend   dump: %s\n", "q");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}


static bool check_output(int m, int n,
			  t_ap_fixed s[ 116 + 0],
			  t_ap_fixed q[ 124 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i;
  auto it_s = golden.find("s");
  hls_eval_check::ArrayChecker checker_s(
      it_s != golden.end() ? &it_s->second : nullptr, "s");
  for (i = 0; i < m; i++)
    checker_s.add((float)s[i]);

  auto it_q = golden.find("q");
  hls_eval_check::ArrayChecker checker_q(
      it_q != golden.end() ? &it_q->second : nullptr, "q");
  for (i = 0; i < n; i++)
    checker_q.add((float)q[i]);

  bool s_ok = checker_s.passed();
  bool q_ok = checker_q.passed();
  return s_ok && q_ok;
}


int main(int argc, char** argv)
{

  int n = 124;
  int m = 116;


  init_array (m, n,
	      A,
	      r,
	      p);


  kernel_bicg (
	       A,
	       s,
	       q,
	       p,
	       r);


  print_array(m, n, s, q);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(m, n, s, q, golden);

  return ok ? 0 : 1;
}