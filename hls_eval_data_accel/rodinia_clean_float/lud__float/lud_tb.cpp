// Minimal software testbench: loads input.data, runs workload() in place,
// and compares against check.data (bit-exact, matching the original
// local_support.cpp's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "lud.h"
#include "support.h"

extern "C" void workload(float result[GRID_ROWS * GRID_COLS]);

static float load(const char *filename, float out[GRID_ROWS * GRID_COLS]) {
  int fd = open(filename, O_RDONLY);
  if (fd < 0) { perror(filename); exit(1); }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), out, GRID_ROWS * GRID_COLS);
  free(p);
  return 0;
}

int main() {
  static float result[GRID_ROWS * GRID_COLS];
  static float reference[GRID_ROWS * GRID_COLS];

  load("input.data", result);
  workload(result);
  load("check.data", reference);

  bool pass = memcmp(result, reference, GRID_ROWS * GRID_COLS * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
