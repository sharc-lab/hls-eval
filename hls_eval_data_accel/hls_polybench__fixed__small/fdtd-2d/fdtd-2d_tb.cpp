#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "fdtd-2d.h"
#include "hls_eval_check.h"


t_ap_fixed ex[ 60 + 0][80 + 0];
t_ap_fixed ey[ 60 + 0][80 + 0];
t_ap_fixed hz[ 60 + 0][80 + 0];
t_ap_fixed _fict_[ 40 + 0];


void init_array (int tmax,
		 int nx,
		 int ny,
		 t_ap_fixed ex[ 60 + 0][80 + 0],
		 t_ap_fixed ey[ 60 + 0][80 + 0],
		 t_ap_fixed hz[ 60 + 0][80 + 0],
		 t_ap_fixed _fict_[ 40 + 0])
{
  int i, j;

  for (i = 0; i < tmax; i++)
    _fict_[i] = (t_ap_fixed) i;
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++)
      {
	ex[i][j] = ((t_ap_fixed) i*(j+1)) / nx;
	ey[i][j] = ((t_ap_fixed) i*(j+2)) / ny;
	hz[i][j] = ((t_ap_fixed) i*(j+3)) / nx;
      }
}


void print_array(int nx,
		 int ny,
		 t_ap_fixed ex[ 60 + 0][80 + 0],
		 t_ap_fixed ey[ 60 + 0][80 + 0],
		 t_ap_fixed hz[ 60 + 0][80 + 0])
{
  int i, j;

  fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
  fprintf(stderr, "begin dump: %s", "ex");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++) {
      if ((i * nx + j) % 20 == 0) fprintf(stderr, "\n");
      fprintf(stderr, "%0.6lf ", (float)ex[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "ex");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");

  fprintf(stderr, "begin dump: %s", "ey");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++) {
      if ((i * nx + j) % 20 == 0) fprintf(stderr, "\n");
      fprintf(stderr, "%0.6lf ", (float)ey[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "ey");

  fprintf(stderr, "begin dump: %s", "hz");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++) {
      if ((i * nx + j) % 20 == 0) fprintf(stderr, "\n");
      fprintf(stderr, "%0.6lf ", (float)hz[i][j]);
    }
  fprintf(stderr, "\nend   dump: %s\n", "hz");
}


static bool check_output(int nx, int ny,
			  t_ap_fixed ex[ 60 + 0][80 + 0],
			  t_ap_fixed ey[ 60 + 0][80 + 0],
			  t_ap_fixed hz[ 60 + 0][80 + 0],
			  const std::map<std::string, std::vector<float>> &golden)
{
  int i, j;

  auto it_ex = golden.find("ex");
  hls_eval_check::ArrayChecker checker_ex(
      it_ex != golden.end() ? &it_ex->second : nullptr, "ex");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++)
      checker_ex.add((float)ex[i][j]);

  auto it_ey = golden.find("ey");
  hls_eval_check::ArrayChecker checker_ey(
      it_ey != golden.end() ? &it_ey->second : nullptr, "ey");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++)
      checker_ey.add((float)ey[i][j]);

  auto it_hz = golden.find("hz");
  hls_eval_check::ArrayChecker checker_hz(
      it_hz != golden.end() ? &it_hz->second : nullptr, "hz");
  for (i = 0; i < nx; i++)
    for (j = 0; j < ny; j++)
      checker_hz.add((float)hz[i][j]);

  bool ex_ok = checker_ex.passed();
  bool ey_ok = checker_ey.passed();
  bool hz_ok = checker_hz.passed();
  return ex_ok && ey_ok && hz_ok;
}


int main(int argc, char** argv)
{

  int tmax = 40;
  int nx = 60;
  int ny = 80;


  init_array (tmax, nx, ny,
	      ex,
	      ey,
	      hz,
	      _fict_);


  kernel_fdtd_2d (
		  ex,
		  ey,
		  hz,
		  _fict_);


  print_array(nx, ny, ex,
				    ey,
				    hz);

  auto golden = hls_eval_check::load_golden_dumps("tb_data.txt");
  bool ok = check_output(nx, ny, ex, ey, hz, golden);

  return ok ? 0 : 1;
}