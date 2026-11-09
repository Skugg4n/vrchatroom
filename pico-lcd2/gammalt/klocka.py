# Pico Klocka
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# En minimalistisk klocka. Spara som klocka.py på Picon.
# För att den ska starta av sig själv när Picon får ström, lägg en
# main.py på Picon med raden: import klocka
#
# Tiden: När Picon är inkopplad till datorn med Thonny ställs klockan
# automatiskt (då visas även datum). Startar Picon utan dator frågar
# den efter tiden:
#   KEY0 = timme +1, KEY1 = minut +1 (håll inne för att gå fort).
#   Rör inga knappar på 5 sekunder så sparas tiden.
# Håll in KEY0 och KEY1 i 3 sekunder för att ställa om tiden eller gå
# tillbaka till startmenyn (main.py).
#
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö.

import machine
from machine import Pin, SPI, PWM
import framebuf
import time

W, H = 320, 240


try:
    import delat           # skapas av startmenyn (main.py)
except ImportError:
    delat = None


def shared_fb():
    """Skärmbilden som startmenyn (main.py) har skapat, annars en egen."""
    fb = delat.FB if delat else None
    return fb if fb is not None else bytearray(W * H * 2)


def leave(next_prog=None):
    """Avsluta utan omstart. Startmenyn tar bort koden ur minnet och
    startar next_prog (eller visar menyn)."""
    if delat:
        delat.NEXT = next_prog
    raise SystemExit
FRAME_MS = 100                # 10 bilder per sekund räcker gott
NIGHT = (22, 7)               # nattläge mellan 22 och 07
DAY_LIGHT, NIGHT_LIGHT = 70, 12

DAYS = ("MANDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG", "LORDAG", "SONDAG")
MONTHS = ("JANUARI", "FEBRUARI", "MARS", "APRIL", "MAJ", "JUNI", "JULI",
          "AUGUSTI", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DECEMBER")


def rgb(r, g, b):
    """RGB888 -> RGB565 med bytebyte (skärmen vill ha big endian)."""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


BG = rgb(6, 6, 10)
WHITE = rgb(255, 255, 255)
GHOST = rgb(18, 18, 26)          # släckta segment, syns knappt
HAIR = rgb(40, 40, 52)           # tunna linjer
TEXT = rgb(120, 120, 140)        # datum och hjälptext

# Färgtema efter tid på dygnet: (siffror, accent)
THEMES = (
    (0, rgb(150, 40, 30), rgb(110, 30, 25)),       # natt: dovt rött
    (7, rgb(255, 236, 210), rgb(255, 170, 60)),    # morgon: varmt
    (10, rgb(235, 240, 250), rgb(80, 200, 255)),   # dag: kallt vitt
    (18, rgb(255, 228, 200), rgb(255, 120, 60)),   # kväll: orange
    (22, rgb(150, 40, 30), rgb(110, 30, 25)),      # natt igen
)


def theme(hour):
    fg, acc = THEMES[0][1], THEMES[0][2]
    for start, f, a in THEMES:
        if hour >= start:
            fg, acc = f, a
    return fg, acc


# ---------------------------------------------------------------
# Skärmdrivrutin
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = shared_fb()
        super().__init__(self.buffer, W, H, framebuf.RGB565)
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=62_500_000, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.backlight(0)
        self._init_display()

    def backlight(self, percent):
        self.bl.duty_u16(int(max(0, min(100, percent)) * 655.35))

    def cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def _init_display(self):
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(120)
        self.cmd(0x36, [0x70])                     # liggande
        self.cmd(0x3A, [0x05])
        self.cmd(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])
        self.cmd(0xB7, [0x35])
        self.cmd(0xBB, [0x19])
        self.cmd(0xC0, [0x2C])
        self.cmd(0xC2, [0x01])
        self.cmd(0xC3, [0x12])
        self.cmd(0xC4, [0x20])
        self.cmd(0xC6, [0x0F])
        self.cmd(0xD0, [0xA4, 0xA1])
        self.cmd(0xE0, [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F,
                        0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23])
        self.cmd(0xE1, [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F,
                        0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23])
        self.cmd(0x21)
        self.cmd(0x11)
        time.sleep_ms(120)
        self.cmd(0x29)
        self.cmd(0x2A, [0x00, 0x00, (W - 1) >> 8, (W - 1) & 0xFF])
        self.cmd(0x2B, [0x00, 0x00, (H - 1) >> 8, (H - 1) & 0xFF])

    def show(self):
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


