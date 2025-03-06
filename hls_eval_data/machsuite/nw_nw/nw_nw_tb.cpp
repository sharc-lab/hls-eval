#include <assert.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "nw_nw.h"

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

int parse_string(char *s, char *arr, int n) {
    int k;
    assert(s != NULL && "Invalid input string");

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
    if (n < 0)
        arr[k] = 0;

    return 0;
}

int write_string(int fd, char *arr, int n) {
    int status, written;
    assert(fd > 1 && "Invalid file descriptor");
    if (n < 0) {
        n = strlen(arr);
    }
    written = 0;
    while (written < n) {
        status = write(fd, &arr[written], n - written);
        assert(status >= 0 && "Write failed");
        written += status;
    }

    do {
        status = write(fd, "\n", 1);
        assert(status >= 0 && "Write failed");
    } while (status == 0);

    return 0;
}

struct bench_args_t {
    char seqA[ALEN];
    char seqB[BLEN];
    char alignedA[ALEN + BLEN];
    char alignedB[ALEN + BLEN];
    int M[(ALEN + 1) * (BLEN + 1)];
    char ptr[(ALEN + 1) * (BLEN + 1)];
};

int INPUT_SIZE = sizeof(struct bench_args_t);

void run_benchmark(void *vargs) {
    struct bench_args_t *args = (struct bench_args_t *)vargs;
    needwun(
        args->seqA,
        args->seqB,
        args->alignedA,
        args->alignedB,
        args->M,
        args->ptr);
}

/* Input format:
%% Section 1
char[]: sequence A
%% Section 2
char[]: sequence B
*/

void input_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Load input string
    p = readfile(fd);

    s = find_section_start(p, 1);
    parse_string(s, data->seqA, ALEN);

    s = find_section_start(p, 2);
    parse_string(s, data->seqB, BLEN);
    free(p);
}

void data_to_input(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;

    write_section_header(fd);
    write_string(fd, data->seqA, ALEN);

    write_section_header(fd);
    write_string(fd, data->seqB, BLEN);

    write_section_header(fd);
}

/* Output format:
%% Section 1
char[sum_size]: aligned sequence A
%% Section 2
char[sum_size]: aligned sequence B
*/

void output_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Load input string
    p = readfile(fd);

    s = find_section_start(p, 1);
    parse_string(s, data->alignedA, ALEN + BLEN);

    s = find_section_start(p, 2);
    parse_string(s, data->alignedB, ALEN + BLEN);
    free(p);
}

void data_to_output(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;

    write_section_header(fd);
    write_string(fd, data->alignedA, ALEN + BLEN);

    write_section_header(fd);
    write_string(fd, data->alignedB, ALEN + BLEN);

    write_section_header(fd);
}

int check_data(void *vdata, void *vref) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    struct bench_args_t *ref = (struct bench_args_t *)vref;
    int has_errors = 0;

    has_errors |= memcmp(data->alignedA, ref->alignedA, ALEN + BLEN);
    has_errors |= memcmp(data->alignedB, ref->alignedB, ALEN + BLEN);

    for (int i = 0; i < ALEN + BLEN; i++) {
        if (data->alignedA[i] != ref->alignedA[i]) {
            printf(
                "ERROR: alignedA[%d] = %c, ref->alignedA[%d] = %c\n",
                i,
                data->alignedA[i],
                i,
                ref->alignedA[i]);
        }
        if (data->alignedB[i] != ref->alignedB[i]) {
            printf(
                "ERROR: alignedB[%d] = %c, ref->alignedB[%d] = %c\n",
                i,
                data->alignedB[i],
                i,
                ref->alignedB[i]);
        }
    }

    // Return true if it's correct.
    return !has_errors;
}

int main(int argc, char **argv) {
    // Parse command line.
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
