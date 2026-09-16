// ap_fixed testbench: loads input.data's 7 sections as float, copies into
// fixed_t arrays, runs workload(), and compares against check.data with
// fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "cfd_flux.h"
#include "fpx_check.h"
#include "support.h"

extern "C" void workload(fixed_t result[SIZE * NVAR],
                          fixed_t elements_surrounding_elements[SIZE * NNB],
                          fixed_t normals[SIZE * NNB * NDIM],
                          fixed_t variables[SIZE * NVAR],
                          fixed_t fc_momentum_x[SIZE * NDIM],
                          fixed_t fc_momentum_y[SIZE * NDIM],
                          fixed_t fc_momentum_z[SIZE * NDIM],
                          fixed_t fc_density_energy[SIZE * NDIM]);

template <int N>
static void load_section(char *p, int n, fixed_t (&arr)[N]) {
  static float tmp[N];
  parse_float_array(find_section_start(p, n), tmp, N);
  for (int i = 0; i < N; i++) arr[i] = tmp[i];
}

int main() {
  static fixed_t result[SIZE * NVAR] = {};
  static fixed_t elements_surrounding_elements[SIZE * NNB];
  static fixed_t normals[SIZE * NNB * NDIM];
  static fixed_t variables[SIZE * NVAR];
  static fixed_t fc_momentum_x[SIZE * NDIM];
  static fixed_t fc_momentum_y[SIZE * NDIM];
  static fixed_t fc_momentum_z[SIZE * NDIM];
  static fixed_t fc_density_energy[SIZE * NDIM];
  static float result_ref[SIZE * NVAR];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  load_section(p, 1, elements_surrounding_elements);
  load_section(p, 2, normals);
  load_section(p, 3, variables);
  load_section(p, 4, fc_momentum_x);
  load_section(p, 5, fc_momentum_y);
  load_section(p, 6, fc_momentum_z);
  load_section(p, 7, fc_density_energy);
  free(p);

  workload(result, elements_surrounding_elements, normals, variables,
           fc_momentum_x, fc_momentum_y, fc_momentum_z, fc_density_energy);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, SIZE * NVAR);
  free(p2);

  fpx_check::ArrayChecker checker("result");
  for (int i = 0; i < SIZE * NVAR; i++)
    checker.add((double)(float)result[i], (double)result_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
