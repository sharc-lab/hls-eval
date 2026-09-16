// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), runs the ap_fixed workload(), and compares
// with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "cfd_step_factor.h"
#include "support.h"

extern "C" void workload(fixed_t result[SIZE], fixed_t variables[SIZE * NVAR], fixed_t areas[SIZE]);

int main() {
  static float variables_f[SIZE * NVAR];
  static float areas_f[SIZE];
  static float result_ref[SIZE];

  static fixed_t result[SIZE] = {};
  static fixed_t variables[SIZE * NVAR];
  static fixed_t areas[SIZE];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), variables_f, SIZE * NVAR);
  parse_float_array(find_section_start(p, 2), areas_f, SIZE);
  free(p);

  for (int i = 0; i < SIZE * NVAR; i++) variables[i] = variables_f[i];
  for (int i = 0; i < SIZE; i++) areas[i] = areas_f[i];

  workload(result, variables, areas);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, SIZE);
  free(p2);

  fpx_check::ArrayChecker checker("result");
  for (int i = 0; i < SIZE; i++)
    checker.add((double)(float)result[i], (double)result_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
