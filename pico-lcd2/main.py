# PICO MENY - startmeny som körs när Picon får ström.
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Välj vad du vill köra:
#   0 / 1           = bläddra
#   2 eller 0+1     = starta
# När Picon just har startat och du inte rör något på 10 sekunder
# startar det du valde senast.
#
# Programmen byts utan omstart: skärmbilden (150 kB) skapas en gång här,
# och när ett program avslutas tas dess kod bort ur minnet innan nästa
# laddas. Ett program avslutas med raise SystemExit, och kan be om att
# ett annat program ska startas efteråt via builtins.PICO_NEXT.
#
# Filerna klocka.py, labyrint.py, hoppa.py, main2.py och nyaspel.py måste
# ligga på Picon bredvid den här filen.
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö.

import gc
gc.collect()
import builtins
W, H = 320, 240
# Skärmbilden skapas allra först, medan minnet är tomt, och delas sedan av
# alla program. Då blir minnet aldrig för uppstyckat för att få plats.
builtins.PICO_FB = bytearray(W * H * 2)
builtins.PICO_NEXT = None

from machine import Pin, SPI, PWM
import framebuf
import time
import json
import sys

AUTO_MS = 10_000
CHOICE_FILE = "meny.json"

# (visningsnamn, beskrivning, fil utan .py, färg)
PROGRAMS = (
    ("KLOCKA", "En snygg klocka", "klocka", (90, 200, 255)),
    ("LABYRINT 3D", "Hitta ut ur labyrinten", "labyrint", (190, 80, 255)),
    ("HOPPA!", "Plattformsspel, 10 banor", "hoppa", (255, 200, 40)),
    ("PICO ARCADE", "Pong, Snake, Tetris m.fl.", "main2", (80, 230, 110)),
    ("NYA SPEL", "Meteorer, Turbo, Golf m.fl.", "nyaspel", (255, 90, 200)),
)


def rgb(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


BG = rgb(6, 6, 12)
WHITE = rgb(255, 255, 255)
TEXT = rgb(130, 130, 150)
DIMC = rgb(40, 40, 55)
ROW = rgb(16, 16, 26)


class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = builtins.PICO_FB
        super().__init__(self.buffer, W, H, framebuf.RGB565)
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=62_500_000, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(50000)
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(120)
        for c, d in ((0x36, [0x70]), (0x3A, [0x05]), (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33]),
                     (0xB7, [0x35]), (0xBB, [0x19]), (0xC0, [0x2C]), (0xC2, [0x01]),
                     (0xC3, [0x12]), (0xC4, [0x20]), (0xC6, [0x0F]), (0xD0, [0xA4, 0xA1]),
                     (0xE0, [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]),
                     (0xE1, [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23])):
            self.cmd(c, d)
        self.cmd(0x21)
        self.cmd(0x11)
        time.sleep_ms(120)
        self.cmd(0x29)
        self.cmd(0x2A, [0, 0, (W - 1) >> 8, (W - 1) & 0xFF])
        self.cmd(0x2B, [0, 0, (H - 1) >> 8, (H - 1) & 0xFF])

    def cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def show(self):
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


_glyph = bytearray(8)
_gfb = framebuf.FrameBuffer(_glyph, 8, 8, framebuf.MONO_HLSB)


def big_text(fb, s, x, y, c, scale):
    for ch in s:
        _gfb.fill(0)
        _gfb.text(ch, 0, 0, 1)
        for row in range(8):
            bits = _glyph[row]
            for col in range(8):
                if bits & (0x80 >> col):
                    fb.fill_rect(x + col * scale, y + row * scale, scale, scale, c)
        x += 8 * scale


def spaced(fb, s, x, y, c, gap=2):
    for ch in s:
        fb.text(ch, x, y, c)
        x += 8 + gap


