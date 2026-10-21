.PHONY: all clean

all:
	cd isal_rs_c && $(MAKE)
	cd go_wrap && go build -o ../bin/rswrap .

clean:
	rm -rf bin out
	cd isal_rs_c && $(MAKE) clean
