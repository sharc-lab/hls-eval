// Minimal software testbench: loads input.data (temp, power sections),
// runs workload(), and compares the resulting temp against check.data
// with the original local_support.cpp's 0.5% relative-error tolerance.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "hotspot.h"
#include "support.h"

extern "C" void workload(float result[GRID_ROWS * GRID_COLS],
                          float temp[GRID_ROWS * GRID_COLS],
                          float power[GRID_ROWS * GRID_COLS]);

int main() {
  static float result[GRID_ROWS * GRID_COLS] = {};
  static float temp[GRID_ROWS * GRID_COLS];
  static float power[GRID_ROWS * GRID_COLS];
  static float temp_ref[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), temp, GRID_ROWS * GRID_COLS);
  parse_float_array(find_section_start(p, 2), power, GRID_ROWS * GRID_COLS);
  free(p);

  workload(result, temp, power);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), temp_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  int errors = 0;
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) {
    if (temp[i] != temp_ref[i]) {
      float diff = fabsf(temp[i] - temp_ref[i]);
      if (diff / temp_ref[i] > 0.005f) errors++;
    }
  }
  bool pass = errors == 0;
  printf(pass ? "PASS\n" : "FAIL (%d errors)\n", errors);
  return pass ? 0 : 1;
}