# ---------------------------------------------------------------
# Siffror med rundade segment (egen "typsnitt")
# ---------------------------------------------------------------
DW, DH, ST, GAP = 50, 100, 9, 3      # siffrans bredd, höjd, strecktjocklek, glapp
#            a  b  c  d  e  f  g
DIGITS = {
    "0": (1, 1, 1, 1, 1, 1, 0), "1": (0, 1, 1, 0, 0, 0, 0),
    "2": (1, 1, 0, 1, 1, 0, 1), "3": (1, 1, 1, 1, 0, 0, 1),
    "4": (0, 1, 1, 0, 0, 1, 1), "5": (1, 0, 1, 1, 0, 1, 1),
    "6": (1, 0, 1, 1, 1, 1, 1), "7": (1, 1, 1, 0, 0, 0, 0),
    "8": (1, 1, 1, 1, 1, 1, 1), "9": (1, 1, 1, 1, 0, 1, 1),
}


def pill_h(fb, x1, x2, y, c):
    """Vågrätt streck med runda ändar, centrerat på y."""
    r = ST // 2
    fb.fill_rect(x1, y - r, x2 - x1 + 1, ST, c)
    fb.ellipse(x1, y, r, r, c, True)
    fb.ellipse(x2, y, r, r, c, True)


def pill_v(fb, x, y1, y2, c):
    """Lodrätt streck med runda ändar, centrerat på x."""
    r = ST // 2
    fb.fill_rect(x - r, y1, ST, y2 - y1 + 1, c)
    fb.ellipse(x, y1, r, r, c, True)
    fb.ellipse(x, y2, r, r, c, True)


def draw_digit(fb, ch, x, y, on_col, off_col=GHOST):
    seg = DIGITS.get(ch, (0,) * 7)
    r = ST // 2
    left, right = x + r, x + DW - r
    top, mid, bot = y + r, y + DH // 2, y + DH - r
    pad = r + GAP + 1
    parts = (
        (pill_h, left + pad, right - pad, top),          # a
        (pill_v, right, top + pad, mid - pad),           # b
        (pill_v, right, mid + pad, bot - pad),           # c
        (pill_h, left + pad, right - pad, bot),          # d
        (pill_v, left, mid + pad, bot - pad),            # e
        (pill_v, left, top + pad, mid - pad),            # f
        (pill_h, left + pad, right - pad, mid),          # g
    )
    # Släckta segment först, sedan de tända ovanpå
    for i, (fn, p1, p2, p3) in enumerate(parts):
        if not seg[i] and off_col is not None:
            fn(fb, p1, p2, p3, off_col)
    for i, (fn, p1, p2, p3) in enumerate(parts):
        if seg[i]:
            fn(fb, p1, p2, p3, on_col)


DIGIT_STEP = DW + 14
COLON_W = 26
TIME_W = 4 * DW + 2 * 14 + COLON_W + 2 * 10


