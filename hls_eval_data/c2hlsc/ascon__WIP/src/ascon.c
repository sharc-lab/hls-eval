
char* bytes_to_hex(uint8_t* bytes, uint32_t len)
{
    char h;
    uint32_t i;
    char* result = (char*)malloc(len * 2 + 1);

    for (i = 0; i < len; i++)
    {
	sprintf(&result[2 * i], "%02X", bytes[i]);
    }

    result[len * 2] = '\0';
    return result;
}

uint8_t* hex_to_bytes(char *hex_string, uint32_t len)
{
    uint8_t b;
    uint32_t i;
    uint8_t* result = (uint8_t*)malloc(len / 2 + 1);
    char hex_byte[3] = "00";

    for (i = 0 ; i < len / 2; i++) 
    {
	hex_byte[0] = hex_string[2 * i];
	hex_byte[1] = hex_string[2 * i + 1];
	b = (uint8_t)strtol(hex_byte, NULL, 16);
	result[i] = b;	
    }

    result[len / 2] = '\0'; 
    return result;
}


#define ROTATE_RIGHT(x, i) (((x) >> (i)) | ((x) << (64 - (i))))

void round_i(uint64_t *state, uint8_t round);
void s_box_layer(uint64_t *state, uint64_t *t);
void diffusion_layer(uint64_t *state, uint64_t *t);


const uint8_t round_constants[12] = {
    0xf0, 0xe1, 0xd2, 0xc3, 0xb4, 0xa5,
    0x96, 0x87, 0x78, 0x69, 0x5a, 0x4b
};

void permute_a(uint64_t *state)
{
    uint8_t i;
    for (i = 0; i < N_ROUNDS_A; i++)
	round_i(state, i);
}

void permute_b(uint64_t *state)
{
    uint64_t i;
    for (i = 0; i < N_ROUNDS_B; i++)
	round_i(state, i + 6);
}

void round_i(uint64_t *state, uint8_t round)
{
    uint64_t temp[5];
    state[2] ^= round_constants[round];
    s_box_layer(state, temp);
    diffusion_layer(state, temp);
}

void s_box_layer(uint64_t *state, uint64_t *t)
{
    state[0] ^= state[4];
    state[4] ^= state[3];
    state[2] ^= state[1];

    t[0] = state[0] ^ (~state[1] & state[2]);
    t[1] = state[1] ^ (~state[2] & state[3]);
    t[2] = state[2] ^ (~state[3] & state[4]);
    t[3] = state[3] ^ (~state[4] & state[0]);
    t[4] = state[4] ^ (~state[0] & state[1]);

    t[1] ^= t[0];
    t[0] ^= t[4];
    t[3] ^= t[2];
    t[2] = ~t[2];
}

void diffusion_layer(uint64_t *state, uint64_t *t)
{
    state[0] = t[0] ^ ROTATE_RIGHT(t[0], 19) ^ ROTATE_RIGHT(t[0], 28);
    state[1] = t[1] ^ ROTATE_RIGHT(t[1], 61) ^ ROTATE_RIGHT(t[1], 39);
    state[2] = t[2] ^ ROTATE_RIGHT(t[2], 1) ^ ROTATE_RIGHT(t[2], 6);
    state[3] = t[3] ^ ROTATE_RIGHT(t[3], 10) ^ ROTATE_RIGHT(t[3], 17);
    state[4] = t[4] ^ ROTATE_RIGHT(t[4], 7) ^ ROTATE_RIGHT(t[4], 41);
}


void encrypt(uint8_t *cipher_text, uint8_t *tag, uint8_t *plain_text, uint32_t plain_text_len, uint8_t *key, uint8_t *associated_data, uint32_t adlen, uint8_t *nonce)
{
    Ascon_data data;
    init_data(&data, plain_text, plain_text_len, associated_data, adlen, key, nonce);
    initialize_state(&data);
    printf("state after init: %s\n", bytes_to_hex((uint8_t*)data.state, STATE_SIZE));
    process_associated_data(&data);
    printf("state after process ad: %s\n", bytes_to_hex((uint8_t*)data.state, STATE_SIZE));
    process_plain_text(cipher_text, &data);
    finalize(tag, &data);
}

void init_data(Ascon_data *data, uint8_t *message, uint32_t message_len, uint8_t *associated_data, uint32_t adlen, uint8_t *key, uint8_t *nonce)
{
    data->message = message;
    data->message_len = message_len;
    data->associated_data = associated_data;
    data->adlen = adlen;
    load_bytes_output_reversed((uint8_t*)data->key, 0, key, 8);
    load_bytes_output_reversed((uint8_t*)&data->key[1], 0, key + 8, 8);
    load_bytes_output_reversed((uint8_t*)data->nonce, 0, nonce, 8);
    load_bytes_output_reversed((uint8_t*)&data->nonce[1], 0, nonce + 8, 8);
}

void initialize_state(Ascon_data *data)
{
    data->state[0] = 0x80400c0600000000;

    data->state[1] = data->key[0];
    data->state[2] = data->key[1];
    data->state[3] = data->nonce[0];
    data->state[4] = data->nonce[1];

    //printf("state before init perm: %s\n", bytes_to_hex((uint8_t*)data->state, STATE_SIZE));
    permute_a(data->state);
    //printf("state after init perm: %s\n", bytes_to_hex((uint8_t*)data->state, STATE_SIZE));

    data->state[3] ^= data->key[0];
    data->state[4] ^= data->key[1];
}

