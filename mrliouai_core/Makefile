# mrliouai_core/Makefile
# origin_signature: MrLiouWord
# 零外部依賴建構 — 只需 g++ 支援 C++17

CXX      ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Wpedantic -Iinclude
LDFLAGS  ?= -pthread

BIN      := mrliouai_core
TEST_BIN := mrl_selftest
SRC      := src/main.cpp
TEST_SRC := tests/selftest.cpp

.PHONY: all clean test run

all: $(BIN)

$(BIN): $(SRC) $(wildcard include/mrl/*.hpp)
	$(CXX) $(CXXFLAGS) -o $@ $(SRC) $(LDFLAGS)

$(TEST_BIN): $(TEST_SRC) $(wildcard include/mrl/*.hpp)
	$(CXX) $(CXXFLAGS) -o $@ $(TEST_SRC) $(LDFLAGS)

test: $(TEST_BIN)
	./$(TEST_BIN)

run: $(BIN)
	./$(BIN) --port 8800 --data ./data --vault ./vault

clean:
	rm -f $(BIN) $(TEST_BIN)
