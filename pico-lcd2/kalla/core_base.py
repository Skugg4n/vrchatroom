# PICO SPEL - massor av spel i en enda fil
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Spara filen som main.py på Picon så startar den av sig själv.
#
# Spelens kod ligger längst ner i filen som kommentarer (rader som börjar
# med #|). Bara det spel du väljer läses in i minnet, och det tas bort
# igen när du går tillbaka till menyn. Därför får många spel plats.
# Filen byggs från mappen kalla/ med build.py, ändra helst där.
#
# Knapparna sitter så här:
#     KEY0 (uppe vänster)    KEY1 (uppe höger)
#     KEY3 (nere vänster)    KEY2 (nere höger)
#
# I menyn: 0/1 väljer spel, 2 startar.
# I alla spel: håll in alla fyra knapparna = paus (fortsätt eller till menyn).
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö.

import gc
# Kör man filen flera gånger med F5 i Thonny ligger förra körningens saker
# kvar i minnet. Ta bort dem först, så att skärmbilden säkert får plats.
for _n in list(globals()):
    if _n[0] != "_" and _n != "gc":
        del globals()[_n]
gc.collect()

W, H = 320, 240
FB = bytearray(W * H * 2)          # skärmbilden skapas allra först

import machine
from machine import Pin, SPI, PWM
import framebuf
import time
import random
import math
import json

try:
    import micropython
    native = micropython.native
except (ImportError, AttributeError):
    def native(f):
        return f

try:
    machine.freq(250_000_000)      # lite snabbare
except Exception:
    pass


# ---------------------------------------------------------------
# Färger
# ---------------------------------------------------------------
def rgb(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def mix(a, b, t):
    return rgb(*lerp(a, b, t))


C_BG = (12, 12, 30)
BLACK = rgb(0, 0, 0)
WHITE = rgb(255, 255, 255)
BG = rgb(*C_BG)
PANEL = rgb(26, 26, 54)
LINE = rgb(48, 48, 92)
DIM = rgb(80, 80, 125)
GRAY = rgb(160, 160, 195)
CORAL = rgb(255, 95, 100)
AMBER = rgb(255, 190, 60)
LIME = rgb(125, 230, 110)
TEAL = rgb(40, 215, 200)
SKY = rgb(80, 165, 255)
VIOLET = rgb(170, 110, 255)
PINK = rgb(255, 110, 200)
YELLOW = rgb(255, 230, 70)
SHADOW = rgb(30, 10, 60)
NIGHT = [mix((14, 14, 40), (40, 14, 60), y / (H - 1)) for y in range(H)]
STAR_C = (rgb(70, 70, 120), rgb(140, 140, 200), rgb(255, 255, 255))
CONFETTI = (CORAL, AMBER, LIME, TEAL, SKY, VIOLET, PINK)


# ---------------------------------------------------------------
# Skärm
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        super().__init__(FB, W, H, framebuf.RGB565)
        self.buffer = FB
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=75_000_000, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(65535)
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
        if TOAST[1] > 0:                     # "UTMANING KLAR!" ovanpå spelet
            TOAST[1] -= 1
            y = 4 if TOAST[1] > 4 else 4 - (4 - TOAST[1]) * 6
            self.fill_rect(30, y, 260, 30, rgb(30, 22, 6))
            self.rect(30, y, 260, 30, YELLOW)
            star(self, 46, y + 15, 9, YELLOW)
            self.text("UTMANING KLAR!", 62, y + 5, YELLOW)
            self.text(TOAST[0][:26], 62, y + 17, WHITE)
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


# ---------------------------------------------------------------
# Knappar
# ---------------------------------------------------------------
K0, K1, K2, K3 = 0, 1, 2, 3
TOAST = ["", 0]


class Keys:
    def __init__(self):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in (15, 17, 2, 3)]
        self.now = [False] * 4
        self.prev = [False] * 4
        self.cnt = [0] * 4
        self.all_cnt = 0

    def update(self):
        self.prev = self.now
        self.now = [p.value() == 0 for p in self.pins]
        for i in range(4):
            self.cnt[i] = self.cnt[i] + 1 if self.now[i] else 0
        self.all_cnt = self.all_cnt + 1 if all(self.now) else 0

    def held(self, k):
        return self.now[k]

    def pressed(self, k):
        return self.now[k] and not self.prev[k] and sum(self.now) < 3

    def repeat(self, k, delay=9, rate=3):
        c = self.cnt[k]
        return (c == 1 or (c > delay and (c - delay) % rate == 0)) and sum(self.now) < 3

    def pause(self):
        """Alla fyra knapparna nere en kort stund."""
        return self.all_cnt >= 6

    def wait_release(self):
        self.update()
        n = 0
        while any(self.now) and n < 200:
            time.sleep_ms(10)
            self.update()
            n += 1
        self.update()


