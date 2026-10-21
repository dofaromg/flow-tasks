#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

#include <isa-l.h>

static void die(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    exit(1);
}

static void die_errno(const char *ctx) {
    fprintf(stderr, "FATAL: %s: %s\n", ctx, strerror(errno));
    exit(1);
}

static void ensure_dir(const char *path) {
    struct stat st;
    if (stat(path, &st) == 0) {
        if (!S_ISDIR(st.st_mode)) die("output path exists but is not a directory");
        return;
    }
    if (mkdir(path, 0755) != 0) die_errno("mkdir");
}

static void path_join(char *out, size_t out_sz, const char *dir, const char *name) {
    size_t dl = strlen(dir);
    int needs_slash = (dl > 0 && dir[dl-1] != '/');
    if (snprintf(out, out_sz, "%s%s%s", dir, needs_slash ? "/" : "", name) >= (int)out_sz) {
        die("path too long");
    }
}

static uint8_t* read_file_exact(const char *path, size_t size) {
    FILE *f = fopen(path, "rb");
    if (!f) die_errno("fopen(read)");
    uint8_t *buf = NULL;
    // ISA-L likes aligned buffers; use posix_memalign
    if (posix_memalign((void**)&buf, 64, size) != 0) die("posix_memalign failed");
    size_t n = fread(buf, 1, size, f);
    if (n != size) {
        fclose(f);
        free(buf);
        die("input shard size mismatch (read)");
    }
    fclose(f);
    return buf;
}

static void write_file_exact(const char *path, const uint8_t *buf, size_t size) {
    FILE *f = fopen(path, "wb");
    if (!f) die_errno("fopen(write)");
    size_t n = fwrite(buf, 1, size, f);
    if (n != size) {
        fclose(f);
        die("write failed");
    }
    fclose(f);
}

static int parse_int_arg(const char *a, const char *name) {
    char *end = NULL;
    long v = strtol(a, &end, 10);
    if (!end || *end != '\0') {
        fprintf(stderr, "Bad %s\n", name);
        exit(2);
    }
    return (int)v;
}

static size_t parse_size_arg(const char *a) {
    char *end = NULL;
    unsigned long long v = strtoull(a, &end, 10);
    if (!end || *end != '\0') {
        fprintf(stderr, "Bad size\n");
        exit(2);
    }
    return (size_t)v;
}

static void usage(void) {
    fprintf(stderr,
        "Usage:\n"
        "  isal_rs_encode --k <k> --m <m> --w <w> --size <bytes> --in <data_dir> --out <parity_dir>\n"
        "Reads:  <data_dir>/shard_00.bin..shard_(k-1).bin\n"
        "Writes: <parity_dir>/shard_k.bin..shard_(k+m-1).bin\n"
    );
    exit(2);
}

int main(int argc, char **argv) {
    int k = 0, m = 0, w = 8;
    size_t shard_size = 0;
    const char *in_dir = NULL;
    const char *out_dir = NULL;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--k") && i+1 < argc) k = parse_int_arg(argv[++i], "k");
        else if (!strcmp(argv[i], "--m") && i+1 < argc) m = parse_int_arg(argv[++i], "m");
        else if (!strcmp(argv[i], "--w") && i+1 < argc) w = parse_int_arg(argv[++i], "w");
        else if (!strcmp(argv[i], "--size") && i+1 < argc) shard_size = parse_size_arg(argv[++i]);
        else if (!strcmp(argv[i], "--in") && i+1 < argc) in_dir = argv[++i];
        else if (!strcmp(argv[i], "--out") && i+1 < argc) out_dir = argv[++i];
        else usage();
    }

    if (k <= 0 || m <= 0 || shard_size == 0 || !in_dir || !out_dir) usage();
    if (w != 8) die("This build expects w=8 (GF(2^8)) for simplicity");

    ensure_dir(out_dir);

    // Generate RS matrix (Vandermonde-based)
    // matrix is (k+m) x k. We'll use last m rows for parity.
    uint8_t *enc_matrix = NULL;
    if (posix_memalign((void**)&enc_matrix, 64, (size_t)(k + m) * (size_t)k) != 0) die("posix_memalign enc_matrix");
    gf_gen_rs_matrix(enc_matrix, k + m, k);

    // Init tables for parity rows
    // tables size: 32*k*m for w=8
    uint8_t *gftbls = NULL;
    if (posix_memalign((void**)&gftbls, 64, (size_t)32 * (size_t)k * (size_t)m) != 0) die("posix_memalign gftbls");
    ec_init_tables(k, m, &enc_matrix[k * k], gftbls);

    // Read data shards
    uint8_t **data = calloc((size_t)k, sizeof(uint8_t*));
    uint8_t **parity = calloc((size_t)m, sizeof(uint8_t*));
    if (!data || !parity) die("calloc");

    char pbuf[4096];

    for (int i = 0; i < k; i++) {
        char name[64];
        snprintf(name, sizeof(name), "shard_%02d.bin", i);
        path_join(pbuf, sizeof(pbuf), in_dir, name);
        data[i] = read_file_exact(pbuf, shard_size);
    }

    for (int j = 0; j < m; j++) {
        if (posix_memalign((void**)&parity[j], 64, shard_size) != 0) die("posix_memalign parity");
        memset(parity[j], 0, shard_size);
    }

    // Encode parity
    ec_encode_data((int)shard_size, k, m, gftbls, data, parity);

    // Write parity shards
    for (int j = 0; j < m; j++) {
        char name[64];
        snprintf(name, sizeof(name), "shard_%02d.bin", k + j);
        path_join(pbuf, sizeof(pbuf), out_dir, name);
        write_file_exact(pbuf, parity[j], shard_size);
    }

    // Cleanup
    for (int i = 0; i < k; i++) free(data[i]);
    for (int j = 0; j < m; j++) free(parity[j]);
    free(data);
    free(parity);
    free(enc_matrix);
    free(gftbls);

    return 0;
}
