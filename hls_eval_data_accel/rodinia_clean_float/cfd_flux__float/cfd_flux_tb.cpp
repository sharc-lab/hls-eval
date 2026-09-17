// Minimal software testbench: loads input.data's 7 sections, runs
// workload(), and compares against check.data (bit-exact, matching the
// original local_support.cpp's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "cfd_flux.h"
#include "support.h"

extern "C" void workload(float result[SIZE * NVAR],
                          float elements_surrounding_elements[SIZE * NNB],
                          float normals[SIZE * NNB * NDIM],
                          float variables[SIZE * NVAR],
                          float fc_momentum_x[SIZE * NDIM],
                          float fc_momentum_y[SIZE * NDIM],
                          float fc_momentum_z[SIZE * NDIM],
                          float fc_density_energy[SIZE * NDIM]);

int main() {
  static float result[SIZE * NVAR] = {};
  static float elements_surrounding_elements[SIZE * NNB];
  static float normals[SIZE * NNB * NDIM];
  static float variables[SIZE * NVAR];
  static float fc_momentum_x[SIZE * NDIM];
  static float fc_momentum_y[SIZE * NDIM];
  static float fc_momentum_z[SIZE * NDIM];
  static float fc_density_energy[SIZE * NDIM];
  static float result_ref[SIZE * NVAR];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), elements_surrounding_elements, SIZE * NNB);
  parse_float_array(find_section_start(p, 2), normals, SIZE * NNB * NDIM);
  parse_float_array(find_section_start(p, 3), variables, SIZE * NVAR);
  parse_float_array(find_section_start(p, 4), fc_momentum_x, SIZE * NDIM);
  parse_float_array(find_section_start(p, 5), fc_momentum_y, SIZE * NDIM);
  parse_float_array(find_section_start(p, 6), fc_momentum_z, SIZE * NDIM);
  parse_float_array(find_section_start(p, 7), fc_density_energy, SIZE * NDIM);
  free(p);

  workload(result, elements_surrounding_elements, normals, variables,
           fc_momentum_x, fc_momentum_y, fc_momentum_z, fc_density_energy);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, SIZE * NVAR);
  free(p2);

  bool pass = memcmp(result, result_ref, SIZE * NVAR * sizeof(float)) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
