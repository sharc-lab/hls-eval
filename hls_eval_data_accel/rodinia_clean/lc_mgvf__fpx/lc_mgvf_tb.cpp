// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), runs the ap_fixed workload(), and compares
// with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "lc_mgvf.h"
#include "support.h"

extern "C" void workload(fixed_t result[GRID_ROWS * GRID_COLS],
                          fixed_t imgvf[GRID_ROWS * GRID_COLS],
                          fixed_t I[GRID_ROWS * GRID_COLS]);

int main() {
  static fixed_t result[GRID_ROWS * GRID_COLS] = {};
  static fixed_t imgvf[GRID_ROWS * GRID_COLS];
  static fixed_t I[GRID_ROWS * GRID_COLS];
  static float imgvf_tmp[GRID_ROWS * GRID_COLS];
  static float I_tmp[GRID_ROWS * GRID_COLS];
  static float imgvf_ref[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), imgvf_tmp, GRID_ROWS * GRID_COLS);
  parse_float_array(find_section_start(p, 2), I_tmp, GRID_ROWS * GRID_COLS);
  free(p);
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) { imgvf[i] = imgvf_tmp[i]; I[i] = I_tmp[i]; }

  workload(result, imgvf, I);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), imgvf_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  fpx_check::ArrayChecker checker("imgvf");
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++)
    checker.add((double)(float)imgvf[i], (double)imgvf_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
