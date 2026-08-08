# Makefile for PD_AI Wire Protocol
# Compiles and runs wire protocol tests

CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -pedantic
TARGET = wire_test
SRC = pd_ai_wire_test.c
HEADER = PD_AI_wire.h

.PHONY: all clean test help

# Default target
all: $(TARGET)

# Build test executable
$(TARGET): $(SRC) $(HEADER)
	@echo "Compiling $(TARGET)..."
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "✓ Build complete: $(TARGET)"

# Run tests
test: $(TARGET)
	@echo ""
	@echo "Running wire protocol tests..."
	@echo ""
	./$(TARGET)

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(TARGET) *.o
	@echo "✓ Clean complete"

# Show help
help:
	@echo "PD_AI Wire Protocol Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make          - Build the test executable (default)"
	@echo "  make test     - Build and run tests"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make help     - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make && ./wire_test    - Build and run manually"
	@echo "  make test              - Build and run in one step"
