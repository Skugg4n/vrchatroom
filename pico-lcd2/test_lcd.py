# Enkelt skärmtest för Waveshare Pico-LCD-2.
# Kör med F5 i Thonny. Skärmen ska växla mellan röd, grön, blå och vit
# och texten i Thonny-skalet visar hur långt programmet kommer.

from machine import Pin, SPI
import time

print("1. Startar")
bl = Pin(13, Pin.OUT, value=1)          # bakgrundsljus på
cs = Pin(9, Pin.OUT, value=1)
dc = Pin(8, Pin.OUT, value=1)
rst = Pin(12, Pin.OUT, value=1)
spi = SPI(1, baudrate=20_000_000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11))
print("2. Pinnar och SPI OK")


def cmd(c, data=b""):
    cs(0)
    dc(0)
    spi.write(bytes([c]))
    if data:
        dc(1)
        spi.write(bytes(data))
    cs(1)


rst(0)
time.sleep_ms(20)
rst(1)
time.sleep_ms(120)
cmd(0x11)                    # vakna
time.sleep_ms(120)
cmd(0x36, [0x70])            # liggande
cmd(0x3A, [0x05])            # 16 bitar/pixel
cmd(0x21)                    # inverterade färger
cmd(0x29)                    # skärm på
print("3. Skärmen initierad")

row = bytearray(320 * 2)


def fill(color):
    for i in range(0, len(row), 2):
        row[i] = color >> 8
        row[i + 1] = color & 0xFF
    cmd(0x2A, [0, 0, 0x01, 0x3F])
    cmd(0x2B, [0, 0, 0, 0xEF])
    cmd(0x2C)
    cs(0)
    dc(1)
    for _ in range(240):
        spi.write(row)
    cs(1)


colors = (("ROD", 0xF800), ("GRON", 0x07E0), ("BLA", 0x001F), ("VIT", 0xFFFF))
print("4. Fyller skärmen, tryck Stopp för att avsluta")
while True:
    for name, c in colors:
        print("   ", name)
        fill(c)
        time.sleep(1)
