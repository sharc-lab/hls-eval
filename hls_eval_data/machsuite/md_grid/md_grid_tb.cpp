#include <assert.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "md_grid.h"

static inline int fd_printf(int fd, const char *format, ...) {
    va_list args;
    int buffered, written, status;
    char buffer[256];
    va_start(args, format);
    buffered = vsnprintf(buffer, 256, format, args);
    va_end(args);
    assert(
        buffered < 256 && "Overran fd_printf buffer---output possibly corrupt");
    written = 0;
    while (written < buffered) {
        status = write(fd, &buffer[written], buffered - written);
        assert(status >= 0 && "Write failed");
        written += status;
    }
    assert(written == buffered && "Wrote more data than given");
    return written;
}

char *readfile(int fd) {
    char *p;
    struct stat s;
    off_t len;
    ssize_t bytes_read, status;

    assert(fd > 1 && "Invalid file descriptor");
    assert(0 == fstat(fd, &s) && "Couldn't determine file size");
    len = s.st_size;
    assert(len > 0 && "File is empty");
    p = (char *)malloc(len + 1);
    bytes_read = 0;
    while (bytes_read < len) {
        status = read(fd, &p[bytes_read], len - bytes_read);
        assert(status >= 0 && "read() failed");
        bytes_read += status;
    }
    p[len] = (char)0;
    close(fd);
    return p;
}

char *find_section_start(char *s, int n) {
    int i = 0;

    assert(n >= 0 && "Invalid section number");
    if (n == 0)
        return s;

    while (i < n && (*s) != (char)0) {

        if (s[0] == '%' && s[1] == '%' && s[2] == '\n') {
            i++;
        }
        s++;
    }
    if (*s != (char)0)
        return s + 2;
    return s;
}

int write_section_header(int fd) {
    assert(fd > 1 && "Invalid file descriptor");
    fd_printf(fd, "%%%%\n");
    return 0;
}

int parse_int32_t_array(char *s, int32_t *arr, int n) {
    char *line, *endptr;
    int i = 0;
    int32_t v;
    assert(s != NULL && "Invalid input string");
    line = strtok(s, "\n");
    while (line != NULL && i < n) {
        endptr = line;
        v = (int32_t)(strtol(line, &endptr, 10));
        if ((*endptr) != (char)0) {
            fprintf(stderr, "Invalid input: line %d of section\n", i);
        }
        arr[i] = v;
        i++;
        line[strlen(line)] = '\n';
        line = strtok(NULL, "\n");
    }
    if (line != NULL) {
        line[strlen(line)] = '\n';
    }
    return 0;
}

int write_int32_t_array(int fd, int32_t *arr, int n) {
    int i;
    assert(fd > 1 && "Invalid file descriptor");
    for (i = 0; i < n; i++) {
        fd_printf(fd, "%" PRId32 "\n", arr[i]);
    }
    return 0;
}

int parse_double_array(char *s, double *arr, int n) {
    char *line, *endptr;
    int i = 0;
    double v;
    assert(s != NULL && "Invalid input string");
    line = strtok(s, "\n");
    while (line != NULL && i < n) {
        endptr = line;
        v = (double)(strtod(line, &endptr));
        if ((*endptr) != (char)0) {
            fprintf(stderr, "Invalid input: line %d of section\n", i);
        }
        arr[i] = v;
        i++;
        line[strlen(line)] = '\n';
        line = strtok(NULL, "\n");
    }
    if (line != NULL) {
        line[strlen(line)] = '\n';
    }
    return 0;
}

int write_double_array(int fd, double *arr, int n) {
    int i;
    assert(fd > 1 && "Invalid file descriptor");
    for (i = 0; i < n; i++) {
        fd_printf(
            fd,
            "%"
            ".16f"
            "\n",
            arr[i]);
    }
    return 0;
}

struct bench_args_t {
    int32_t n_points[blockSide][blockSide][blockSide];
    dvector_t force[blockSide][blockSide][blockSide][densityFactor];
    dvector_t position[blockSide][blockSide][blockSide][densityFactor];
};

int INPUT_SIZE = sizeof(struct bench_args_t);

#define EPSILON ((TYPE)1.0e-6)

void run_benchmark(void *vargs) {
    struct bench_args_t *args = (struct bench_args_t *)vargs;
    md(args->n_points, args->force, args->position);
}

/* Input format:
%% Section 1
int32_t[blockSide^3]: grid populations
%% Section 2
TYPE[blockSide^3*densityFactor]: positions
*/