def menu(auto):
    """Visar menyn och returnerar filnamnet som ska startas.
    auto = starta det senast valda av sig själv efter 10 s."""
    try:
        with open(CHOICE_FILE) as f:
            sel = json.load(f).get("sel", 0) % len(PROGRAMS)
    except Exception:
        sel = 0
    lcd = LCD()
    k0 = Pin(15, Pin.IN, Pin.PULL_UP)
    k1 = Pin(17, Pin.IN, Pin.PULL_UP)
    k2 = Pin(2, Pin.IN, Pin.PULL_UP)
    k3 = Pin(3, Pin.IN, Pin.PULL_UP)
    # Vänta tills alla knappar är släppta (man kan komma hit med knappar nere)
    lcd.fill(BG)
    lcd.show()
    while not (k0.value() and k1.value() and k2.value() and k3.value()):
        time.sleep_ms(20)
    time.sleep_ms(60)
    prev = (False, False)
    cnt = [0, 0]
    both = 0
    chorded = False
    last = time.ticks_ms()
    t = 0
    while True:
        t0 = time.ticks_ms()
        now = (k0.value() == 0, k1.value() == 0)
        start = False
        if now[0] or now[1]:
            last = t0
        if k2.value() == 0:                      # KEY2 startar också
            start = True
        b = now[0] and now[1]
        if b:
            chorded = True
            both += 1
        else:
            if both > 0:
                start = True                     # 0+1 släpptes
            both = 0
        for i in (0, 1):
            if prev[i] and not now[i] and not chorded and cnt[i] <= 8:
                sel = (sel + (1 if i else -1)) % len(PROGRAMS)
            cnt[i] = cnt[i] + 1 if now[i] else 0
        if not now[0] and not now[1]:
            chorded = False
        prev = now
        left = AUTO_MS - time.ticks_diff(t0, last)
        if auto and left <= 0:
            start = True

        # --- Rita ---
        lcd.fill(BG)
        big_text(lcd, "PICO", 18, 14, WHITE, 4)
        spaced(lcd, "VAD VILL DU GORA?", 160, 30, TEXT, 1)
        for i, (name, desc, _, col) in enumerate(PROGRAMS):
            y = 54 + i * 31
            c = rgb(*col)
            on = i == sel
            lcd.fill_rect(14, y, W - 28, 29, ROW if on else BG)
            lcd.fill_rect(14, y, 4, 29, c if on else DIMC)
            lcd.ellipse(36, y + 14, 6, 6, c if on else DIMC, True)
            if on:
                big_text(lcd, name, 52, y + 2, WHITE, 2)
                lcd.text(desc, 52, y + 19, TEXT)
            else:
                spaced(lcd, name, 52, y + 7, TEXT, 2)
        # Linje som visar när det valda startar av sig själv
        c = rgb(*PROGRAMS[sel][3])
        if auto:
            frac = max(0, left) / AUTO_MS
            lcd.hline(14, 214, W - 28, DIMC)
            lcd.hline(14, 214, int((W - 28) * frac), c)
            lcd.text("%2d" % (max(0, left) // 1000 + 1), W - 30, 224, c)
        lcd.text("0/1 bladdra  2 eller 0+1 start", 14, 224, TEXT)
        lcd.show()
        if start:
            break
        t += 1
        used = time.ticks_diff(time.ticks_ms(), t0)
        if used < 50:
            time.sleep_ms(50 - used)
    try:
        with open(CHOICE_FILE, "w") as f:
            json.dump({"sel": sel}, f)
    except Exception:
        pass
    lcd.fill(BG)
    spaced(lcd, "STARTAR " + PROGRAMS[sel][0] + "...", 20, 112, WHITE, 2)
    lcd.show()
    return PROGRAMS[sel][2]


def show_error(e):
    """Visar ett fel på skärmen och väntar på en knapp."""
    import io
    sys.print_exception(e)
    buf = io.StringIO()
    sys.print_exception(e, buf)
    lcd = LCD()
    lcd.fill(rgb(120, 0, 0))
    lcd.text("FEL! Tryck pa en knapp", 4, 4, WHITE)
    y = 20
    for line in buf.getvalue().split("\n"):
        while line and y < H - 8:
            lcd.text(line[:39], 4, y, WHITE)
            line = line[39:]
            y += 10
    lcd.show()
    pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in (15, 17, 2, 3)]
    time.sleep_ms(500)
    while all(p.value() for p in pins):
        time.sleep_ms(20)
    while not all(p.value() for p in pins):
        time.sleep_ms(20)


BASE = list(sys.modules)


def run(name):
    """Kör ett program. När det är klart tas dess kod bort ur minnet."""
    gc.collect()
    try:
        __import__(name)
    except SystemExit:
        pass
    except Exception as e:
        show_error(e)
    finally:
        for m in list(sys.modules):
            if m not in BASE:
                del sys.modules[m]
        gc.collect()


first = True
while True:
    nxt = builtins.PICO_NEXT
    builtins.PICO_NEXT = None
    if not nxt:
        nxt = menu(first)
    first = False
    run(nxt)
