#include "hex_utils.h"
#include <stdlib.h>
#include <stdio.h>

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