void input_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Load input string
    p = readfile(fd);

    s = find_section_start(p, 1);
    parse_int32_t_array(
        s, (int32_t *)(data->n_points), blockSide * blockSide * blockSide);

    s = find_section_start(p, 2);
    parse_double_array(
        s,
        (double *)(data->position),
        3 * blockSide * blockSide * blockSide * densityFactor);
    free(p);
}

void data_to_input(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;

    write_section_header(fd);
    write_int32_t_array(
        fd, (int32_t *)(data->n_points), blockSide * blockSide * blockSide);

    write_section_header(fd);
    write_double_array(
        fd,
        (double *)(data->position),
        3 * blockSide * blockSide * blockSide * densityFactor);
}

/* Output format:
%% Section 1
TYPE[blockSide^3*densityFactor]: force
*/

void output_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Load input string
    p = readfile(fd);

    s = find_section_start(p, 1);
    parse_double_array(
        s,
        (double *)data->force,
        3 * blockSide * blockSide * blockSide * densityFactor);
    free(p);
}

void data_to_output(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;

    write_section_header(fd);
    write_double_array(
        fd,
        (double *)data->force,
        3 * blockSide * blockSide * blockSide * densityFactor);
}

int check_data(void *vdata, void *vref) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    struct bench_args_t *ref = (struct bench_args_t *)vref;
    int has_errors = 0;
    int i, j, k, d;
    TYPE diff_x, diff_y, diff_z;

    for (i = 0; i < blockSide; i++) {
        for (j = 0; j < blockSide; j++) {
            for (k = 0; k < blockSide; k++) {
                for (d = 0; d < densityFactor; d++) {
                    diff_x =
                        data->force[i][j][k][d].x - ref->force[i][j][k][d].x;
                    diff_y =
                        data->force[i][j][k][d].y - ref->force[i][j][k][d].y;
                    diff_z =
                        data->force[i][j][k][d].z - ref->force[i][j][k][d].z;

                    has_errors |= (diff_x < -EPSILON) || (EPSILON < diff_x);
                    if ((diff_x < -EPSILON) || (EPSILON < diff_x)) {
                        printf(
                            "Mismatch at force[%d][%d][%d][%d].x\n",
                            i,
                            j,
                            k,
                            d);
                        printf("  Actual: %f\n", data->force[i][j][k][d].x);
                        printf("  Expected: %f\n", ref->force[i][j][k][d].x);
                        printf("  Diff: %f\n", diff_x);
                    }

                    has_errors |= (diff_y < -EPSILON) || (EPSILON < diff_y);
                    if ((diff_y < -EPSILON) || (EPSILON < diff_y)) {
                        printf(
                            "Mismatch at force[%d][%d][%d][%d].y\n",
                            i,
                            j,
                            k,
                            d);
                        printf("  Actual: %f\n", data->force[i][j][k][d].y);
                        printf("  Expected: %f\n", ref->force[i][j][k][d].y);
                        printf("  Diff: %f\n", diff_y);
                    }

                    has_errors |= (diff_z < -EPSILON) || (EPSILON < diff_z);
                    if ((diff_z < -EPSILON) || (EPSILON < diff_z)) {
                        printf(
                            "Mismatch at force[%d][%d][%d][%d].z\n",
                            i,
                            j,
                            k,
                            d);
                        printf("  Actual: %f\n", data->force[i][j][k][d].z);
                        printf("  Expected: %f\n", ref->force[i][j][k][d].z);
                        printf("  Diff: %f\n", diff_z);
                    }
                }
            }
        }
    }

    // Return true if it's correct.
    return !has_errors;
}

int main() {
    char *in_file;
    char *check_file;

    in_file = "input.data";
    check_file = "check.data";

    int in_fd;
    char *data;
    data = (char *)malloc(INPUT_SIZE);
    assert(data != NULL && "Out of memory");
    in_fd = open(in_file, O_RDONLY);
    assert(in_fd > 0 && "Couldn't open input data file");
    input_to_data(in_fd, data);

    run_benchmark(data);

    int out_fd;
    out_fd = open(
        "output.data",
        O_WRONLY | O_CREAT | O_TRUNC,
        S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
    assert(out_fd > 0 && "Couldn't open output data file");
    data_to_output(out_fd, data);
    close(out_fd);

    int check_fd;
    char *ref;
    ref = (char *)malloc(INPUT_SIZE);
    assert(ref != NULL && "Out of memory");
    check_fd = open(check_file, O_RDONLY);
    assert(check_fd > 0 && "Couldn't open check data file");
    output_to_data(check_fd, ref);

    if (!check_data(data, ref)) {
        fprintf(stderr, "Benchmark results are incorrect\n");
        return -1;
    }

    free(data);
    free(ref);

    printf("Success.\n");
    return 0;
}
