
int main() {
    unsigned char text[57] = {
        "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"};
    unsigned char buf[SHA256_BLOCK_SIZE];
    SHA256_CTX ctx;
    sha256_init(&ctx);
    sha256_update(
        &(ctx.data),
        &(ctx.datalen),
        &(ctx.state),
        &(ctx.bitlen),
        text,
        strlen(text));
    sha256_final(&ctx, buf);
    for (int i = 0; i < SHA256_BLOCK_SIZE; i++) {
        printf("%x", buf[i]);
    }

    return (0);
}