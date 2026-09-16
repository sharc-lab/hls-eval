// Minimal software testbench: loads input.data, runs workload(), and
// compares against check.data (bit-exact, matching the original
// local_support.c's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "pathfinder.h"
#include "support.h"

extern "C" void workload(int32_t J[ROWS * COLS], int32_t Jout[COLS]);

int main() {
  static int32_t J[ROWS * COLS];
  static int32_t Jout[COLS];
  static int32_t Jout_ref[COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_int32_t_array(find_section_start(p, 1), J, ROWS * COLS);
  free(p);

  workload(J, Jout);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_int32_t_array(find_section_start(p2, 1), Jout_ref, COLS);
  free(p2);

  bool pass = memcmp(Jout, Jout_ref, COLS * sizeof(int32_t)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
