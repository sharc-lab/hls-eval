// Minimal software testbench: loads input.data (a GRID_ROWS*GRID_COLS
// image), places it into the padded img buffer workload() expects, runs
// workload(), and compares against check.data (bit-exact, matching the
// original local_support.cpp's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "dilate.h"
#include "support.h"

extern "C" void workload(float result[GRID_ROWS * GRID_COLS],
                          float img[(GRID_ROWS + 2 * MAX_RADIUS) * GRID_COLS]);

int main() {
  static float img[(GRID_ROWS + 2 * MAX_RADIUS) * GRID_COLS] = {};
  static float result[GRID_ROWS * GRID_COLS];
  static float result_ref[GRID_ROWS * GRID_COLS];
  static float tmp_img[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), tmp_img, GRID_ROWS * GRID_COLS);
  free(p);
  int starting_idx = MAX_RADIUS * GRID_COLS;
  for (int i = 0; i < GRID_ROWS; ++i)
    for (int j = 0; j < GRID_COLS; ++j)
      img[starting_idx + i * GRID_COLS + j] = tmp_img[i * GRID_COLS + j];

  workload(result, img);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  bool pass = memcmp(result, result_ref, GRID_ROWS * GRID_COLS * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
