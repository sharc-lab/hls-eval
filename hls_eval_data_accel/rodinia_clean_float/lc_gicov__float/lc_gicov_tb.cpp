// Minimal software testbench: loads input.data (grad_x, grad_y), runs
// workload(), and compares against check.data (bit-exact, matching the
// original local_support.cpp's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "lc_gicov.h"
#include "support.h"

extern "C" void workload(float result[GRID_ROWS * GRID_COLS],
                          float grad_x[GRID_ROWS * GRID_COLS],
                          float grad_y[GRID_ROWS * GRID_COLS]);

int main() {
  static float result[GRID_ROWS * GRID_COLS] = {};
  static float grad_x[GRID_ROWS * GRID_COLS];
  static float grad_y[GRID_ROWS * GRID_COLS];
  static float result_ref[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), grad_x, GRID_ROWS * GRID_COLS);
  parse_float_array(find_section_start(p, 2), grad_y, GRID_ROWS * GRID_COLS);
  free(p);

  workload(result, grad_x, grad_y);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  bool pass = memcmp(result, result_ref, GRID_ROWS * GRID_COLS * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
