// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), runs the ap_fixed workload(), and compares
// with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "srad.h"
#include "support.h"

extern "C" void workload(fixed_t J[(ROWS + 3) * COLS], fixed_t Jout[(ROWS + 3) * COLS]);

static void load_J(const char *filename, fixed_t J[(ROWS + 3) * COLS]) {
  static float tmp[(ROWS + 3) * COLS];
  int fd = open(filename, O_RDONLY);
  if (fd < 0) { perror(filename); exit(1); }
  char *p = readfile(fd);
  char *s = find_section_start(p, 1);
  memset(tmp, 0, COLS * sizeof(float));
  parse_float_array(s, tmp + COLS, ROWS * COLS);
  memset(tmp + (ROWS + 1) * COLS, 0, 2 * COLS * sizeof(float));
  free(p);
  for (int i = 0; i < (ROWS + 3) * COLS; i++) J[i] = tmp[i];
}

int main() {
  static fixed_t J[(ROWS + 3) * COLS];
  static fixed_t Jout[(ROWS + 3) * COLS];
  static float Jout_ref[(ROWS + 3) * COLS];

  load_J("input.data", J);
  workload(J, Jout);

  int fd = open("check.data", O_RDONLY);
  if (fd < 0) { perror("check.data"); return 1; }
  char *p = readfile(fd);
  char *s = find_section_start(p, 1);
  memset(Jout_ref, 0, COLS * sizeof(float));
  parse_float_array(s, Jout_ref + COLS, ROWS * COLS);
  free(p);

  fpx_check::ArrayChecker checker("Jout");
  for (int i = 0; i < ROWS * COLS; i++)
    checker.add((double)(float)Jout[COLS + i], (double)Jout_ref[COLS + i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
