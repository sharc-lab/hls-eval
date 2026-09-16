// Minimal software testbench: loads input.data (variables, areas), runs
// workload(), and compares against check.data (bit-exact, matching the
// original local_support.cpp's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "cfd_step_factor.h"
#include "support.h"

extern "C" void workload(float result[SIZE], float variables[SIZE * NVAR], float areas[SIZE]);

int main() {
  static float result[SIZE] = {};
  static float variables[SIZE * NVAR];
  static float areas[SIZE];
  static float result_ref[SIZE];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), variables, SIZE * NVAR);
  parse_float_array(find_section_start(p, 2), areas, SIZE);
  free(p);

  workload(result, variables, areas);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, SIZE);
  free(p2);

  bool pass = memcmp(result, result_ref, SIZE * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
