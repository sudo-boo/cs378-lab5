# Makefile to compile sender and receiver programs

CC = gcc          # Compiler
CFLAGS = -Wall -g # Compiler flags: show all warnings, include debug info
TARGETS = sender receiver # Programs to be built

# Default target to build all programs
all: $(TARGETS)

# Rule to build sender.o
sender: sender.c
	$(CC) $(CFLAGS) -o sender.o sender.c

# Rule to build receiver.o
receiver: receiver.c
	$(CC) $(CFLAGS) -o receiver.o receiver.c

# Clean target to remove object files and executables
clean:
	rm -f *.o
