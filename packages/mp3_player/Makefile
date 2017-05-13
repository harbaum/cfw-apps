ifndef FTC_BUILDROOT
$(error "FTC_BUILDROOT not set. Please point it to the ftcommunity-TXT directory")
endif

ARM_CC=$(FTC_BUILDROOT)/output/host/usr/bin/arm-linux-gnueabihf-gcc

SRC = txt_snd_cat.c
CFLAGS = -O2
BIN = txt_snd_cat

all: $(BIN)

$(BIN): $(SRC)
	$(ARM_CC) $(CFLAGS) $(SRC) -o $@

clean:
	rm -rf *~ cache
