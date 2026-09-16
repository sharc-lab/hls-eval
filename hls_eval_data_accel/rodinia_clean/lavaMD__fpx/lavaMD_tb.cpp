// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), repacks into the padded box grid as fixed_t,
// runs the ap_fixed workload(), and compares with fpx_check's
// numpy.allclose-style tolerance.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "lavaMD.h"
#include "support.h"

extern "C" void workload(TYPE pos_i[N_PADDED * POS_DIM], TYPE q_i[N_PADDED], TYPE pos_o[N * POS_DIM]);

int main() {
  static float pos_i_f[N * POS_DIM];
  static float q_i_f[N];
  static TYPE pos_o[N * POS_DIM];
  static float pos_o_ref[N * POS_DIM];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  char *s = find_section_start(p, 1);
  s = parse_float_array2D(s, pos_i_f, N, POS_DIM);
  parse_float_array(s, q_i_f, N);
  free(p);

  static TYPE pos_i[N * POS_DIM];
  static TYPE q_i[N];
  for (int i = 0; i < N * POS_DIM; ++i) pos_i[i] = pos_i_f[i];
  for (int i = 0; i < N; ++i) q_i[i] = q_i_f[i];

  // Re-pack into the padded box grid workload() expects (matches
  // local_support.c's run_benchmark() exactly).
  const int POS_I_SIZE = sizeof(TYPE) * DIMENSION_3D_PADDED * NUMBER_PAR_PER_BOX * POS_DIM;
  const int Q_I_SIZE = sizeof(TYPE) * DIMENSION_3D_PADDED * NUMBER_PAR_PER_BOX;
  const int LINE_1D_SIZE = sizeof(TYPE) * DIMENSION_1D * NUMBER_PAR_PER_BOX;
  const int LINE_1D_LEN = DIMENSION_1D * NUMBER_PAR_PER_BOX;

  TYPE *pos_i_padded = (TYPE *)malloc(POS_I_SIZE);
  TYPE *q_i_padded = (TYPE *)malloc(Q_I_SIZE);
  memset(pos_i_padded, 0, POS_I_SIZE);
  memset(q_i_padded, 0, Q_I_SIZE);

  int base_addr_q = DIMENSION_2D_PADDED * NUMBER_PAR_PER_BOX;
  int base_addr_pos = DIMENSION_2D_PADDED * NUMBER_PAR_PER_BOX * POS_DIM;
  for (int i = 0; i < DIMENSION_1D; ++i) {
    base_addr_q += (DIMENSION_1D_PADDED + 1) * NUMBER_PAR_PER_BOX;
    base_addr_pos += (DIMENSION_1D_PADDED + 1) * NUMBER_PAR_PER_BOX * POS_DIM;
    for (int j = 0; j < DIMENSION_1D; ++j) {
      int num_lines = i * DIMENSION_1D + j;
      memcpy(q_i_padded + base_addr_q, q_i + num_lines * LINE_1D_LEN, LINE_1D_SIZE);
      memcpy(pos_i_padded + base_addr_pos, pos_i + num_lines * LINE_1D_LEN * POS_DIM, LINE_1D_SIZE * POS_DIM);
      base_addr_q += (DIMENSION_1D + 2) * NUMBER_PAR_PER_BOX;
      base_addr_pos += (DIMENSION_1D + 2) * NUMBER_PAR_PER_BOX * POS_DIM;
    }
    base_addr_q += (DIMENSION_1D_PADDED - 1) * NUMBER_PAR_PER_BOX;
    base_addr_pos += (DIMENSION_1D_PADDED - 1) * NUMBER_PAR_PER_BOX * POS_DIM;
  }

  workload(pos_i_padded, q_i_padded, pos_o);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array2D(find_section_start(p2, 1), pos_o_ref, N, POS_DIM);
  free(p2);

  fpx_check::ArrayChecker checker("pos_o");
  for (int i = 0; i < N * POS_DIM; ++i)
    checker.add((double)(float)pos_o[i], (double)pos_o_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