def draw_time(fb, hh, mm, y, col, colon_col, hour_col=None, min_col=None):
    x = (W - TIME_W) // 2
    txt = "%02d%02d" % (hh, mm)
    for i, ch in enumerate(txt):
        c = col
        if i < 2 and hour_col is not None:
            c = hour_col
        if i >= 2 and min_col is not None:
            c = min_col
        draw_digit(fb, ch, x, y, c)
        x += DIGIT_STEP if i != 1 else DW
        if i == 1:
            cx = x + 10 + COLON_W // 2
            r = ST // 2 + 1
            fb.ellipse(cx, y + DH // 3, r, r, colon_col, True)
            fb.ellipse(cx, y + 2 * DH // 3, r, r, colon_col, True)
            x += COLON_W + 20


def spaced(fb, s, y, c, gap=3):
    """Liten text med luft mellan bokstäverna, centrerad."""
    w = len(s) * (8 + gap) - gap
    x = (W - w) // 2
    for ch in s:
        fb.text(ch, x, y, c)
        x += 8 + gap


def dim(c565, f):
    """Gör en färg mörkare (f = 0..1)."""
    c = ((c565 & 0xFF) << 8) | (c565 >> 8)
    r = ((c >> 11) & 31) * f
    g = ((c >> 5) & 63) * f
    b = (c & 31) * f
    c = (int(r) << 11) | (int(g) << 5) | int(b)
    return ((c & 0xFF) << 8) | (c >> 8)


# ---------------------------------------------------------------
# Knappar (används bara när tiden ställs in)
# ---------------------------------------------------------------
k0 = Pin(15, Pin.IN, Pin.PULL_UP)
k1 = Pin(17, Pin.IN, Pin.PULL_UP)
rtc = machine.RTC()
TIME_Y = 46


def wait(t0):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < FRAME_MS:
        time.sleep_ms(FRAME_MS - used)


def set_time(lcd, h, m):
    """KEY0 = timme +1, KEY1 = minut +1. Sparas efter 5 s utan tryck."""
    held = [0, 0]
    idle = 0
    t = 0
    lcd.backlight(DAY_LIGHT)
    while k0.value() == 0 or k1.value() == 0:      # vänta tills knapparna släpps
        time.sleep_ms(20)
    while idle < 50:                               # 50 x 100 ms = 5 s
        t0 = time.ticks_ms()
        for i, pin in enumerate((k0, k1)):
            if pin.value() == 0:
                held[i] += 1
                idle = 0
                if held[i] == 1 or held[i] > 5:    # ett steg, sedan fort
                    if i == 0:
                        h = (h + 1) % 24
                    else:
                        m = (m + 1) % 60
            else:
                held[i] = 0
        if held == [0, 0]:
            idle += 1
        fg, acc = theme(10)
        blink = (t // 4) % 2 == 0
        lcd.fill(BG)
        spaced(lcd, "STALL IN TIDEN", 18, TEXT)
        draw_time(lcd, h, m, TIME_Y, fg, fg,
                  hour_col=acc if held[0] or blink else fg,
                  min_col=acc if held[1] or blink else fg)
        spaced(lcd, "KEY0  TIMME        KEY1  MINUT", 172, TEXT, 1)
        # tunn linje som krymper tills tiden sparas
        lcd.hline(60, 200, 200, HAIR)
        lcd.hline(60, 200, 200 - idle * 4, acc)
        spaced(lcd, "SPARAS AV SIG SJALV", 212, dim(TEXT, 0.6), 2)
        lcd.show()
        t += 1
        wait(t0)
    # År 2000 betyder: klockslaget är känt men inte datumet
    rtc.datetime((2000, 1, 1, 5, h, m, 0, 0))


def choose_action(lcd):
    """0 = ställ in tiden (True), 1 = tillbaka till startmenyn.
    Inget val på 5 s = tillbaka till klockan (False)."""
    lcd.backlight(DAY_LIGHT)
    while k0.value() == 0 or k1.value() == 0:
        time.sleep_ms(20)
    _, acc = theme(10)
    for i in range(50):
        if k0.value() == 0:
            return True
        if k1.value() == 0:
            leave()                              # tillbaka till startmenyn
        lcd.fill(BG)
        spaced(lcd, "VAD VILL DU GORA?", 50, TEXT)
        spaced(lcd, "KEY0   STALL IN TIDEN", 100, WHITE, 2)
        spaced(lcd, "KEY1   TILL MENYN", 124, WHITE, 2)
        lcd.hline(60, 170, 200, HAIR)
        lcd.hline(60, 170, 200 - i * 4, acc)
        spaced(lcd, "ANNARS TILLBAKA TILL KLOCKAN", 184, dim(TEXT, 0.6), 1)
        lcd.show()
        time.sleep_ms(100)
    return False


def clock_loop(lcd):
    both = 0
    light = None
    last_s = -1
    s_start = time.ticks_ms()
    while True:
        t0 = time.ticks_ms()
        d = rtc.datetime()
        year, month, day, wd, hh, mm, ss = d[0], d[1], d[2], d[3], d[4], d[5], d[6]
        if ss != last_s:
            last_s = ss
            s_start = t0
        frac = min(1.0, time.ticks_diff(t0, s_start) / 1000)

        night = hh >= NIGHT[0] or hh < NIGHT[1]
        want = NIGHT_LIGHT if night else DAY_LIGHT
        if want != light:
            lcd.backlight(want)
            light = want

        # Håll in båda knapparna i 3 s: ställ in tiden eller gå till menyn
        if k0.value() == 0 and k1.value() == 0:
            both += 1
            if both > 30:
                if choose_action(lcd):
                    set_time(lcd, hh, mm)
                both = 0
                light = None
                continue
        else:
            both = 0

        fg, acc = theme(hh)
        lcd.fill(BG)
        # Kolon som andas: ljust i början av sekunden, tonar ner
        draw_time(lcd, hh, mm, TIME_Y, fg, dim(fg, 1.0 - 0.75 * frac))

        # Sekunder: en tunn linje med en prick som vandrar
        x0, x1 = 70, 250
        lcd.hline(x0, 166, x1 - x0, HAIR)
        px = x0 + int((x1 - x0) * (ss + frac) / 60)
        lcd.hline(x0, 166, px - x0, dim(acc, 0.55))
        lcd.ellipse(px, 166, 3, 3, acc, True)

        if year >= 2024:                           # datumet är känt
            spaced(lcd, DAYS[wd % 7], 186, fg if not night else dim(fg, 0.7))
            spaced(lcd, "%d %s %d" % (day, MONTHS[(month - 1) % 12], year), 204, TEXT, 2)
        lcd.show()
        wait(t0)


def main():
    lcd = LCD()
    d = rtc.datetime()
    if d[0] < 2024 and d[0] != 2000:
        # Picon har startat utan dator och vet inte vad klockan är
        lcd.backlight(DAY_LIGHT)
        set_time(lcd, 12, 0)
    clock_loop(lcd)


main()
