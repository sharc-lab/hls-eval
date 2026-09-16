// Minimal software testbench: loads input.data (seqA, seqB), runs
// workload() for a single job (the original harness just replicated the
// same job 1024x for throughput profiling -- correctness only needs one),
// and compares against check.data (bit-exact, matching the original
// local_support.c's check_data()).
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "nw.h"
#include "support.h"

extern "C" void workload(char *SEQA, char *SEQB, char *alignedA, char *alignedB, int num_jobs);

int main() {
  static char seqA[ALEN] = {};
  static char seqB[BLEN] = {};
  static char alignedA[ALEN + BLEN] = {};
  static char alignedB[ALEN + BLEN] = {};
  static char alignedA_ref[ALEN + BLEN] = {};
  static char alignedB_ref[ALEN + BLEN] = {};

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_string(find_section_start(p, 1), seqA, ALEN);
  parse_string(find_section_start(p, 2), seqB, BLEN);
  free(p);

  workload(seqA, seqB, alignedA, alignedB, 1);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_string(find_section_start(p2, 1), alignedA_ref, ALEN + BLEN);
  parse_string(find_section_start(p2, 2), alignedB_ref, ALEN + BLEN);
  free(p2);

  bool pass = memcmp(alignedA, alignedA_ref, ALEN + BLEN) == 0 &&
              memcmp(alignedB, alignedB_ref, ALEN + BLEN) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
