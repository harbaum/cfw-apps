## RFID - MFRC522 I²C MIFARE reader demo

This app uses a
[MFRC522](https://www.nxp.com/documents/data_sheet/MFMFRC522.pdf) chip to
access MIFARE chip cards.

# I²C bus

The MFRC522 can optionally use a SPI, I²C or UART to interface to a
host. Most cheap MFRC522 based boards are setup for SPI connection.
For this setup a I²C configured board is needed. A search for
"rc522 i2c" on e.g. EBay will show appropriate results.

But since the rc522 I²C requires I²C clock stretching support on host
side but neither the TXT nor the Raspberry Pi support this on their
native I²C interfaces. Thus a
[i2c-tiny-usb](http://www.harbaum.org/till/i2c_tiny_usb/index.shtml)
is being used. The i2c-tiny-usb comes with a kernel driver and its I²C
bus is transparently mapped into the Linux system. For the software it
thus doesn't make any difference whether the i2c-tiny-usb or any other
I²C bus is being used. The app scans all available I²C busses and
should be able to work with any connection. Only the i2c-tiny-usb has
been tested.

# Hardware setup

The current setup consists of a
[digipark](http://digistump.com/products/1) running the [i2c-tiny-usb
firmware](https://github.com/harbaum/I2C-Tiny-USB/tree/master/digispark).
The following connections have to be made from the digispark to the
MFRC522 board:

From digispark | to MFRC522
--- | --- | ---
5V | via two 1N4148 diodes to 3.3V
GND | GND
P0 | SDA
P2 | SCL

The two diodes drop about 0.7V each and convert the 5V to ~3.6V which
seems to be ok for the MFRC522. If you want to be 100% sure you might
install a 5V to 3.3V regulator instead.

On MFRC522 side three 10k pullup resistors must each be mounted
between SDA and 3.3V, between SCL and 3.3V and RST and 3.3V.

# Hardware test on a Linux PC

When connected to a Linux PC after a few seconds the digispark will
first show up with its bootloader under vendor 16d0 and product 0753
and a few seconds later it should be re-detected as a i2c-tiny-usb
device and the kernel should load the appropriate driver.

```
[23538.950950] usb 3-1: new low-speed USB device number 12 using xhci_hcd
[23539.094974] usb 3-1: New USB device found, idVendor=16d0, idProduct=0753
[23539.094978] usb 3-1: New USB device strings: Mfr=0, Product=0, SerialNumber=0
[23543.934521] usb 3-1: USB disconnect, device number 12
[23544.495026] usb 3-1: new low-speed USB device number 13 using xhci_hcd
[23544.642628] usb 3-1: New USB device found, idVendor=0403, idProduct=c631
[23544.642633] usb 3-1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[23544.642636] usb 3-1: Product: i2c-tiny-usb
[23544.642637] usb 3-1: Manufacturer: harbaum.org
[23544.642639] usb 3-1: SerialNumber: 113
[23544.643267] i2c-tiny-usb 3-1:1.0: version 2.01 found at bus 003 address 013
[23544.644333] i2c i2c-9: connected i2c-tiny-usb device
```

In this case the i2c-tiny-usb is detected as i2c bus 9
(i2c-9). Running ```i2cdetect``` on this should result in the MFRC522 to show
up under address 0x28:

```
$ i2cdetect 9
WARNING! This program can confuse your I2C bus, cause data loss and worse!
I will probe file /dev/i2c-9.
I will probe address range 0x03-0x77.
Continue? [Y/n] 
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- 28 -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --                         
```

Congratulations, the hardware seems to be working and you can connect it
to the TXT or a Raspberry Pi running the community firmware.
