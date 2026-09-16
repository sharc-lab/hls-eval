#pragma once
/*
 * Portable, OpenCL-free reimplementation of the Rosetta-benchmark-suite
 * text I/O helpers (originally common/support.h + support.c in this
 * repository's Rodinia port). Each data file is plain text: one numeric
 * value per line, with "%%\n" lines marking section boundaries. This
 * header only keeps what a software testbench needs to read input.data /
 * check.data directly and call the kernel's workload() in-process --
 * the OpenCL/FPGA host-program plumbing (run_benchmark, cl_context, ...)
 * is intentionally dropped.
 */
#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static inline char *readfile(int fd) {
  struct stat s;
  assert(fd > 1 && "Invalid file descriptor");
  assert(0 == fstat(fd, &s) && "Couldn't determine file size");
  off_t len = s.st_size;
  assert(len > 0 && "File is empty");
  char *p = (char *)malloc(len + 1);
  p[len] = 0;
  ssize_t bytes_read = 0, status;
  while (bytes_read < len) {
    status = read(fd, &p[bytes_read], len - bytes_read);
    assert(status >= 0 && "read() failed");
    bytes_read += status;
  }
  close(fd);
  return p;
}

static inline char *find_section_start(char *s, int n) {
  assert(n >= 0 && "Invalid section number");
  if (n == 0) return s;
  int i = 0;
  while (i < n && (*s) != (char)0) {
    if (s[0] == '%' && s[1] == '%' && s[2] == '\n') i++;
    s++;
  }
  if (*s != (char)0) return s + 2;
  return s;
}

#define GENERATE_PARSE_TYPE_ARRAY(TYPE, STRTOTYPE)                         \
  static inline int parse_##TYPE##_array(char *s, TYPE *arr, int n) {      \
    char *line, *endptr;                                                   \
    int i = 0;                                                             \
    assert(s != NULL && "Invalid input string");                           \
    line = strtok(s, "\n");                                                \
    while (line != NULL && i < n) {                                        \
      endptr = line;                                                       \
      arr[i] = (TYPE)(STRTOTYPE(line, &endptr));                           \
      i++;                                                                 \
      line[strlen(line)] = '\n'; /* undo strtok's mutation */              \
      line = strtok(NULL, "\n");                                           \
    }                                                                      \
    if (line != NULL) line[strlen(line)] = '\n';                           \
    return 0;                                                              \
  }

#define STRTOL_10(a, b) strtol(a, b, 10)
GENERATE_PARSE_TYPE_ARRAY(uint8_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(uint16_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(uint32_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(uint64_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(int8_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(int16_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(int32_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(int64_t, STRTOL_10)
GENERATE_PARSE_TYPE_ARRAY(float, strtof)
GENERATE_PARSE_TYPE_ARRAY(double, strtod)

static inline int parse_string(char *s, char *arr, int n) {
  assert(s != NULL && "Invalid input string");
  int k;
  if (n < 0) {
    k = 0;
    while (s[k] != (char)0 && s[k + 1] != (char)0 && s[k + 2] != (char)0 &&
           !(s[k] == '\n' && s[k + 1] == '%' && s[k + 2] == '%')) {
      k++;
    }
  } else {
    k = n;
  }
  memcpy(arr, s, k);
  if (n < 0) arr[k] = 0;
  return 0;
}

static inline char *parse_float_array2D(char *s, float *arr, int num_row, int num_col) {
  char *line, *endptr;
  line = strtok(s, "\n");
  for (int row = 0; row < num_row; ++row) {
    for (int col = 0; col < num_col; ++col) {
      endptr = line;
      arr[row * num_col + col] = strtof(line, &endptr);
      line[strlen(line)] = '\n'; /* undo strtok's mutation */
      line = strtok(NULL, "\n");
    }
  }
  return line;
}

#define STAC_EXPANDED(f_pfx, t, f_sfx) f_pfx##t##f_sfx
#define STAC(f_pfx, t, f_sfx) STAC_EXPANDED(f_pfx, t, f_sfx)
