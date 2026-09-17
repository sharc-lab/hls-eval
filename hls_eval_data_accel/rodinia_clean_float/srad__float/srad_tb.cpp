// Minimal software testbench: loads input.data, runs workload(), and
// compares against check.data (bit-exact, matching the original
// local_support.c's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "srad.h"
#include "support.h"

extern "C" void workload(float J[(ROWS + 3) * COLS], float Jout[(ROWS + 3) * COLS]);

static void load_J(const char *filename, float J[(ROWS + 3) * COLS]) {
  int fd = open(filename, O_RDONLY);
  if (fd < 0) { perror(filename); exit(1); }
  char *p = readfile(fd);
  char *s = find_section_start(p, 1);
  memset(J, 0, COLS * sizeof(float));
  parse_float_array(s, J + COLS, ROWS * COLS);
  memset(J + (ROWS + 1) * COLS, 0, 2 * COLS * sizeof(float));
  free(p);
}

int main() {
  static float J[(ROWS + 3) * COLS];
  static float Jout[(ROWS + 3) * COLS];
  static float Jout_ref[(ROWS + 3) * COLS];

  load_J("input.data", J);
  workload(J, Jout);
  load_J("check.data", Jout_ref);

  bool pass = memcmp(Jout, Jout_ref, ROWS * COLS * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
