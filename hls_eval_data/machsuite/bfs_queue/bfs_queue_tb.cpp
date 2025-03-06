#include <assert.h>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

#include "bfs_queue.h"

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

int write_uint64_t_array(int fd, uint64_t *arr, int n) {
    int i;
    assert(fd > 1 && "Invalid file descriptor");
    for (i = 0; i < n; i++) {
        fd_printf(fd, "%" PRIu64 "\n", arr[i]);
    }
    return 0;
}

int parse_uint64_t_array(char *s, uint64_t *arr, int n) {
    char *line, *endptr;
    int i = 0;
    uint64_t v;
    assert(s != NULL && "Invalid input string");
    line = strtok(s, "\n");
    while (line != NULL && i < n) {
        endptr = line;
        v = (uint64_t)(strtol(line, &endptr, 10));
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

struct bench_args_t {
    node_t nodes[N_NODES];
    edge_t edges[N_EDGES];
    node_index_t starting_node;
    level_t level[N_NODES];
    edge_index_t level_counts[N_LEVELS];
};

int INPUT_SIZE = sizeof(struct bench_args_t);

void run_benchmark(void *vargs) {
    struct bench_args_t *args = (struct bench_args_t *)vargs;
    bfs(args->nodes,
        args->edges,
        args->starting_node,
        args->level,
        args->level_counts);
}

/* Input format:
%% Section 1
uint64_t[1]: starting node
%% Section 2
uint64_t[N_NODES*2]: node structures (start and end indices of edge lists)
%% Section 3
uint64_t[N_EDGES]: edges structures (just destination node id)
*/

void input_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    uint64_t *nodes;
    int64_t i;

    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Max-ify levels
    for (i = 0; i < N_NODES; i++) {
        data->level[i] = MAX_LEVEL;
    }
    // Load input string
    p = readfile(fd);
    // Section 1: starting node
    s = find_section_start(p, 1);
    parse_uint64_t_array(s, &data->starting_node, 1);

    // Section 2: node structures
    s = find_section_start(p, 2);
    nodes = (uint64_t *)malloc(N_NODES * 2 * sizeof(uint64_t));
    parse_uint64_t_array(s, nodes, N_NODES * 2);
    for (i = 0; i < N_NODES; i++) {
        data->nodes[i].edge_begin = nodes[2 * i];
        data->nodes[i].edge_end = nodes[2 * i + 1];
    }
    free(nodes);
    // Section 3: edge structures
    s = find_section_start(p, 3);
    parse_uint64_t_array(s, (uint64_t *)(data->edges), N_EDGES);
    free(p);
}

void data_to_input(int fd, void *vdata) {
    uint64_t *nodes;
    int64_t i;

    struct bench_args_t *data = (struct bench_args_t *)vdata;
    // Section 1: starting node
    write_section_header(fd);
    write_uint64_t_array(fd, &data->starting_node, 1);
    // Section 2: node structures
    write_section_header(fd);
    nodes = (uint64_t *)malloc(N_NODES * 2 * sizeof(uint64_t));
    for (i = 0; i < N_NODES; i++) {
        nodes[2 * i] = data->nodes[i].edge_begin;
        nodes[2 * i + 1] = data->nodes[i].edge_end;
    }
    write_uint64_t_array(fd, nodes, N_NODES * 2);
    free(nodes);
    // Section 3: edge structures
    write_section_header(fd);
    write_uint64_t_array(fd, (uint64_t *)(&data->edges), N_EDGES);
}

/* Output format:
%% Section 1
uint64_t[N_LEVELS]: horizon counts
*/

void output_to_data(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    char *p, *s;
    // Zero-out everything.
    memset(vdata, 0, sizeof(struct bench_args_t));
    // Load input string
    p = readfile(fd);
    // Section 1: horizon counts
    s = find_section_start(p, 1);
    parse_uint64_t_array(s, data->level_counts, N_LEVELS);
    free(p);
}

void data_to_output(int fd, void *vdata) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    // Section 1
    write_section_header(fd);
    write_uint64_t_array(fd, data->level_counts, N_LEVELS);
}

int check_data(void *vdata, void *vref) {
    struct bench_args_t *data = (struct bench_args_t *)vdata;
    struct bench_args_t *ref = (struct bench_args_t *)vref;
    int has_errors = 0;
    int i;

    // Check that the horizons have the same number of nodes
    // for (i = 0; i < N_LEVELS; i++) {
    //     has_errors |= (data->level_counts[i] != ref->level_counts[i]);
    // }

    for (i = 0; i < N_LEVELS; i++) {
        if (data->level_counts[i] != ref->level_counts[i]) {
            printf(
                "Mismatch at level %d: (actual) %" PRIu64 " != %" PRIu64
                " (expected)\n",
                i,
                data->level_counts[i],
                ref->level_counts[i]);
            has_errors = 1;
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