# ---------------------------------------------------------------
# Text
# ---------------------------------------------------------------
_glyph = bytearray(8)
_gfb = framebuf.FrameBuffer(_glyph, 8, 8, framebuf.MONO_HLSB)
_RUNS = {}


def _runs(ch):
    r = _RUNS.get(ch)
    if r is None:
        _gfb.fill(0)
        _gfb.text(ch, 0, 0, 1)
        out = []
        for row in range(8):
            bits = _glyph[row]
            col = 0
            while col < 8:
                if bits & (0x80 >> col):
                    s = col
                    while col < 8 and bits & (0x80 >> col):
                        col += 1
                    out.append((s, row, col - s))
                else:
                    col += 1
        r = tuple(out)
        _RUNS[ch] = r
    return r


@native
def big(fb, s, x, y, c, scale=2):
    """Text i valfri storlek."""
    if scale == 1:
        fb.text(s, x, y, c)
        return
    for ch in s:
        for run in _runs(ch):
            fb.fill_rect(x + run[0] * scale, y + run[1] * scale, run[2] * scale, scale, c)
        x += 8 * scale


def ctext(fb, s, y, c, scale=1, cx=W // 2):
    big(fb, s, cx - len(s) * 4 * scale, y, c, scale)


def stext(fb, s, y, c, scale=2, cx=W // 2):
    ctext(fb, s, y + max(1, scale), SHADOW, scale, cx)
    ctext(fb, s, y, c, scale, cx)


def rtext(fb, s, x, y, c, scale=1):
    """Högerjusterad text som slutar vid x."""
    big(fb, s, x - len(s) * 8 * scale, y, c, scale)


# ---------------------------------------------------------------
# Hjälp för bilder och effekter
# ---------------------------------------------------------------
@native
def gradient(fb, cols, y0=0, y1=H):
    for y in range(y0, y1):
        fb.hline(0, y, W, cols[y])


def tri(fb, x0, y0, x1, y1, x2, y2, c):
    """Fylld triangel."""
    if y0 > y1:
        x0, y0, x1, y1 = x1, y1, x0, y0
    if y1 > y2:
        x1, y1, x2, y2 = x2, y2, x1, y1
    if y0 > y1:
        x0, y0, x1, y1 = x1, y1, x0, y0
    for y in range(int(y0), int(y2) + 1):
        if y2 != y0:
            xa = x0 + (x2 - x0) * (y - y0) / (y2 - y0)
        else:
            xa = x0
        if y < y1:
            xb = x0 + (x1 - x0) * (y - y0) / (y1 - y0) if y1 != y0 else x1
        else:
            xb = x1 + (x2 - x1) * (y - y1) / (y2 - y1) if y2 != y1 else x2
        if xa > xb:
            xa, xb = xb, xa
        fb.hline(int(xa), y, int(xb - xa) + 1, c)


def arrow(fb, x, y, d, c, s=5):
    """Liten pil: d = 0 upp, 1 höger, 2 ner, 3 vänster."""
    if d == 0:
        tri(fb, x, y - s, x - s, y + s, x + s, y + s, c)
    elif d == 1:
        tri(fb, x + s, y, x - s, y - s, x - s, y + s, c)
    elif d == 2:
        tri(fb, x, y + s, x - s, y - s, x + s, y - s, c)
    else:
        tri(fb, x - s, y, x + s, y - s, x + s, y + s, c)


def shuffled(n):
    a = list(range(n))
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


class Stars:
    def __init__(self, n=40):
        self.s = [[random.randint(0, W - 1), random.randint(0, H - 1), random.randint(1, 3)]
                  for _ in range(n)]

    @native
    def draw(self, fb, dx=0.0, dy=0.5):
        for s in self.s:
            s[0] += dx * s[2]
            s[1] += dy * s[2]
            if s[1] >= H:
                s[1] -= H
                s[0] = random.randint(0, W - 1)
            if s[0] < 0:
                s[0] += W
            elif s[0] >= W:
                s[0] -= W
            fb.pixel(int(s[0]), int(s[1]), STAR_C[s[2] - 1])


class Particles:
    def __init__(self, cap=140):
        self.p = []
        self.cap = cap

    def burst(self, x, y, col, n=12, speed=3.0, life=18, grav=0.0):
        for _ in range(n):
            if len(self.p) >= self.cap:
                return
            a = random.uniform(0, 6.283)
            v = random.uniform(0.3, 1.0) * speed
            self.p.append([x, y, math.cos(a) * v, math.sin(a) * v,
                           life + random.randint(0, 8), col, grav])

    @native
    def draw(self, fb, ox=0, oy=0):
        keep = []
        for p in self.p:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[6]
            p[2] *= 0.95
            p[4] -= 1
            if p[4] > 0:
                keep.append(p)
                s = 2 if p[4] > 6 else 1
                fb.fill_rect(int(p[0]) + ox, int(p[1]) + oy, s, s, p[5])
        self.p = keep


class Popups:
    def __init__(self):
        self.p = []

    def add(self, x, y, txt, col=YELLOW, scale=1):
        if len(self.p) < 10:
            self.p.append([x, y, txt, col, 32, scale])

    def draw(self, fb, ox=0, oy=0):
        keep = []
        for p in self.p:
            p[1] -= 0.7
            p[4] -= 1
            if p[4] > 0:
                keep.append(p)
                col = p[3] if p[4] > 8 or p[4] % 2 else WHITE
                ctext(fb, p[2], int(p[1]) + oy, col, p[5], int(p[0]) + ox)
        self.p = keep


class Shake:
    def __init__(self):
        self.a = 0.0

    def hit(self, a):
        self.a = max(self.a, a)

    def offset(self):
        if self.a < 0.6:
            self.a = 0.0
            return 0, 0
        a = int(self.a)
        self.a *= 0.82
        return random.randint(-a, a), random.randint(-a, a)


def wait(t0, ms=33):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < ms:
        time.sleep_ms(ms - used)


# ---------------------------------------------------------------
# Rekord
# ---------------------------------------------------------------
SAVE = "spel.json"


def load_scores():
    try:
        with open(SAVE) as f:
            return json.load(f)
    except Exception:
        return {}


SCORES = load_scores()          # rekord, utmaningar, banor och val sparas här


def save_scores():
    try:
        with open(SAVE, "w") as f:
            json.dump(SCORES, f)
    except Exception:
        pass


def submit(key, score, lower=False):
    """Sparar ett rekord. Returnerar (rekord, nytt_rekord?).
    lower=True betyder att lägre är bättre (t.ex. tid)."""
    best = SCORES.get(key)
    if best is None or (score < best if lower else score > best):
        if lower or score > 0:
            SCORES[key] = score
            save_scores()
            return score, True
    return (best if best is not None else score), False


# Utmaningar: tre per spel, varje klarad ger en stjärna
CHALLENGES = {
    "tetris": ("Rensa 20 rader", "Gor en TETRIS (4 rader)", "Na niva 6"),
    "ladr": ("Klara 5 banor", "Klara 12 banor", "Klara alla banor"),
    "flode": ("Klara 5 banor", "Klara 15 banor", "Klara 5 i tidsjakten"),
    "aventyr": ("Klara bana 2", "Ta alla 3 stenar pa en bana", "Klara alla banor"),
    "studs": ("Na 500", "Besegra ett monster", "Na 2000"),
    "pac": ("Klara en niva", "At 4 spoken pa ett piller", "Fa 5000 poang"),
    "2048": ("Gor en 256-bricka", "Gor en 1024-bricka", "Gor 2048!"),
    "invasion": ("Klara vag 3", "Anvand superlasern", "Fa 3000 poang"),
    "kross": ("Klara bana 2", "Fanga en multiboll", "Klara bana 5"),
    "kurvan": ("Vinn en runda", "Vinn en match mot datorn", "Vinn mot 2 datorer"),
}


def goal(game, i):
    """Markerar utmaning i som klar (en gång) och visar ett meddelande."""
    ach = SCORES.setdefault("ach", {})
    got = ach.get(game, [0, 0, 0])
    if got[i]:
        return
    got[i] = 1
    ach[game] = got
    save_scores()
    TOAST[0] = CHALLENGES[game][i]
    TOAST[1] = 75


def game_stars(game):
    return sum(SCORES.get("ach", {}).get(game, [0, 0, 0]))


def total_stars():
    return sum(sum(v) for v in SCORES.get("ach", {}).values())


@native
def star(fb, x, y, r, c):
    """Fylld femuddig stjärna."""
    pts = []
    for i in range(10):
        a = -1.5708 + i * 0.6283
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    for i in range(0, 10, 2):
        p0 = pts[i]
        p1 = pts[(i + 1) % 10]
        p9 = pts[(i - 1) % 10]
        tri(fb, x, y, p0[0], p0[1], p1[0], p1[1], c)
        tri(fb, x, y, p0[0], p0[1], p9[0], p9[1], c)


# ---------------------------------------------------------------
# Gemensamma skärmar
# ---------------------------------------------------------------
def pause(lcd, keys):
    """True = avsluta till menyn."""
    lcd.fill_rect(70, 72, 180, 96, BG)
    lcd.rect(70, 72, 180, 96, AMBER)
    lcd.rect(72, 74, 176, 92, LINE)
    stext(lcd, "PAUS", 84, AMBER, 3)
    ctext(lcd, "2  fortsatt", 124, WHITE)
    ctext(lcd, "3  till menyn", 142, WHITE)
    lcd.show()
    keys.wait_release()
    while True:
        keys.update()
        if keys.pressed(K2):
            keys.wait_release()
            return False
        if keys.pressed(K3):
            keys.wait_release()
            return True
        time.sleep_ms(20)


def game_over(lcd, keys, key, score, col, head="GAME OVER", sub="", lower=False, fmt=None):
    """Slutskärm. True = spela igen. fmt gör om poängen till text (t.ex. en tid)."""
    best, new = submit(key, score, lower) if key else (score, False)
    if fmt is None:
        fmt = str
    stars = Stars(40)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 15:
            if keys.pressed(K2):
                return True
            if keys.pressed(K3) or keys.pressed(K0) or keys.pressed(K1):
                return False
        gradient(lcd, NIGHT)
        stars.draw(lcd)
        if new:
            for _ in range(30):
                lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3,
                              random.choice(CONFETTI))
        dy = int(4 * math.sin(t * 0.18))
        stext(lcd, head, 30 + dy, col, 3 if len(head) <= 12 else 2)
        if sub:
            ctext(lcd, sub, 68, GRAY)
        s = fmt(score)
        stext(lcd, s, 90, WHITE, 6 if len(s) <= 5 else (4 if len(s) <= 8 else 3))
        if new:
            if (t // 7) % 2 == 0:
                ctext(lcd, "NYTT REKORD!", 156, YELLOW, 2)
        else:
            ctext(lcd, "Rekord: " + fmt(best), 160, GRAY)
        lcd.fill_rect(0, 206, W, 34, PANEL)
        ctext(lcd, "2  spela igen        3  meny", 218, WHITE)
        lcd.show()
        t += 1
        wait(t0)


def corner_keys(fb, labels, col=DIM):
    """Visar vad knapparna gör i skärmens hörn, där knapparna sitter.
    labels = (KEY0, KEY1, KEY3, KEY2)."""
    a, b, c, d = labels
    if a:
        fb.text(a, 2, 2, col)
    if b:
        fb.text(b, W - 2 - len(b) * 8, 2, col)
    if c:
        fb.text(c, 2, H - 10, col)
    if d:
        fb.text(d, W - 2 - len(d) * 8, H - 10, col)

