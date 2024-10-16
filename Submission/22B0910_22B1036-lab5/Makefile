# Makefile to compile sender and receiver programs

CC = gcc          # Compiler
CFLAGS = -Wall -g # Compiler flags: show all warnings, include debug info
TARGETS = sender receiver # Programs to be built

# Default target to build all programs
all: $(TARGETS)

# Rule to build sender executable
sender: sender.c
	$(CC) $(CFLAGS) -o sender sender.c

# Rule to build receiver executable
receiver: receiver.c
	$(CC) $(CFLAGS) -o receiver receiver.c

# Clean target to remove executables
clean:
	rm -f $(TARGETS)