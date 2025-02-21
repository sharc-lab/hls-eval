std = c99
src = ascon.c ../../utils/hex_utils.c ascon_permutation.c

ascon: $(src)
	gcc -std=$(std) -o $@ $(src)

avr: $(src)
	avr-gcc -Os -DF_CPU=16000000L -mmcu=atmega328p -c $(src)
	avr-gcc -DF_CPU=16000000L -mmcu=atmega328p -o ascon.elf ascon.o hex_utils.o ascon_permutation.o
	avr-objcopy -O ihex ascon.elf ascon.hex 

clean:
	rm ascon.exe
