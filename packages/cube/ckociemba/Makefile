ifndef FTC_BUILDROOT
$(error "FTC_BUILDROOT not set. Please point it to the ftcommunity-TXT directory")
endif

ARM_CC=$(FTC_BUILDROOT)/output/host/usr/bin/arm-linux-gnueabihf-gcc

CKOCIEMBA_SRC = coordcube.c cubiecube.c facecube.c search.c
CKOCIEMBA_INCLUDE = include
CFLAGS = -std=c99 -O3
BINDIR = ..
BIN = kociemba
ARM = armv7l

all: $(BINDIR)/$(BIN) $(BINDIR)/$(BIN)-$(ARM)

$(BINDIR)/$(BIN): solve.c $(CKOCIEMBA_SRC)
	$(CC) $(CFLAGS) $(CKOCIEMBA_SRC) -I$(CKOCIEMBA_INCLUDE) solve.c -o $@

$(BINDIR)/$(BIN)-$(ARM): solve.c $(CKOCIEMBA_SRC)
	$(ARM_CC) $(CFLAGS) $(CKOCIEMBA_SRC) -I$(CKOCIEMBA_INCLUDE) solve.c -o $@

clean:
	rm -rf *~ cache
