CC = clang
CFLAGS = -O3 -Wall -Wextra -fPIC -Iinclude
TARGET = libtriage.so
SRCS = src/triage_engine.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -shared -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all clean