void process_associated_data(Ascon_data *data)
{
    uint64_t temp;
    uint32_t n_ad_blocks, i;
    if (data->adlen > 0)
    {
	n_ad_blocks = data->adlen / BLOCK_SIZE + 1;
	for (i = 0; i < n_ad_blocks; i++) 
	{
	    get_block_padded((uint8_t*)&temp, data->associated_data, data->adlen, i);		
	    //printf("ad block %d: %s\n", i, bytes_to_hex((uint8_t*)&temp, 8));
	    data->state[0] ^= temp;
	    permute_b(data->state);
	}
    }
    data->state[4] ^= 0x01;
}

void process_plain_text(uint8_t *cipher_text, Ascon_data *data)
{
    uint64_t temp;
    uint32_t n_message_blocks, i;
    n_message_blocks = data->message_len / BLOCK_SIZE + 1;
    for (i = 0; i < n_message_blocks - 1; i++)
    {
	get_block_padded((uint8_t*)&temp, data->message, data->message_len, i);
	//printf("pi: %s\n", bytes_to_hex((uint8_t*)&temp, 8));
	data->state[0] ^= temp;
	load_bytes_input_reversed((uint8_t*)((uint64_t*)cipher_text + i), (uint8_t*)data->state, BLOCK_SIZE);
	permute_b(data->state);
    }
    get_block_padded((uint8_t*)&temp, data->message, data->message_len, n_message_blocks - 1);
    //printf("pi: %s\n", bytes_to_hex((uint8_t*)&temp, 8));
    data->state[0] ^= temp;
    //printf("s[0]: %s\n", bytes_to_hex((uint8_t*)data->state, 8));
    load_bytes_input_reversed((uint8_t*)((uint64_t*)cipher_text + n_message_blocks - 1), (uint8_t*)data->state, data->message_len % BLOCK_SIZE);
} 
    
	
/**
 * Returns a index th block of data. Pladded with 1 || 0 *. For plain text, ad or 
 * cipher text.
 */
void get_block_padded(uint8_t *output, uint8_t *data, uint32_t data_len, uint32_t index)
{
    uint32_t offset, count;
    offset = index * BLOCK_SIZE;
    count = ((data_len - offset) < BLOCK_SIZE) ? (data_len - offset) : BLOCK_SIZE;
    //memcpy(output, data + offset, count);
    load_bytes_output_reversed(output, 0, data + offset, count);
    if (count < BLOCK_SIZE)
    {
	output[BLOCK_SIZE - count - 1] = 0x80;
	memset(output, 0, BLOCK_SIZE - count - 1);
    }
}
    
void load_bytes_output_reversed(uint8_t* output, uint8_t output_offset, uint8_t* input, uint8_t count)
{
    uint8_t i;
    output_offset = BLOCK_SIZE - output_offset - 1;
    for (i = 0; i < count; i++)
	output[output_offset - i] = input[i];
}

void finalize(uint8_t *tag, Ascon_data *data)
{
    data->state[1] ^= data->key[0];
    data->state[2] ^= data->key[1];
    permute_a(data->state);
    data->state[3] ^= data->key[0];
    data->state[4] ^= data->key[1];
    load_bytes_input_reversed(tag, (uint8_t*)(data->state + 3), 8);
    load_bytes_input_reversed(tag + 8, (uint8_t*)(data->state + 4), 8);
}

void load_bytes_input_reversed(uint8_t *output, uint8_t *input, uint8_t count)
{
    uint8_t i;
    for (i = 0; i < count; i++)
	output[i] = input[BLOCK_SIZE - i - 1];
}

uint8_t decrypt(uint8_t *plain_text, uint8_t *tag, uint8_t *cipher_text, uint32_t cipher_text_len, uint8_t *key, uint8_t *associated_data, uint32_t adlen, uint8_t *nonce)
{
    Ascon_data data;
    uint8_t tag_match, tag_new[TAG_SIZE], i;
    init_data(&data, cipher_text, cipher_text_len, associated_data, adlen, key, nonce);
    initialize_state(&data);
    //printf("state after init: %s\n", bytes_to_hex((uint8_t*)data.state, STATE_SIZE));
    process_associated_data(&data);
    //printf("state after process ad: %s\n", bytes_to_hex((uint8_t*)data.state, STATE_SIZE));
    process_cipher_text(plain_text, &data);
    finalize(tag_new, &data);
    tag_match = 0;
    for (i = 0; i < TAG_SIZE; i++)
	tag_match |= tag[i] ^ tag_new[i];
    return !tag_match;
}

void process_cipher_text(uint8_t *plain_text, Ascon_data *data)
{
    uint64_t ci, temp;
    uint32_t n_message_blocks, i;
    uint8_t last_block_size, *last_block;
    n_message_blocks = data->message_len / BLOCK_SIZE + (data->message_len % BLOCK_SIZE > 0);
    printf("n_message_blocks: %d\n", n_message_blocks);
    for (i = 0; i < n_message_blocks - 1; i++)
    {
	load_bytes_output_reversed((uint8_t*)&ci, 0, (uint8_t*)((uint64_t*)data->message + i), BLOCK_SIZE);
	temp = ci ^ data->state[0];
	load_bytes_input_reversed((uint8_t*)((uint64_t*)plain_text + i), (uint8_t*)&temp, BLOCK_SIZE);
	data->state[0] = ci;
	permute_b(data->state);
    }
    last_block_size = data->message_len % BLOCK_SIZE;
    load_bytes_output_reversed((uint8_t*)&ci, 0, (uint8_t*)((uint64_t*)data->message + n_message_blocks - 1), last_block_size);
    temp = ci ^ data->state[0];
    last_block = (uint8_t*)((uint64_t*)plain_text + n_message_blocks - 1);
    load_bytes_input_reversed(last_block, (uint8_t*)&temp, last_block_size);
    get_block_padded((uint8_t*)&temp, last_block, last_block_size, 0);
    data->state[0] ^= temp;
}


