CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -std=c11
LDFLAGS ?=
BIN_DIR := ../bin
TARGET := $(BIN_DIR)/isal_rs_encode

# Prefer pkg-config if available
PKG_CFLAGS := $(shell pkg-config --cflags libisal 2>/dev/null)
PKG_LIBS   := $(shell pkg-config --libs libisal 2>/dev/null)

# Allow manual override:
#   make ISAL_INC=/path/include ISAL_LIB=/path/lib
ISAL_INC ?=
ISAL_LIB ?=

INCFLAGS :=
LIBFLAGS :=

ifneq ($(strip $(PKG_CFLAGS)),)
  INCFLAGS += $(PKG_CFLAGS)
endif
ifneq ($(strip $(PKG_LIBS)),)
  LIBFLAGS += $(PKG_LIBS)
endif

ifneq ($(strip $(ISAL_INC)),)
  INCFLAGS += -I$(ISAL_INC)
endif
ifneq ($(strip $(ISAL_LIB)),)
  LIBFLAGS += -L$(ISAL_LIB) -lisal
endif

# Fallback if pkg-config not found and no overrides: try -lisal
ifeq ($(strip $(LIBFLAGS)),)
  LIBFLAGS := -lisal
endif

all: $(TARGET)

$(TARGET): main.c
	mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $(INCFLAGS) -o $@ $< $(LDFLAGS) $(LIBFLAGS)

clean:
	rm -f $(TARGET)
