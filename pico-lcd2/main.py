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



def choose(lcd, keys, title, options, col, sub="", locked=()):
    """Liten valmeny. Returnerar index, eller None (3 = tillbaka).
    locked = text för alternativ som är låsta (tom sträng = öppet)."""
    sel = 0
    t = 0
    stars = Stars(30)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K0):
            sel = (sel - 1) % len(options)
        if keys.pressed(K1):
            sel = (sel + 1) % len(options)
        lk = locked[sel] if sel < len(locked) else ""
        if keys.pressed(K2) and not lk:
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            return None
        gradient(lcd, theme_bg())
        stars.draw(lcd)
        stext(lcd, title, 22 + int(3 * math.sin(t * 0.15)), col, 4)
        if sub:
            ctext(lcd, sub, 64, GRAY)
        n = len(options)
        top = 132 - n * 17
        for i, o in enumerate(options):
            y = top + i * 34
            lo = locked[i] if i < len(locked) else ""
            if i == sel:
                lcd.fill_rect(40, y - 8, 240, 28, DIM if lo else col)
                ctext(lcd, o, y, BG, 2)
            else:
                lcd.rect(40, y - 8, 240, 28, LINE)
                ctext(lcd, o, y, GRAY if lo else WHITE, 2)
            if lo:
                lcd.text(lo, 274 - len(lo) * 8, y + 4, AMBER)
        ctext(lcd, "0/1 valj   2 ok   3 tillbaka", 222, GRAY)
        lcd.show()
        t += 1
        wait(t0)


# ---------------------------------------------------------------
# Små förhandsbilder till menyn (160 x 72)
# ---------------------------------------------------------------
T_RAW = ((40, 215, 235), (255, 210, 60), (175, 95, 255), (110, 225, 100),
         (255, 85, 95), (75, 125, 255), (255, 150, 50))
T_FILL = [rgb(*c) for c in T_RAW]
T_LIGHT = [mix(c, (255, 255, 255), 0.5) for c in T_RAW]
T_DARK = [mix(c, (0, 0, 0), 0.45) for c in T_RAW]


@native
def t_cell(fb, x, y, ci, s=10):
    fb.fill_rect(x, y, s, s, T_FILL[ci])
    fb.hline(x, y, s, T_LIGHT[ci])
    fb.vline(x, y, s, T_LIGHT[ci])
    fb.hline(x, y + s - 1, s, T_DARK[ci])
    fb.vline(x + s - 1, y, s, T_DARK[ci])
    if s > 6:
        fb.fill_rect(x + 2, y + 2, 2, 2, WHITE)


def icon_tetris(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(16, 16, 38))
    stack = ((0, 5, 3), (1, 5, 3), (2, 5, 5), (3, 5, 1), (4, 5, 1), (6, 5, 2), (7, 5, 4),
             (8, 5, 4), (0, 4, 3), (1, 4, 5), (6, 4, 2), (7, 4, 2), (8, 4, 6), (9, 5, 6))
    for cx, cy, ci in stack:
        t_cell(fb, x + 25 + cx * 11, y + cy * 11 + 5, ci)
    fy = (t // 4) % 6
    for cx in (-1, 0, 1, 2):
        if fy - 1 >= 0:
            t_cell(fb, x + 25 + (4 + cx) * 11, y + (fy - 1) * 11 + 5, 0)


def icon_ladr(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(30, 22, 18))
    for i in range(8):
        for j in range(4):
            fb.fill_rect(x + 8 + i * 18, y + 2 + j * 18, 17, 17, rgb(52, 42, 34) if (i + j) % 2 else rgb(58, 46, 38))
    fb.ellipse(x + 125, y + 38, 6, 6, LIME)
    bx = x + 44 + min(60, (t % 120) // 2)
    crate(fb, bx, y + 29, 18)
    px = bx - 18
    hero(fb, px + 9, y + 38, 1, t)


def icon_flode(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, BG)
    cols = (CORAL, SKY, LIME, AMBER)
    paths = (((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)), ((0, 1), (0, 2), (1, 2), (2, 2), (3, 2)),
             ((1, 1), (2, 1)), ((4, 0), (5, 0), (5, 1), (5, 2), (4, 2), (4, 1)))
    n = (t // 6) % 24
    for k, p in enumerate(paths):
        for i, (cx, cy) in enumerate(p):
            px, py = x + 32 + cx * 20, y + 10 + cy * 20
            if i <= n - k * 3:
                fb.fill_rect(px - 4, py - 4, 9, 9, cols[k])
        for e in (p[0], p[-1]):
            fb.ellipse(x + 32 + e[0] * 20, y + 10 + e[1] * 20, 7, 7, cols[k], True)


def icon_aventyr(fb, x, y, t):
    for yy in range(72):
        fb.hline(x, y + yy, 160, mix((70, 150, 255), (190, 225, 255), yy / 72))
    for i in range(10):
        fb.fill_rect(x + i * 16, y + 56, 16, 16, rgb(140, 90, 50))
        fb.fill_rect(x + i * 16, y + 56, 16, 4, LIME)
    fb.fill_rect(x + 96, y + 36, 48, 8, rgb(160, 110, 60))
    fb.fill_rect(x + 96, y + 36, 48, 2, LIME)
    for k in range(3):
        cx = x + 30 + k * 18
        w = int(4 * abs(math.sin(t * 0.15 + k)))
        fb.ellipse(cx, y + 30, w + 1, 5, YELLOW, True)
    px = x + 20 + (t * 2) % 120
    py = y + 56 - int(abs(math.sin(t * 0.1)) * 22)
    hero(fb, px, py - 8, 1, t)


S_PLAT_C = (LIME, SKY, rgb(170, 110, 60), AMBER, rgb(235, 240, 255))


def icon_studs(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(16, 20, 44))
    for cx, cy, k in ((20, 60, 0), (90, 46, 1), (40, 30, 3), (110, 16, 4)):
        fb.fill_rect(x + cx, y + cy, 40, 5, S_PLAT_C[k])
    h = abs(math.sin(t * 0.08)) * 40
    bx = x + 40 + int(math.sin(t * 0.03) * 30)
    by = y + 58 - int(h)
    fb.ellipse(bx, by, 6, 6, LIME, True)
    fb.fill_rect(bx + 4, by - 2, 5, 3, LIME)


P_YEL = rgb(255, 225, 40)
P_BGC = rgb(4, 4, 14)
P_WALL = rgb(40, 60, 200)
P_DOT = rgb(255, 200, 170)
GHOST_C = (rgb(255, 50, 60), rgb(255, 150, 210), rgb(60, 230, 240), rgb(255, 170, 60))
FRIGHT_C = rgb(50, 70, 255)
DIRS4 = ((0, -1), (1, 0), (0, 1), (-1, 0))         # upp, höger, ner, vänster


def draw_pac(fb, px, py, face, mouth, col=P_YEL, r=5, bg=P_BGC):
    fb.ellipse(px, py, r, r, col, True)
    if mouth > 0.05:
        a = DIRS4[face if face >= 0 else 3]
        ang = math.atan2(a[1], a[0])
        m = mouth * 0.9
        tri(fb, px, py, px + int(math.cos(ang - m) * (r + 2)), py + int(math.sin(ang - m) * (r + 2)),
            px + int(math.cos(ang + m) * (r + 2)), py + int(math.sin(ang + m) * (r + 2)), bg)


def draw_ghost(fb, px, py, col, d, t, eyes_only=False, fright=False):
    if not eyes_only:
        fb.ellipse(px, py - 1, 5, 5, col, True)
        fb.fill_rect(px - 5, py - 1, 11, 5, col)
        k = (t // 4) % 2
        for i in range(3):
            fb.fill_rect(px - 5 + i * 4 + k, py + 4, 2, 2, col)
    if fright:
        fb.fill_rect(px - 3, py - 2, 2, 2, WHITE)
        fb.fill_rect(px + 2, py - 2, 2, 2, WHITE)
        fb.hline(px - 3, py + 2, 7, WHITE)
        return
    dx, dy = DIRS4[d] if d >= 0 else (0, 0)
    for ex in (-2, 2):
        fb.fill_rect(px + ex - 1, py - 3, 3, 4, WHITE)
        fb.fill_rect(px + ex + dx, py - 2 + dy, 2, 2, rgb(30, 50, 200))


def icon_pac(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, P_BGC)
    fb.rect(x + 4, y + 4, 152, 64, P_WALL)
    fb.rect(x + 6, y + 6, 148, 60, P_WALL)
    px = x + 20 + (t * 2) % 120
    for i in range(12):
        dx = x + 20 + i * 12
        if dx > px:
            fb.fill_rect(dx, y + 36, 3, 3, P_DOT)
    draw_pac(fb, px, y + 37, 1, abs(math.sin(t * 0.5)), P_YEL, 9)
    for i in range(2):
        gx = px - 34 - i * 22
        if gx > x + 10:
            draw_ghost(fb, gx, y + 37, GHOST_C[i], 1, t)


G_RAW = ((238, 228, 218), (237, 224, 200), (242, 177, 121), (245, 149, 99), (246, 124, 95),
         (246, 94, 59), (237, 207, 114), (237, 204, 97), (237, 200, 80), (237, 197, 63),
         (237, 194, 46), (170, 110, 255), (120, 90, 255), (60, 200, 220))
G_COL = [rgb(*c) for c in G_RAW]
G_TXT_DARK = rgb(119, 110, 101)
G_S = 46


def g_tile(fb, x, y, e, s=G_S):
    col = G_COL[min(e - 1, len(G_COL) - 1)]
    fb.fill_rect(x + 2, y, s - 4, s, col)
    fb.fill_rect(x, y + 2, s, s - 4, col)
    v = str(1 << e)
    sc = 3 if len(v) == 1 else (2 if len(v) <= 3 else 1)
    if s < G_S:
        sc = max(1, sc - 1)
    tc = G_TXT_DARK if e <= 2 else WHITE
    ctext(fb, v, y + s // 2 - 4 * sc, tc, sc, x + s // 2)


def icon_2048(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(60, 52, 80))
    vals = (1, 2, 3, 4, 5, 6, 7, 11)
    for i in range(8):
        e = vals[(i + t // 30) % 8]
        g_tile(fb, x + 6 + (i % 4) * 38, y + 4 + (i // 4) * 34, e, 32)


SPR_SQUID = ("...##...", "..####..", ".######.", "##.##.##", "########", "..#..#..", ".#.##.#.", "#.#..#.#")


def icon_invasion(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, BLACK)
    off = int(6 * math.sin(t * 0.05))
    cols = (PINK, TEAL, LIME)
    for r in range(3):
        for c in range(5):
            bx = x + 18 + c * 26 + off
            by = y + 4 + r * 13
            for yy, row in enumerate(SPR_SQUID):
                for xx, ch in enumerate(row):
                    if ch == "#":
                        fb.pixel(bx + xx, by + yy, cols[r])
    sx = x + 80 + int(40 * math.sin(t * 0.04))
    fb.fill_rect(sx - 8, y + 64, 16, 5, SKY)
    fb.fill_rect(sx - 1, y + 60, 3, 4, SKY)
    k = (t * 4) % 40
    fb.fill_rect(sx, y + 56 - k, 1, 4, YELLOW)


BR_N = (CORAL, AMBER, YELLOW, LIME, SKY)


def icon_kross(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(18, 14, 40))
    for r in range(4):
        for c in range(7):
            if (r * 7 + c + t // 15) % 9:
                fb.fill_rect(x + 4 + c * 22, y + 4 + r * 9, 20, 7, BR_N[r])
    bx = x + 10 + int(abs(((t * 3) % 280) - 140))
    by = y + 44 + int(abs(((t * 2) % 40) - 20)) // 2
    fb.fill_rect(min(max(bx - 16, x), x + 128), y + 66, 32, 4, SKY)
    fb.ellipse(min(bx, x + 156), by, 3, 3, WHITE, True)


K_COLS = (TEAL, PINK, AMBER)


def icon_kurvan(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, BG)
    fb.rect(x, y, 160, 72, LINE)
    for i in range(2):
        a = 0.0
        px, py = x + 20 + i * 30, y + 20 + i * 30
        for s in range(min(110, t % 160)):
            a += math.sin(s * 0.06 + i * 2) * 0.09
            px += math.cos(a) * 1.2
            py += math.sin(a) * 0.7
            if (s // 20) % 6 != 5:
                fb.fill_rect(int(px), int(py), 2, 2, K_COLS[i])


# Figurer som flera spel använder
def crate(fb, x, y, s, done=False):
    """Trälåda (LÅDOR)."""
    c = rgb(200, 140, 60) if not done else rgb(120, 210, 90)
    d = rgb(130, 80, 30) if not done else rgb(60, 140, 50)
    fb.fill_rect(x, y, s, s, c)
    fb.rect(x, y, s, s, d)
    fb.rect(x + 2, y + 2, s - 4, s - 4, d)
    fb.line(x + 2, y + 2, x + s - 3, y + s - 3, d)
    fb.line(x + s - 3, y + 2, x + 2, y + s - 3, d)


def hero(fb, x, y, face, t, col=None):
    """Liten hjälte med keps, x/y = mitten."""
    c = col if col is not None else rgb(255, 90, 90)
    fb.fill_rect(x - 4, y - 7, 8, 3, c)                         # keps
    fb.fill_rect(x + (2 if face > 0 else -6), y - 6, 4, 2, c)
    fb.fill_rect(x - 3, y - 4, 6, 5, rgb(255, 205, 160))        # ansikte
    fb.pixel(x + face * 1 + (1 if face > 0 else -2), y - 3, BLACK)
    fb.fill_rect(x - 4, y + 1, 8, 5, c)                          # tröja
    s = (t // 3) % 2
    fb.fill_rect(x - 4, y + 6, 3, 3 if s else 2, rgb(50, 80, 200))
    fb.fill_rect(x + 1, y + 6, 3, 2 if s else 3, rgb(50, 80, 200))


# ---------------------------------------------------------------
# Teman för menyn (låses upp med stjärnor)
# ---------------------------------------------------------------
THEMES = (
    ("NATT", 0, ((16, 14, 40), (36, 14, 54))),
    ("SOLNEDGANG", 8, ((60, 20, 60), (140, 60, 40))),
    ("HAV", 16, ((6, 30, 60), (10, 80, 90))),
    ("SKOG", 22, ((10, 40, 20), (40, 70, 30))),
    ("GULD", 30, ((60, 40, 6), (120, 90, 20))),
)
_THEME_BG = [None, -1]


def theme_bg():
    i = SCORES.get("theme", 0) % len(THEMES)
    if _THEME_BG[1] != i:
        a, b = THEMES[i][2]
        _THEME_BG[0] = [mix(a, b, y / (H - 1)) for y in range(H)]
        _THEME_BG[1] = i
    return _THEME_BG[0]


# ---------------------------------------------------------------
# Spelen läses in från kommentarerna längst ner i den här filen
# ---------------------------------------------------------------
def load_game(name):
    """Läser spelets kod (rader '#|...' efter '#@@ namn') och kör den.
    Returnerar spelets namnrymd. Bara ett spel i minnet åt gången."""
    gc.collect()
    src = None
    for path in (globals().get("__file__"), "main.py", "/main.py"):
        if not path:
            continue
        try:
            src = open(path)
            break
        except OSError:
            src = None
    if src is None:
        raise OSError("Hittar inte main.py pa Picon. Spara filen pa Picon som main.py.")
    lines = []
    on = False
    for line in src:
        if line.startswith("#@@ "):
            on = line[4:].strip() == name
            continue
        if on and line.startswith("#|"):
            lines.append(line[2:])
    src.close()
    code = "".join(lines)
    lines = None
    gc.collect()
    ns = dict(globals())
    exec(code, ns)
    code = None
    gc.collect()
    return ns


# (nyckel, namn, färg, beskrivning, knappar (0, 1, 3, 2), ikon)
GAMES = (
    ("tetris", "TETRIS", TEAL, ("Fyll hela rader. Tre", "lagen: MARATON,", "SPRINT och SKATT."),
     ("vanster", "hoger", "slapp", "vrid"), icon_tetris),
    ("ladr", "LADOR", AMBER, ("Knuffa ladorna till", "de grona prickarna.", "Fa drag = rekord!"),
     ("upp", "hoger", "vanster", "ner"), icon_ladr),
    ("flode", "FLODE", PINK, ("Koppla ihop lika", "farger och fyll hela", "rutnatet. Tidsjakt!"),
     ("upp", "hoger", "vanster", "ner"), icon_flode),
    ("aventyr", "AVENTYR", LIME, ("Spring, hoppa och", "dasha genom banorna.", "Ta mynt och stenar!"),
     ("vanster", "hoger", "dash", "hoppa"), icon_aventyr),
    ("studs", "STUDS", SKY, ("Studsa hogt upp! Nya", "varldar, jetpack och", "monster pa vagen."),
     ("vanster", "hoger", "", "skjut"), icon_studs),
    ("pac", "SPOKJAKT", YELLOW, ("At alla prickar!", "Stora prickar gor", "spoken atbara."),
     ("upp", "hoger", "vanster", "ner"), icon_pac),
    ("2048", "2048", G_COL[4], ("Skjut brickorna at", "ett hall. Lika tal", "slas ihop. Na 2048!"),
     ("upp", "hoger", "vanster", "ner"), icon_2048),
    ("invasion", "INVASION", LIME, ("Skjut ner invasionen", "innan den landar.", "Full matare = laser"),
     ("vanster", "hoger", "laser", "skjut"), icon_invasion),
    ("kross", "KROSS", CORAL, ("Krossa alla stenar.", "Lila tal flera slag,", "X-stenar sprangs."),
     ("vanster", "hoger", "skjut", "skjut"), icon_kross),
    ("kurvan", "KURVAN", VIOLET, ("Rita en linje och", "krocka inte! Mot", "datorn eller 2 spel."),
     ("P1 <", "P2 <", "P1 >", "P2 >"), icon_kurvan),
)


def menu(lcd, keys, sel):
    stars = Stars(36)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.repeat(K0, 12, 4):
            sel = (sel - 1) % len(GAMES)
        if keys.repeat(K1, 12, 4):
            sel = (sel + 1) % len(GAMES)
        if keys.pressed(K2):
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            stars_screen(lcd, keys, sel)
            keys.wait_release()
        key, name, col, desc, ctrl, icon = GAMES[sel]
        gradient(lcd, theme_bg())
        stars.draw(lcd, -0.3, 0.0)
        # Rubrik
        x = 6
        for i, ch in enumerate("PICO SPEL"):
            c = CONFETTI[(i + t // 8) % len(CONFETTI)]
            dy = int(2 * math.sin(t * 0.15 + i * 0.6))
            big(lcd, ch, x + 2, 6 + dy + 2, SHADOW, 3)
            big(lcd, ch, x, 6 + dy, c, 3)
            x += 24
        star(lcd, 240, 17, 8, YELLOW)
        big(lcd, "%d" % total_stars(), 252, 10, YELLOW, 2)
        rtext(lcd, "/30", W - 4, 14, GRAY)
        # Listan
        for i, g in enumerate(GAMES):
            y = 38 + i * 20
            if i == sel:
                lcd.fill_rect(4, y - 2, 134, 19, g[2])
                if len(g[1]) > 7:
                    big(lcd, g[1], 10, y + 4, BG, 1)
                else:
                    big(lcd, g[1], 10, y, BG, 2)
            else:
                lcd.fill_rect(4, y - 2, 3, 19, g[2])
                lcd.text(g[1], 12, y + 4, WHITE)
            gs = game_stars(g[0])
            for k in range(3):
                c = YELLOW if k < gs else (BG if i == sel else LINE)
                lcd.fill_rect(118 + k * 6, y + 6, 4, 4, c)
        # Förhandsvisning
        lcd.fill_rect(144, 36, 172, 202, PANEL)
        lcd.rect(144, 36, 172, 202, col)
        icon(lcd, 150, 42, t)
        lcd.rect(149, 41, 162, 74, LINE)
        ctext(lcd, name, 120, col, 2, 230)
        for i, d in enumerate(desc):
            ctext(lcd, d, 140 + i * 11, GRAY, 1, 230)
        best = SCORES.get(key)
        if isinstance(best, int) and best > 0:
            ctext(lcd, "Rekord: %d" % best, 176, WHITE, 1, 230)
        a, b, c, d = ctrl
        lcd.hline(150, 190, 160, LINE)
        lcd.text("0 " + a, 152, 196, WHITE)
        if b:
            rtext(lcd, b + " 1", 310, 196, WHITE)
        if c:
            lcd.text("3 " + c, 152, 210, WHITE)
        if d:
            rtext(lcd, d + " 2", 310, 210, WHITE)
        ctext(lcd, "2 spela   3 stjarnor", 226, DIM, 1, 230)
        lcd.show()
        t += 1
        wait(t0)


def stars_screen(lcd, keys, sel):
    """Utmaningarna för valt spel, och val av menytema.
    0/1 byter spel, 2 byter tema, 3 tillbaka."""
    keys.wait_release()
    t = 0
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K3):
            return
        if keys.pressed(K0):
            sel = (sel - 1) % len(GAMES)
        if keys.pressed(K1):
            sel = (sel + 1) % len(GAMES)
        if keys.pressed(K2):
            n = total_stars()
            cur = SCORES.get("theme", 0)
            for k in range(1, len(THEMES) + 1):
                j = (cur + k) % len(THEMES)
                if THEMES[j][1] <= n:
                    SCORES["theme"] = j
                    break
            save_scores()
        key, name, col = GAMES[sel][0], GAMES[sel][1], GAMES[sel][2]
        gradient(lcd, theme_bg())
        big(lcd, "STJARNOR", 14, 11, SHADOW, 3)
        big(lcd, "STJARNOR", 12, 9, YELLOW, 3)
        star(lcd, 236, 20, 10, YELLOW)
        big(lcd, "%d/30" % total_stars(), 250, 13, YELLOW, 1)
        lcd.fill_rect(10, 44, 300, 104, PANEL)
        lcd.rect(10, 44, 300, 104, col)
        ctext(lcd, "< " + name + " >", 52, col, 2)
        got = SCORES.get("ach", {}).get(key, [0, 0, 0])
        for i, txt in enumerate(CHALLENGES[key]):
            y = 80 + i * 22
            if got[i]:
                star(lcd, 30, y + 3, 7, YELLOW)
            else:
                lcd.ellipse(30, y + 3, 6, 6, DIM)
            lcd.text(txt, 46, y, WHITE if got[i] else GRAY)
        # Teman
        n = total_stars()
        lcd.text("MENYTEMA (2 byter):", 12, 160, GRAY)
        cur = SCORES.get("theme", 0)
        for i, (tn, need, cols) in enumerate(THEMES):
            x = 12 + i * 61
            a, b = cols
            lcd.fill_rect(x, 174, 56, 24, mix(a, b, 0.5))
            if i == cur:
                lcd.rect(x - 2, 172, 60, 28, WHITE)
            if need > n:
                lcd.text("%d" % need, x + 4, 182, AMBER)
                star(lcd, x + 40, 186, 5, AMBER)
            else:
                lcd.text(tn[:7], x + 2, 182, WHITE)
        ctext(lcd, "0/1 byt spel   3 tillbaka", 222, GRAY)
        lcd.show()
        t += 1
        wait(t0)


def show_error(lcd, e):
    import sys
    import io
    sys.print_exception(e)
    buf = io.StringIO()
    sys.print_exception(e, buf)
    lcd.fill(rgb(110, 0, 0))
    lcd.text("FEL! Skicka det har till Claude:", 4, 4, WHITE)
    y = 20
    for line in buf.getvalue().split("\n"):
        while line and y < H - 8:
            lcd.text(line[:39], 4, y, WHITE)
            line = line[39:]
            y += 10
    lcd.show()


def main():
    lcd = LCD()
    keys = Keys()
    sel = SCORES.get("_sel", 0) % len(GAMES)
    while True:
        try:
            sel = menu(lcd, keys, sel)
            if SCORES.get("_sel") != sel:
                SCORES["_sel"] = sel
                save_scores()
            key, name, col = GAMES[sel][0], GAMES[sel][1], GAMES[sel][2]
            lcd.fill(BG)
            ctext(lcd, "LADDAR " + name + "...", 112, col, 2)
            lcd.show()
            ns = load_game(key)
            play = ns["play"]
            while True:
                gc.collect()
                res = play(lcd, keys)
                if res is None:
                    break
                if isinstance(res, tuple):
                    # (rubrik, poäng, rekordnyckel, text, lägre_bättre, visa)
                    head, score, rk, sub, low, fmt = res
                    again = game_over(lcd, keys, rk, score, col, head, sub, low, fmt)
                else:
                    again = game_over(lcd, keys, key, res, col)
                if not again:
                    break
            play = None
            ns.clear()
            ns = None
            gc.collect()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            show_error(lcd, e)
            keys.wait_release()
            while True:
                keys.update()
                if any(keys.now):
                    break
                time.sleep_ms(20)


main()

# ===============================================================
# SPELENS KOD (läses in av load_game när spelet väljs)
# ===============================================================
#@@ tetris
#|# TETRIS: tre lägen. 0 vänster, 1 höger, 2 vrid, 3 släpp direkt.
#|TC = 11                         # rutstorlek
#|TW, TH = 10, 20
#|TX, TY = 105, 10
#|SHAPES = (
#|    ((-1, 0), (0, 0), (1, 0), (2, 0)),      # I
#|    ((0, 0), (1, 0), (0, 1), (1, 1)),       # O
#|    ((-1, 0), (0, 0), (1, 0), (0, -1)),     # T
#|    ((-1, 0), (0, 0), (0, -1), (1, -1)),    # S
#|    ((-1, -1), (0, -1), (0, 0), (1, 0)),    # Z
#|    ((-1, -1), (-1, 0), (0, 0), (1, 0)),    # J
#|    ((1, -1), (-1, 0), (0, 0), (1, 0)),     # L
#|)
#|# Guld (index 7) och skräp (index 8) läggs till efter de vanliga färgerna
#|if len(T_FILL) == 7:
#|    for c in ((255, 215, 0), (110, 110, 135)):
#|        T_FILL.append(rgb(*c))
#|        T_LIGHT.append(mix(c, (255, 255, 255), 0.6))
#|        T_DARK.append(mix(c, (0, 0, 0), 0.45))
#|T_GHOST = [mix(c, C_BG, 0.6) for c in T_RAW]
#|GOLD, JUNK = 8, 9                     # värden i brädet (färg + 1)
#|T_BOARD = rgb(16, 16, 38)
#|T_GRID = rgb(28, 28, 58)
#|T_BG = [mix((20, 18, 50), (8, 30, 50), y / (H - 1)) for y in range(H)]
#|T_POINTS = (0, 100, 300, 500, 800)
#|
#|
#|@native
#|def t_board(fb, board):
#|    for y in range(TH):
#|        row = board[y]
#|        for x in range(TW):
#|            v = row[x]
#|            if v:
#|                t_cell(fb, TX + x * TC, TY + y * TC, v - 1)
#|
#|
#|def fmt_time(f):
#|    """Bilder (30 per sekund) till m:ss.t"""
#|    s10 = f * 10 // 30
#|    return "%d:%02d.%d" % (s10 // 600, (s10 // 10) % 60, s10 % 10)
#|
#|
#|def play(lcd, keys):
#|    n = total_stars()
#|    mode = choose(lcd, keys, "TETRIS", ("MARATON", "SPRINT 40", "SKATT"), TEAL,
#|                  "Las upp lagen med stjarnor",
#|                  ("", "" if n >= 3 else "3 stj", "" if n >= 8 else "8 stj"))
#|    if mode is None:
#|        return None
#|    return tetris(lcd, keys, mode)
#|
#|
#|def tetris(lcd, keys, mode):
#|    board = [bytearray(TW) for _ in range(TH)]
#|    bag = []
#|    golds = 0
#|    if mode == 2:                       # SKATT: skräprader med guld längst ner
#|        for y in range(TH - 9, TH):
#|            hole = random.randint(0, TW - 1)
#|            for x in range(TW):
#|                if x != hole:
#|                    board[y][x] = JUNK
#|            if y >= TH - 7 and y % 2 == 1:
#|                gx = random.randint(0, TW - 1)
#|                if gx == hole:
#|                    gx = (gx + 1) % TW
#|                board[y][gx] = GOLD
#|                golds += 1
#|    found = 0
#|    clock = 0
#|    rise = 0
#|
#|    def nxt():
#|        if not bag:
#|            bag.extend(shuffled(7))
#|        return bag.pop()
#|
#|    def fits(cells, px, py):
#|        for cx, cy in cells:
#|            x = px + cx
#|            y = py + cy
#|            if x < 0 or x >= TW or y >= TH:
#|                return False
#|            if y >= 0 and board[y][x]:
#|                return False
#|        return True
#|
#|    queue = [nxt(), nxt(), nxt()]
#|    cur = nxt()
#|    cells = SHAPES[cur]
#|    px, py = 4, 1
#|    score = lines = 0
#|    level = 1
#|    fall = 0
#|    lock = 0
#|    resets = 0
#|    combo = -1
#|    parts = Particles(160)
#|    pops = Popups()
#|    shake = Shake()
#|    banner, btxt, bcol = 0, "", WHITE
#|    t = 0
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pause() and pause(lcd, keys):
#|            return None if mode else score
#|        clock += 1
#|        if mode == 2:                   # skräp stiger upp var 15:e sekund
#|            rise += 1
#|            if rise >= 450:
#|                rise = 0
#|                if any(board[0]):
#|                    return ("BEGRAVD!", found, None, "Guld hittat: %d av %d" % (found, golds), False, str)
#|                del board[0]
#|                hole = random.randint(0, TW - 1)
#|                row = bytearray(TW)
#|                for x in range(TW):
#|                    if x != hole:
#|                        row[x] = JUNK
#|                board.append(row)
#|                shake.hit(4)
#|                if not fits(cells, px, py):  # skräpet knuffar upp biten
#|                    py -= 1
#|        moved = False
#|        if keys.repeat(K0, 8, 2) and fits(cells, px - 1, py):
#|            px -= 1
#|            moved = True
#|        if keys.repeat(K1, 8, 2) and fits(cells, px + 1, py):
#|            px += 1
#|            moved = True
#|        if keys.pressed(K2) and cur != 1:
#|            r = tuple((-cy, cx) for cx, cy in cells)
#|            for dx, dy in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)):
#|                if fits(r, px + dx, py + dy):
#|                    cells = r
#|                    px += dx
#|                    py += dy
#|                    moved = True
#|                    break
#|        if moved and lock and resets < 15:        # man hinner flytta lite på marken
#|            lock = 1
#|            resets += 1
#|        drop = False
#|        if keys.pressed(K3):                      # släpp direkt
#|            n = 0
#|            while fits(cells, px, py + 1):
#|                py += 1
#|                n += 1
#|            score += n * 2
#|            drop = True
#|            shake.hit(3)
#|            for cx, cy in cells:
#|                parts.burst(TX + (px + cx) * TC + 5, TY + (py + cy) * TC + 10,
#|                            T_LIGHT[cur], 2, 1.5, 10)
#|        # Tyngdkraft
#|        fall += 1
#|        interval = max(2, int(30 * (0.84 ** (level - 1)))) if mode == 0 else (8 if mode == 1 else 14)
#|        if fall >= interval:
#|            fall = 0
#|            if fits(cells, px, py + 1):
#|                py += 1
#|        on_ground = not fits(cells, px, py + 1)
#|        lock = lock + 1 if on_ground else 0
#|        if on_ground and (lock > 16 or drop):
#|            for cx, cy in cells:
#|                if py + cy >= 0:
#|                    board[py + cy][px + cx] = cur + 1
#|            full = []
#|            for y in range(TH):
#|                if all(board[y]):
#|                    full.append(y)
#|            if full:
#|                combo += 1
#|                for y in full:
#|                    for x in range(TW):
#|                        if board[y][x] == GOLD:
#|                            found += 1
#|                            pops.add(TX + x * TC + 5, TY + y * TC - 6, "GULD!", YELLOW)
#|                for k in range(8):                # blinka raderna
#|                    gradient(lcd, T_BG)
#|                    lcd.fill_rect(TX - 1, TY - 1, TW * TC + 1, TH * TC + 1, T_BOARD)
#|                    t_board(lcd, board)
#|                    for y in full:
#|                        if k % 2 == 0:
#|                            lcd.fill_rect(TX, TY + y * TC, TW * TC - 1, TC - 1, WHITE)
#|                    lcd.show()
#|                    time.sleep_ms(30)
#|                for y in full:
#|                    for x in range(TW):
#|                        parts.burst(TX + x * TC + 5, TY + y * TC + 5, T_FILL[board[y][x] - 1], 3, 3, 16)
#|                    del board[y]
#|                    board.insert(0, bytearray(TW))
#|                gain = T_POINTS[len(full)] * level + max(0, combo) * 50 * level
#|                score += gain
#|                lines += len(full)
#|                if lines >= 20:
#|                    goal("tetris", 0)
#|                if len(full) == 4:
#|                    goal("tetris", 1)
#|                new_level = lines // 10 + 1 if mode == 0 else level
#|                pops.add(TX + TW * TC // 2, TY + full[0] * TC, "+%d" % gain, AMBER)
#|                if len(full) == 4:
#|                    banner, btxt, bcol = 50, "TETRIS!", PINK
#|                    shake.hit(8)
#|                elif combo >= 2:
#|                    banner, btxt, bcol = 35, "KOMBO x%d" % combo, TEAL
#|                if new_level > level:
#|                    level = new_level
#|                    banner, btxt, bcol = 50, "NIVA %d" % level, LIME
#|                    if level >= 6:
#|                        goal("tetris", 2)
#|                if mode == 1 and lines >= 40:
#|                    return ("SNABBT!", clock, "tetris_sprint", "40 rader", True, fmt_time)
#|                if mode == 2 and found >= golds:
#|                    return ("SKATTEN HITTAD!", clock, "tetris_skatt", "Allt guld pa", True, fmt_time)
#|            else:
#|                combo = -1
#|            cur = queue.pop(0)
#|            queue.append(nxt())
#|            cells = SHAPES[cur]
#|            px, py = 4, 1
#|            lock = resets = 0
#|            fall = 0
#|            if not fits(cells, px, py):
#|                for k in range(20):
#|                    lcd.fill_rect(TX, TY + (19 - k) * TC, TW * TC - 1, TC - 1, DIM)
#|                    lcd.show()
#|                    time.sleep_ms(30)
#|                if mode == 1:
#|                    return ("GAME OVER", lines, None, "Rader av 40", False, str)
#|                if mode == 2:
#|                    return ("GAME OVER", found, None, "Guld hittat av %d" % golds, False, str)
#|                return score
#|
#|        # --- Rita ---
#|        ox, oy = shake.offset()
#|        gradient(lcd, T_BG)
#|        lcd.fill_rect(TX - 4 + ox, TY - 4 + oy, TW * TC + 7, TH * TC + 7, LINE)
#|        lcd.fill_rect(TX - 1 + ox, TY - 1 + oy, TW * TC + 1, TH * TC + 1, T_BOARD)
#|        for x in range(1, TW):
#|            lcd.vline(TX + x * TC - 1 + ox, TY + oy, TH * TC - 1, T_GRID)
#|        for y in range(1, TH):
#|            lcd.hline(TX + ox, TY + y * TC - 1 + oy, TW * TC - 1, T_GRID)
#|        if ox or oy:
#|            for y in range(TH):
#|                for x in range(TW):
#|                    v = board[y][x]
#|                    if v:
#|                        t_cell(lcd, TX + x * TC + ox, TY + y * TC + oy, v - 1)
#|        else:
#|            t_board(lcd, board)
#|        gy = py
#|        while fits(cells, px, gy + 1):
#|            gy += 1
#|        for cx, cy in cells:
#|            if gy + cy >= 0:
#|                lcd.rect(TX + (px + cx) * TC, TY + (gy + cy) * TC, 10, 10, T_GHOST[cur])
#|        for cx, cy in cells:
#|            if py + cy >= 0:
#|                t_cell(lcd, TX + (px + cx) * TC + ox, TY + (py + cy) * TC + oy, cur)
#|        # Nästa bitar
#|        lcd.fill_rect(228, 10, 84, 136, PANEL)
#|        lcd.text("NASTA", 250, 16, GRAY)
#|        for i, q in enumerate(queue):
#|            s = 10 if i == 0 else 7
#|            bx, by = 262, 46 + i * 34 + (0 if i == 0 else 6)
#|            for cx, cy in SHAPES[q]:
#|                t_cell(lcd, bx + cx * (s + 1), by + cy * (s + 1), q, s)
#|        # Poäng
#|        lcd.fill_rect(8, 10, 88, 160, PANEL)
#|        if mode == 0:
#|            lcd.text("POANG", 16, 18, GRAY)
#|            big(lcd, str(score), 16, 30, WHITE, 2 if score < 100000 else 1)
#|            lcd.text("RADER", 16, 62, GRAY)
#|            big(lcd, str(lines), 16, 74, WHITE, 2)
#|            lcd.text("NIVA", 16, 106, GRAY)
#|            big(lcd, str(level), 16, 118, LIME, 3)
#|            lcd.text("REKORD", 16, 150, DIM)
#|            lcd.text(str(SCORES.get("tetris", 0)), 16, 160, DIM)
#|        else:
#|            lcd.text("TID", 16, 18, GRAY)
#|            big(lcd, fmt_time(clock), 14, 30, WHITE, 1)
#|            if mode == 1:
#|                lcd.text("RADER KVAR", 16, 62, GRAY)
#|                big(lcd, str(max(0, 40 - lines)), 16, 74, AMBER, 3)
#|                rk = SCORES.get("tetris_sprint")
#|            else:
#|                lcd.text("GULD", 16, 62, GRAY)
#|                big(lcd, "%d/%d" % (found, golds), 16, 74, YELLOW, 2)
#|                lcd.text("SKRAP OM", 16, 106, GRAY)
#|                big(lcd, "%d" % ((450 - rise) // 30), 16, 118, CORAL, 2)
#|                rk = SCORES.get("tetris_skatt")
#|            if rk:
#|                lcd.text("REKORD", 16, 150, DIM)
#|                lcd.text(fmt_time(rk), 16, 160, DIM)
#|        lcd.text("0 <  > 1", 18, 196, DIM)
#|        lcd.text("3 slapp", 18, 208, DIM)
#|        lcd.text("2 vrid", 18, 220, DIM)
#|        parts.draw(lcd, ox, oy)
#|        pops.draw(lcd, ox, oy)
#|        if banner > 0:
#|            banner -= 1
#|            stext(lcd, btxt, 100, bcol, 3, TX + TW * TC // 2)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#@@ ladr
#|# LADOR (Sokoban): knuffa alla lådor till de gröna prickarna.
#|#   pilarna i hörnen: 0 upp, 1 höger, 2 ner, 3 vänster
#|#   håll alla fyra: 0 ångra, 1 börja om, 2 fortsätt, 3 till banorna
#|# Banorna är skapade av verktyg/gen_ladr.py och kontrollerade med en lösare.
#|
#|LEVELS = (
#|    (4, ('#######', '#  #  #', '#  $. #', '#$    #', '#+#  ##', '######-')),  # minst 4 knuffar
#|    (6, ('#######', '#@    #', '#  #$ #', '#.$   #', '#.  ###', '#####--')),  # minst 6 knuffar
#|    (4, ('######-', '# .#@##', '#   $ #', '# $  .#', '#    ##', '######-')),  # minst 4 knuffar
#|    (4, ('#######', '# #. @#', '#  $$##', '#    ##', '#    .#', '#######')),  # minst 4 knuffar
#|    (4, ('#######', '#   $.#', '#   $@#', '#  #. #', '#   ###', '#####--')),  # minst 4 knuffar
#|    (8, ('########', '#      #', '#   $@##', '# $    #', '# #.$  #', '## . . #', '-#######')),  # minst 8 knuffar
#|    (8, ('#######-', '# $ . ##', '# $.##@#', '#   #  #', '#   .$ #', '### #  #', '--######')),  # minst 8 knuffar
#|    (9, ('########', '#    #.#', '#    $ #', '# .   .#', '#   #$$#', '# ## @ #', '########')),  # minst 9 knuffar
#|    (8, ('########', '#@##   #', '# $  . #', '# $ .# #', '# $  # #', '#   .  #', '########')),  # minst 8 knuffar
#|    (10, ('########', '#+ #   #', '#$# $ .#', '#   # ##', '#  #   #', '#  $  .#', '########')),  # minst 10 knuffar
#|    (9, ('-#######', '##@# . #', '# $#   #', '#   #$ #', '#    . #', '# . $  #', '########')),  # minst 9 knuffar
#|    (8, ('########', '#@  # .#', '#$#$# $#', '#      #', '#    # #', '#..#   #', '########')),  # minst 8 knuffar
#|    (15, ('-########', '##@#  # #', '#.$  .# #', '#      .#', '###     #', '#  $$   #', '#       #', '#########')),  # minst 15 knuffar
#|    (14, ('-########', '##  # #.#', '#     @ #', '# $##   #', '#    #$ #', '###.    #', '#.  $  ##', '########-')),  # minst 14 knuffar
#|    (14, ('########-', '#.     ##', '#     . #', '#      ##', '# #$$  .#', '##@$  # #', '#  #    #', '#########')),  # minst 14 knuffar
#|    (15, ('########-', '#   #  ##', '# $ # $ #', '#    @# #', '# $   . #', '#    .###', '# ## .  #', '#########')),  # minst 15 knuffar
#|    (14, ('#########', '#.@ #   #', '#    $  #', '# $  ####', '#    #  #', '# $  #  #', '# .  .  #', '#########')),  # minst 14 knuffar
#|    (18, ('#######--', '#  #  ###', '# $@$  .#', '# $ #   #', '#     ..#', '#  .  $ #', '#    # ##', '########-')),  # minst 18 knuffar
#|    (16, ('-########', '##    . #', '#   .$ ##', '#     $ #', '# .# ##@#', '#  #  $ #', '#  $   .#', '#########')),  # minst 16 knuffar
#|    (16, ('-#######-', '## ## @##', '#  # $$ #', '#     $.#', '#     $ #', '#    .  #', '#.    #.#', '#########')),  # minst 16 knuffar
#|)
#|
#|L_FLOOR = (rgb(58, 46, 38), rgb(52, 42, 34))
#|L_WALL = rgb(120, 90, 160)
#|L_WALL_L = rgb(160, 130, 200)
#|L_WALL_D = rgb(70, 50, 100)
#|L_GOAL = rgb(90, 230, 120)
#|L_BG = [mix((24, 16, 30), (40, 24, 20), y / (H - 1)) for y in range(H)]
#|
#|
#|def l_parse(rows):
#|    walls, goals, boxes = set(), set(), []
#|    p = (0, 0)
#|    for y, r in enumerate(rows):
#|        for x, ch in enumerate(r):
#|            if ch == "#":
#|                walls.add((x, y))
#|            if ch in ".*+":
#|                goals.add((x, y))
#|            if ch in "$*":
#|                boxes.append((x, y))
#|            if ch in "@+":
#|                p = (x, y)
#|    return walls, goals, boxes, p
#|
#|
#|def l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, hud):
#|    gradient(lcd, L_BG)
#|    for y, r in enumerate(rows):
#|        for x, ch in enumerate(r):
#|            if ch == "-":
#|                continue
#|            px, py = ox + x * ts, oy + y * ts
#|            if (x, y) in walls:
#|                lcd.fill_rect(px, py, ts, ts, L_WALL)
#|                lcd.hline(px, py, ts, L_WALL_L)
#|                lcd.vline(px, py, ts, L_WALL_L)
#|                lcd.hline(px, py + ts - 1, ts, L_WALL_D)
#|                lcd.vline(px + ts - 1, py, ts, L_WALL_D)
#|            else:
#|                lcd.fill_rect(px, py, ts, ts, L_FLOOR[(x + y) % 2])
#|                if (x, y) in goals:
#|                    r2 = ts // 4 + (1 if (t // 8) % 2 else 0)
#|                    lcd.ellipse(px + ts // 2, py + ts // 2, r2, r2, L_GOAL)
#|                    lcd.ellipse(px + ts // 2, py + ts // 2, 2, 2, L_GOAL, True)
#|    for b in boxes:
#|        crate(lcd, ox + b[0] * ts + 1, oy + b[1] * ts + 1, ts - 2, b in goals)
#|    hero(lcd, ox + p[0] * ts + ts // 2, oy + p[1] * ts + ts // 2 - 1, 1 if face != 3 else -1, t)
#|    lcd.fill_rect(0, 0, W, 14, BG)
#|    lcd.text(hud, 4, 3, WHITE)
#|    for d, (x, y) in enumerate(((10, 24), (W - 10, 24), (W - 10, H - 10), (10, H - 10))):
#|        arrow(lcd, x, y, d, DIM, 4)
#|
#|
#|def l_time(f):
#|    s = f // 30
#|    return "%d:%02d" % (s // 60, s % 60)
#|
#|
#|def play(lcd, keys):
#|    best = SCORES.get("ladr_best", [0] * len(LEVELS))
#|    if len(best) != len(LEVELS):
#|        best = (best + [0] * len(LEVELS))[:len(LEVELS)]
#|    sel = 0
#|    for i in range(len(LEVELS)):
#|        if best[i]:
#|            sel = min(i + 1, len(LEVELS) - 1)
#|    while True:
#|        sel = l_select(lcd, keys, best, sel)
#|        if sel is None:
#|            return None
#|        res = l_level(lcd, keys, sel)
#|        if res:
#|            moves, frames = res
#|            if not best[sel] or moves < best[sel]:
#|                best[sel] = moves
#|            SCORES["ladr_best"] = best
#|            bt = SCORES.get("ladr_time", [0] * len(LEVELS))
#|            bt = (bt + [0] * len(LEVELS))[:len(LEVELS)]
#|            if not bt[sel] or frames < bt[sel]:
#|                bt[sel] = frames
#|            SCORES["ladr_time"] = bt
#|            save_scores()
#|            done = sum(1 for b in best if b)
#|            if done >= 5:
#|                goal("ladr", 0)
#|            if done >= 12:
#|                goal("ladr", 1)
#|            if done >= len(LEVELS):
#|                goal("ladr", 2)
#|            if sel < len(LEVELS) - 1:
#|                sel += 1
#|
#|
#|def l_select(lcd, keys, best, sel):
#|    stars = Stars(30)
#|    t = 0
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        unlocked = 0
#|        while unlocked < len(LEVELS) and best[unlocked]:
#|            unlocked += 1
#|        if keys.repeat(K0, 10, 4):
#|            sel = (sel - 1) % len(LEVELS)
#|        if keys.repeat(K1, 10, 4):
#|            sel = (sel + 1) % len(LEVELS)
#|        if keys.pressed(K2) and sel <= unlocked:
#|            keys.wait_release()
#|            return sel
#|        if keys.pressed(K3):
#|            return None
#|        gradient(lcd, L_BG)
#|        stars.draw(lcd)
#|        big(lcd, "LADOR", 12, 10, SHADOW, 3)
#|        big(lcd, "LADOR", 10, 8, AMBER, 3)
#|        done = sum(1 for b in best if b)
#|        rtext(lcd, "%d/%d klara" % (done, len(LEVELS)), W - 8, 12, GRAY)
#|        rtext(lcd, "0/1 valj 2 spela 3 ut", W - 8, 24, DIM)
#|        for i in range(len(LEVELS)):
#|            x = 14 + (i % 5) * 60
#|            y = 42 + (i // 5) * 40
#|            if i == sel:
#|                lcd.fill_rect(x - 3, y - 3, 58, 36, WHITE)
#|            if best[i]:
#|                c = rgb(90, 200, 110)
#|            elif i <= unlocked:
#|                c = AMBER
#|            else:
#|                c = LINE
#|            lcd.fill_rect(x, y, 52, 30, c)
#|            ctext(lcd, str(i + 1), y + 7, BG, 2, x + 26)
#|        p = LEVELS[sel][0]
#|        lcd.fill_rect(10, 206, 300, 30, PANEL)
#|        if sel > unlocked:
#|            ctext(lcd, "Klara banan innan forst", 216, AMBER)
#|        elif best[sel]:
#|            bt = SCORES.get("ladr_time", [0] * len(LEVELS))
#|            tt = bt[sel] if sel < len(bt) else 0
#|            ctext(lcd, "Basta: %d drag  %s  minst %d" % (best[sel], l_time(tt), p), 216, WHITE)
#|        else:
#|            ctext(lcd, "Ny bana! Minst %d knuffar." % p, 216, WHITE)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def l_level(lcd, keys, n):
#|    rows = LEVELS[n][1]
#|    walls, goals, boxes0, p0 = l_parse(rows)
#|    w, h = max(len(r) for r in rows), len(rows)
#|    ts = min(24, (W - 40) // w, (H - 24) // h)
#|    ox = (W - w * ts) // 2
#|    oy = 16 + (H - 16 - h * ts) // 2
#|    boxes, p = list(boxes0), p0
#|    hist = []
#|    moves = 0
#|    face = 1
#|    frames = 0
#|    parts = Particles(60)
#|    t = 0
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pause():
#|            r = l_menu(lcd, keys, rows, walls, goals, boxes, p, face, ts, ox, oy, hist)
#|            if r == "exit":
#|                return None
#|            if r == "restart":
#|                boxes, p, hist, moves, frames = list(boxes0), p0, [], 0, 0
#|            elif r:
#|                boxes, p, moves = r
#|        frames += 1
#|        for k in (K0, K1, K2, K3):
#|            if keys.repeat(k, 8, 3):
#|                dx, dy = DIRS4[k]
#|                face = k
#|                nxt = (p[0] + dx, p[1] + dy)
#|                if nxt in walls:
#|                    continue
#|                if nxt in boxes:
#|                    to = (nxt[0] + dx, nxt[1] + dy)
#|                    if to in walls or to in boxes:
#|                        continue
#|                    hist.append((p, list(boxes), moves))
#|                    boxes[boxes.index(nxt)] = to
#|                    if to in goals:
#|                        parts.burst(ox + to[0] * ts + ts // 2, oy + to[1] * ts + ts // 2, L_GOAL, 10, 2, 12)
#|                else:
#|                    hist.append((p, list(boxes), moves))
#|                p = nxt
#|                moves += 1
#|                break
#|        on = sum(1 for b in boxes if b in goals)
#|        hud = "BANA %d   DRAG %d   %s   %d/%d" % (n + 1, moves, l_time(frames), on, len(boxes))
#|        l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, hud)
#|        parts.draw(lcd)
#|        if on == len(boxes):
#|            for k in range(40):
#|                t1 = time.ticks_ms()
#|                l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t + k, hud)
#|                for _ in range(10):
#|                    lcd.fill_rect(random.randint(0, W - 3), random.randint(16, H - 3), 3, 3,
#|                                  random.choice(CONFETTI))
#|                stext(lcd, "KLART!", 90, LIME, 4)
#|                ctext(lcd, "%d drag  %s" % (moves, l_time(frames)), 140, WHITE, 2)
#|                lcd.show()
#|                wait(t1)
#|            return moves, frames
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def l_menu(lcd, keys, rows, walls, goals, boxes, p, face, ts, ox, oy, hist):
#|    """Paus-rutan: 0 ångra (flera gånger), 1 börja om, 2 fortsätt, 3 till banorna."""
#|    keys.wait_release()
#|    moves = None
#|    t = 0
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.repeat(K0, 10, 4) and hist:
#|            p, boxes, moves = hist.pop()
#|        if keys.pressed(K1):
#|            keys.wait_release()
#|            return "restart"
#|        if keys.pressed(K2):
#|            keys.wait_release()
#|            return (boxes, p, moves) if moves is not None else None
#|        if keys.pressed(K3):
#|            keys.wait_release()
#|            return "exit"
#|        l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, "PAUS")
#|        lcd.fill_rect(0, 0, W, 14, AMBER)
#|        lcd.text("0 angra  1 om  2 spela  3 banor", 6, 3, BG)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#@@ flode
#|# FLODE: koppla ihop prickarna med samma färg och fyll hela rutnätet.
#|#   0 upp, 1 höger, 2 ner, 3 vänster (pilarna i hörnen)
#|#   Gå in på en prick (eller slutet av en linje) så ritar du.
#|#   Tryck två knappar samtidigt för att lyfta/sänka pennan och gå fritt.
#|#   Håll alla fyra: 0 börja om, 2 fortsätt, 3 till banorna.
#|# Banorna skapas av en generator: en slingrande väg genom hela rutnätet
#|# klipps i bitar, och bitarnas ändar blir prickarna. Alltså går varje bana
#|# att lösa med alla rutor fyllda.
#|
#|F_RAW = ((235, 60, 60), (60, 120, 255), (60, 200, 80), (250, 220, 50), (255, 140, 30),
#|         (60, 220, 230), (240, 90, 200), (150, 80, 230), (225, 225, 225))
#|F_COL = [rgb(*c) for c in F_RAW]
#|F_DIM = [rgb(c[0] // 4, c[1] // 4, c[2] // 4) for c in F_RAW]
#|F_BG = [mix((10, 14, 30), (26, 12, 40), y / (H - 1)) for y in range(H)]
#|F_GRID = rgb(50, 56, 90)
#|NLEV = 25
#|F_SOL = [None]                  # senaste lösningen (används av testerna)
#|
#|
#|class Rng:
#|    """Egen enkel slump så att banorna blir likadana på Picon och datorn."""
#|    def __init__(self, s):
#|        self.s = (s * 7919 + 17) & 0xFFFFFF
#|
#|    def n(self, m):
#|        self.s = (self.s * 1103 + 12345) & 0xFFFFFF
#|        return (self.s >> 4) % m
#|
#|
#|def f_size(i):
#|    """Storlek och antal färger för bana i."""
#|    if i < 5:
#|        return 5, 4 + i % 2
#|    if i < 12:
#|        return 6, 5 + i % 2
#|    if i < 19:
#|        return 7, 6 + i % 2
#|    return 8, 7 + i % 2
#|
#|
#|def f_gen(w, k, rng):
#|    n = w * w
#|    while True:
#|        path = []
#|        for y in range(w):
#|            for x in range(w):
#|                path.append(y * w + (x if y % 2 == 0 else w - 1 - x))
#|        for _ in range(n * 10):
#|            if rng.n(2):
#|                path.reverse()
#|            e = path[0]
#|            dx, dy = DIRS4[rng.n(4)]
#|            nx, ny = e % w + dx, e // w + dy
#|            if 0 <= nx < w and 0 <= ny < w:
#|                i = path.index(ny * w + nx)
#|                if i > 1:
#|                    head = path[:i]
#|                    head.reverse()
#|                    path = head + path[i:]
#|        lens = [3] * k
#|        wt = [1 + rng.n(4) for _ in range(k)]
#|        for _ in range(n - 3 * k):
#|            r = rng.n(sum(wt))
#|            j = 0
#|            while r >= wt[j]:
#|                r -= wt[j]
#|                j += 1
#|            lens[j] += 1
#|        dots = []
#|        a = 0
#|        ok = True
#|        for L in lens:
#|            p, q = path[a], path[a + L - 1]
#|            if abs(p % w - q % w) + abs(p // w - q // w) <= 1:
#|                ok = False
#|            dots.append((p, q))
#|            a += L
#|        if ok:
#|            F_SOL[0] = (path, lens)
#|            return dots
#|
#|
#|def f_level(i):
#|    w, k = f_size(i)
#|    return w, f_gen(w, k, Rng(i * 31 + 5))
#|
#|
#|def play(lcd, keys):
#|    mode = choose(lcd, keys, "FLODE", ("BANOR", "TIDSJAKT"), PINK, "Koppla ihop lika farger")
#|    if mode is None:
#|        return None
#|    if mode == 1:
#|        return f_rush(lcd, keys)
#|    done = SCORES.get("flode_done", [0] * NLEV)
#|    done = (done + [0] * NLEV)[:NLEV]
#|    sel = 0
#|    while sel < NLEV - 1 and done[sel]:
#|        sel += 1
#|    while True:
#|        sel = f_select(lcd, keys, done, sel)
#|        if sel is None:
#|            return None
#|        while True:
#|            w, dots = f_level(sel)
#|            r = f_play(lcd, keys, w, dots, "BANA %d" % (sel + 1), None)
#|            if not r:
#|                break
#|            done[sel] = max(done[sel], r)
#|            SCORES["flode_done"] = done
#|            save_scores()
#|            c = sum(1 for d in done if d)
#|            if c >= 5:
#|                goal("flode", 0)
#|            if c >= 15:
#|                goal("flode", 1)
#|            if sel >= NLEV - 1:
#|                break
#|            sel += 1
#|
#|
#|def f_rush(lcd, keys):
#|    """TIDSJAKT: lös så många banor du hinner. Varje lösning ger mer tid."""
#|    rng = Rng(time.ticks_ms() & 0xFFFF)
#|    clock = [60 * 30]
#|    solved = 0
#|    while True:
#|        w = 5 if solved < 2 else 6 if solved < 5 else 7 if solved < 8 else 8
#|        k = w - 1 + rng.n(2)
#|        dots = f_gen(w, k, rng)
#|        r = f_play(lcd, keys, w, dots, "TIDSJAKT  %d LOSTA" % solved, clock)
#|        if r is None:
#|            return None
#|        if r == -1:
#|            return ("TIDEN UT!", solved, "flode_tid", "Losta banor:", False, str)
#|        solved += 1
#|        clock[0] += (12 if r == 2 else 8) * 30
#|        if solved >= 5:
#|            goal("flode", 2)
#|
#|
#|def f_select(lcd, keys, done, sel):
#|    stars = Stars(30)
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        unlocked = 0
#|        while unlocked < NLEV and done[unlocked]:
#|            unlocked += 1
#|        if keys.repeat(K0, 10, 4):
#|            sel = (sel - 1) % NLEV
#|        if keys.repeat(K1, 10, 4):
#|            sel = (sel + 1) % NLEV
#|        if keys.pressed(K2) and sel <= unlocked:
#|            keys.wait_release()
#|            return sel
#|        if keys.pressed(K3):
#|            return None
#|        gradient(lcd, F_BG)
#|        stars.draw(lcd)
#|        big(lcd, "FLODE", 12, 10, SHADOW, 3)
#|        big(lcd, "FLODE", 10, 8, PINK, 3)
#|        rtext(lcd, "%d/%d klara" % (sum(1 for d in done if d), NLEV), W - 8, 12, GRAY)
#|        rtext(lcd, "0/1 valj 2 spela 3 ut", W - 8, 24, DIM)
#|        for i in range(NLEV):
#|            x = 14 + (i % 5) * 60
#|            y = 40 + (i // 5) * 33
#|            if i == sel:
#|                lcd.fill_rect(x - 3, y - 3, 58, 30, WHITE)
#|            c = YELLOW if done[i] == 2 else rgb(90, 200, 110) if done[i] else PINK if i <= unlocked else LINE
#|            lcd.fill_rect(x, y, 52, 24, c)
#|            ctext(lcd, str(i + 1), y + 4, BG, 2, x + 26)
#|        w, k = f_size(sel)
#|        lcd.fill_rect(10, 208, 300, 26, PANEL)
#|        if sel > unlocked:
#|            ctext(lcd, "Klara banan innan forst", 217, AMBER)
#|        else:
#|            txt = "%dx%d  %d farger" % (w, w, k)
#|            if done[sel] == 2:
#|                txt += "  PERFEKT"
#|            elif done[sel]:
#|                txt += "  klar"
#|            ctext(lcd, txt, 217, WHITE)
#|        lcd.show()
#|        wait(t0)
#|
#|
#|def f_draw(lcd, w, dots, paths, occ, cur, pen, ox, oy, s, t, hud):
#|    gradient(lcd, F_BG)
#|    for c in range(w * w):
#|        k = occ[c]
#|        x, y = ox + (c % w) * s, oy + (c // w) * s
#|        if k >= 0:
#|            lcd.fill_rect(x + 1, y + 1, s - 1, s - 1, F_DIM[k])
#|    for i in range(w + 1):
#|        lcd.hline(ox, oy + i * s, w * s, F_GRID)
#|        lcd.vline(ox + i * s, oy, w * s, F_GRID)
#|    lw = max(4, s // 3)
#|    h2 = s // 2
#|    for k, p in enumerate(paths):
#|        col = F_COL[k]
#|        for j in range(1, len(p)):
#|            a, b = p[j - 1], p[j]
#|            ax, ay = ox + (a % w) * s + h2, oy + (a // w) * s + h2
#|            bx, by = ox + (b % w) * s + h2, oy + (b // w) * s + h2
#|            lcd.fill_rect(min(ax, bx) - lw // 2, min(ay, by) - lw // 2,
#|                          abs(ax - bx) + lw, abs(ay - by) + lw, col)
#|    r = s * 3 // 10
#|    for k, (a, b) in enumerate(dots):
#|        for c in (a, b):
#|            lcd.ellipse(ox + (c % w) * s + h2, oy + (c // w) * s + h2, r, r, F_COL[k], True)
#|    cx, cy = ox + (cur % w) * s, oy + (cur // w) * s
#|    if pen >= 0:
#|        cc = F_COL[pen]
#|        lcd.rect(cx - 1, cy - 1, s + 3, s + 3, cc)
#|        lcd.rect(cx, cy, s + 1, s + 1, WHITE if (t // 4) % 2 else cc)
#|    else:
#|        lcd.rect(cx, cy, s + 1, s + 1, WHITE)
#|        lcd.rect(cx + 1, cy + 1, s - 1, s - 1, WHITE)
#|    lcd.fill_rect(0, 0, W, 14, BG)
#|    lcd.text(hud, 4, 3, WHITE)
#|    for d, (x, y) in enumerate(((10, 24), (W - 10, 24), (W - 10, H - 10), (10, H - 10))):
#|        arrow(lcd, x, y, d, DIM, 4)
#|    ctext(lcd, "2 knappar samtidigt = lyft pennan", 231, DIM)
#|
#|
#|def f_play(lcd, keys, w, dots, title, clock):
#|    """Spelar en bana. Svar: 1 klar, 2 perfekt, None avbruten, -1 tiden slut."""
#|    n = w * w
#|    s = min(38, (H - 34) // w)
#|    ox = (W - w * s) // 2
#|    oy = 16 + (H - 16 - w * s) // 2
#|    dot_at = {}
#|    for k, (a, b) in enumerate(dots):
#|        dot_at[a] = k
#|        dot_at[b] = k
#|    paths = [[] for _ in dots]
#|    occ = [-1] * n
#|    cur = dots[0][0]
#|    pen = -1
#|    snap = None
#|    snap_t = -99
#|    parts = Particles(60)
#|    t = 0
#|    keys.wait_release()
#|
#|    def complete(k):
#|        p = paths[k]
#|        return len(p) > 1 and p[0] in dot_at and p[-1] in dot_at and p[0] != p[-1]
#|
#|    def engage(c):
#|        # Gå in på en prick eller ett linjeslut: pennan tar den färgen.
#|        for k, p in enumerate(paths):
#|            if len(p) > 1 and p[-1] == c:
#|                return k
#|        k = dot_at.get(c, -1)
#|        if k >= 0 and (not paths[k] or len(paths[k]) == 1):
#|            paths[k] = [c]
#|            return k
#|        return -1
#|
#|    pen = engage(cur)
#|
#|    def pos(c):
#|        return ox + (c % w) * s + s // 2, oy + (c // w) * s + s // 2
#|
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if clock is not None:
#|            clock[0] -= 1
#|            if clock[0] <= 0:
#|                for _ in range(45):
#|                    t1 = time.ticks_ms()
#|                    f_draw(lcd, w, dots, paths, occ, cur, -1, ox, oy, s, t, title)
#|                    stext(lcd, "TIDEN UT!", 100, CORAL, 4)
#|                    lcd.show()
#|                    wait(t1)
#|                return -1
#|        if keys.pause():
#|            r = f_pause(lcd, keys)
#|            if r == "exit":
#|                return None
#|            if r == "restart":
#|                paths = [[] for _ in dots]
#|                pen = -1
#|        held = sum(keys.now)
#|        if held == 2 and sum(keys.prev) < 2:
#|            # två knappar samtidigt: lyft/sänk pennan (ångra steget den första gav)
#|            if snap and t - snap_t <= 5:
#|                cur, pen, paths = snap
#|            pen = -1 if pen >= 0 else engage(cur)
#|            snap = None
#|        for d in (K0, K1, K2, K3):
#|            if held != 1 or not keys.repeat(d, 7, 3):
#|                continue
#|            dx, dy = DIRS4[d]
#|            x, y = cur % w + dx, cur // w + dy
#|            if not (0 <= x < w and 0 <= y < w):
#|                break
#|            nc = y * w + x
#|            snap = (cur, pen, [list(q) for q in paths])
#|            snap_t = t
#|            if pen >= 0:
#|                p = paths[pen]
#|                if len(p) >= 2 and nc == p[-2]:
#|                    p.pop()
#|                    cur = nc
#|                elif nc in p:
#|                    paths[pen] = p[:p.index(nc) + 1]
#|                    cur = nc
#|                elif dot_at.get(nc, pen) != pen or complete(pen):
#|                    pen = -1                    # annan prick / klar linje: lyft pennan
#|                    cur = nc
#|                    pen = engage(nc)
#|                else:
#|                    j = occ[nc]
#|                    if j >= 0 and j != pen:     # skär av en annan linje
#|                        q = paths[j]
#|                        paths[j] = q[:q.index(nc)]
#|                    p.append(nc)
#|                    cur = nc
#|                    if dot_at.get(nc) == pen:
#|                        x2, y2 = pos(nc)
#|                        parts.burst(x2, y2, F_COL[pen], 12, 2.5, 14)
#|                        pen = -1
#|            else:
#|                cur = nc
#|                pen = engage(nc)
#|            break
#|        occ = [-1] * n
#|        for k, p in enumerate(paths):
#|            for c in p:
#|                occ[c] = k
#|        fills = sum(1 for c in occ if c >= 0)
#|        hud = "%s  %d%%" % (title, fills * 100 // n)
#|        f_draw(lcd, w, dots, paths, occ, cur, pen, ox, oy, s, t, hud)
#|        if clock is not None:
#|            sec = clock[0] // 30
#|            rtext(lcd, "%d:%02d" % (sec // 60, sec % 60), W - 4, 3, CORAL if sec < 10 else WHITE)
#|        parts.draw(lcd)
#|        if all(complete(k) for k in range(len(dots))):
#|            perfect = fills == n
#|            for f in range(30 if clock is not None else 45):
#|                t1 = time.ticks_ms()
#|                f_draw(lcd, w, dots, paths, occ, cur, -1, ox, oy, s, t + f, hud)
#|                if perfect:
#|                    for _ in range(8):
#|                        lcd.fill_rect(random.randint(0, W - 3), random.randint(16, H - 3), 3, 3,
#|                                      random.choice(CONFETTI))
#|                stext(lcd, "PERFEKT!" if perfect else "KLART!", 92, LIME if perfect else SKY, 4)
#|                if not perfect:
#|                    ctext(lcd, "Fyll alla rutor for PERFEKT", 136, WHITE)
#|                lcd.show()
#|                wait(t1)
#|            return 2 if perfect else 1
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def f_pause(lcd, keys):
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pressed(K0):
#|            keys.wait_release()
#|            return "restart"
#|        if keys.pressed(K2):
#|            keys.wait_release()
#|            return None
#|        if keys.pressed(K3):
#|            keys.wait_release()
#|            return "exit"
#|        lcd.fill_rect(40, 70, 240, 100, PANEL)
#|        lcd.rect(40, 70, 240, 100, PINK)
#|        ctext(lcd, "PAUS", 82, PINK, 2)
#|        ctext(lcd, "0 borja om", 110, WHITE)
#|        ctext(lcd, "2 fortsatt", 126, WHITE)
#|        ctext(lcd, "3 till banorna", 142, WHITE)
#|        lcd.show()
#|        wait(t0)
#@@ aventyr
#|# AVENTYR: plattformsspel med 8 banor.
#|#   0 vänster, 1 höger, 2 hoppa (håll = högre), 3 dash (krossar sprickor och monster)
#|#   Ta mynt och de 3 ädelstenarna på varje bana. Flaggor = kontrollpunkter.
#|#   Håll alla fyra: paus (2 fortsätt, 3 till banorna).
#|# Banorna byggs av verktyg/gen_aventyr.py, som också kollar att allt går att nå.
#|
#|AV_LEVELS = (
#|    ('ANGEN', 0, '0/1 spring  2 hoppa', (
#|        '                                                                                                ',
#|        '                                                                                                ',
#|        '                                                                                                ',
#|        '                                                                                                ',
#|        '                                                                     G                          ',
#|        '                                                                  ======                        ',
#|        '                                                                                                ',
#|        '                                                                   oooo                 G       ',
#|        '                              ooo     G           oooooooo        ######                        ',
#|        '                                    =====                         ######        oooo    B       ',
#|        '     ooooo                w                 B               ############               BB       ',
#|        '  P                 ##########             BB  C    w    w  ############    w         BB     E  ',
#|        '##############################   ###############################################    ############',
#|        '##############################   ###############################################^^^^############',
#|        '##############################   ###############################################################',
#|    )),
#|    ('GROTTAN', 1, '3 = dash! Krossar sprickor', (
#|        '####################################################################################################',
#|        '####################################################################################################',
#|        '####################################################################################################',
#|        '            XX   #######                                                                   XX       ',
#|        '            XX   #######                                                         G         XX       ',
#|        '            XX   #######                                                                   XX       ',
#|        '            XX   #######                                                                   XX       ',
#|        '            XX   #######         G                               o                         XX       ',
#|        '            XX   #######      ======    XXXXX   ooooo        o       o                     XX       ',
#|        '            XX   #######       oooo     X   X                    B                         XX       ',
#|        '    ooooo   XX                ######    X   X                B   B   B                     XX       ',
#|        '  P         XX            C   ######  w X G X     k          B   B   B     C     S      k  XX   E   ',
#|        '##################^^^^####################################^^^^^^^^^^^^^^^###########################',
#|        '####################################################################################################',
#|        '####################################################################################################',
#|    )),
#|    ('MOLNEN', 2, 'Ramla inte ner!', (
#|        '                                                                                                    ',
#|        '                                                                                                    ',
#|        '                                                                                                    ',
#|        '                                     G                                                              ',
#|        '                                 ======                                                             ',
#|        '                                                     f                                              ',
#|        '                                          f   ooo                              G               G    ',
#|        '                 oooo                         ===                                                   ',
#|        '                 ====                                                         ccc           =====   ',
#|        '           oooo        ====             ====       ====                                  ooo        ',
#|        '  P        ====                C  w S                    ====            ccc       ccc            E ',
#|        '#########                    ########                           C    k                  ############',
#|        '#########                    ########                         #########                 ############',
#|        '#########                    ########                         #########                 ############',
#|        '#########                    ########                         #########                 ############',
#|    )),
#|    ('SKOGEN', 3, 'Hoppa pa monstren', (
#|        '                                                                                                              ',
#|        '                                                                                                              ',
#|        '                                                                                                              ',
#|        '                                                                                                              ',
#|        '                      G                                   G                                                   ',
#|        '                                                                                                              ',
#|        '                    =====                               =====                         BB      =====           ',
#|        '                      T                                   T                           XX        T             ',
#|        '      ooooo           T                           ooooo   T                           XX BBB    T             ',
#|        '      =====        =========== w      =====       ccccc=======                =====   XX     =======oooo      ',
#|        '        T             T       ####      T                 T                     T     XX        T             ',
#|        '  P     T     w   w   T       ####      T   C   k   w     T   w   w   k       C T     XX  G     T   w     E   ',
#|        '##################################    ##################################    ##################################',
#|        '##################################^^^^##################################^^^^##################################',
#|        '##############################################################################################################',
#|    )),
#|    ('ISEN', 4, 'Det ar halt!', (
#|        '                                                                                                    ',
#|        '                                                                                                    ',
#|        '                                                                                                    ',
#|        '                                                              XX                                    ',
#|        '                               G                              XX   G                  ooooGo        ',
#|        '                            =====                             XX  ====                ======        ',
#|        '                                                              XX                                    ',
#|        '                                                              XX                                    ',
#|        '                          IIII                       o        XX                                    ',
#|        '                          IIII                      BB        XX      IIII                          ',
#|        '     ooooooo          IIIIIIII                                XX   f  IIII                          ',
#|        '  P                   IIIIIIII      C   w    k            C   XX      IIII          S   k       E   ',
#|        'IIIIIIIIIIIIII    IIIIIIIIIIII    IIIIIIIIIIIIIIII      IIIIIIIIIIIIIIIIIIII    IIIIIIIIIIIIIIIIIIII',
#|        'IIIIIIIIIIIIII^^^^IIIIIIIIIIII^^^^IIIIIIIIIIIIIIII^^^^^^IIIIIIIIIIIIIIIIIIII^^^^IIIIIIIIIIIIIIIIIIII',
#|        'IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII',
#|    )),
#|    ('VULKANEN', 5, 'Akta lavan!', (
#|        '                                                                                                    ',
#|        '                                                                                                    ',
#|        '                                                          G                                         ',
#|        '                                                       =====                                        ',
#|        '                                                                                    XX              ',
#|        '                                         G                                          XX              ',
#|        '                                                               foooooooooooo        XX              ',
#|        '                                        cc                                          XX  G           ',
#|        '               oo          oooooo                                    cc             XX BBB          ',
#|        '               cc                   cc      cc            BBB   BBB      BBB        XX              ',
#|        '  P       BBB      BBB    C   k                   C  w S                        C   XX       k   E  ',
#|        '########                ##########              ########                      ########    ##########',
#|        '########                ##########              ########                      ########    ##########',
#|        '########LLLLLLLLLLLLLLLL##########LLLLLLLLLLLLLL########LLLLLLLLLLLLLLLLLLLLLL########LLLL##########',
#|        '########LLLLLLLLLLLLLLLL##########LLLLLLLLLLLLLL########LLLLLLLLLLLLLLLLLLLLLL########LLLL##########',
#|    )),
#|    ('BORGEN', 6, 'Dasha igelkottarna', (
#|        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
#|        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
#|        '        BB      XX                                                  BBBBBB      XX                            ',
#|        '        BB      XX                                                  BBBBBB      XX                            ',
#|        '        BB      XX                                                  BBBBBB      XX                            ',
#|        '        BB      XX                   G                              BBBBBB      XX                            ',
#|        '        BB      XX               f BBBB      f                      BBBBBB      XX        f                   ',
#|        '        BB      XX                         o   o   o                BBBBBB      XX       o     o    G         ',
#|        '        BB      XX                                                  BBBBBB      XX    o     o     BBBB        ',
#|        '                XX  oooooo    BBBB         B   B   B    oooooooooo  ^^^^^^      XX       c     c              ',
#|        '                XX                                                              XX    c     c                 ',
#|        '  P          k  XX          C                         C   k   w  k     G     C  XX                      k  E  ',
#|        'BBBBBBBBBBBBBBBBBBBBB^^^^BBBBBBBBBBBBBBB^^^^^^^^^^^^BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB^^^^^^^^^^^^BBBBBBBBBBBBBB',
#|        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
#|        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
#|    )),
#|    ('TOPPEN', 7, 'Allt pa en gang!', (
#|        '                                                                                                                        ',
#|        '                                                                                                                        ',
#|        '                                                    XX                                                                  ',
#|        '         oooo                                       XX             G                                    XX              ',
#|        '        ======                                      XX          ======                                  XX              ',
#|        '                      f                             XX                           f                      XX              ',
#|        '                ccc                    G            XX                  oofoooooooooo                   XX    G         ',
#|        '                                                    XX                                                  XX  BBBB        ',
#|        '                     ===                            XX                       ===                        XX              ',
#|        '                                       B            XX   cccc                                           XX              ',
#|        '                            C  k    B     B     C   XX w          S  k  ===       ===   C   w k         XX      w   E   ',
#|        '  P     S                 IIIIIIII            ##########      ########                ##########    ####################',
#|        '##########                IIIIIIII            ##########      ########                ##########    ####################',
#|        '##########                IIIIIIIILLLLLLLLLLLL##########^^^^^^########LLLLLLLLLLLLLLLL##########^^^^####################',
#|        '##########                IIIIIIIILLLLLLLLLLLL########################LLLLLLLLLLLLLLLL##################################',
#|    )),
#|)
#|
#|TS = 16
#|PW, PH = 10, 14
#|AV_PAL = (   # himmel uppe, himmel nere, mark, mörk mark, gräs/topp, kullar, planka
#|    ((90, 160, 255), (200, 230, 255), (150, 95, 50), (105, 62, 32), (90, 200, 70), (120, 190, 130), (170, 120, 70)),
#|    ((16, 12, 26), (46, 34, 62), (92, 80, 104), (58, 48, 70), (140, 128, 160), (34, 26, 46), (150, 120, 90)),
#|    ((110, 165, 255), (250, 205, 225), (236, 236, 250), (190, 190, 216), (255, 255, 255), (255, 232, 244), (255, 255, 255)),
#|    ((40, 90, 60), (150, 200, 120), (110, 75, 40), (78, 50, 26), (70, 170, 60), (40, 110, 60), (60, 150, 60)),
#|    ((150, 200, 255), (232, 245, 255), (200, 222, 242), (150, 172, 202), (250, 255, 255), (184, 212, 240), (170, 120, 70)),
#|    ((60, 10, 12), (170, 64, 22), (84, 52, 50), (52, 30, 30), (130, 74, 60), (96, 30, 22), (110, 110, 120)),
#|    ((26, 26, 56), (92, 82, 124), (120, 120, 140), (80, 80, 100), (160, 160, 182), (50, 50, 82), (150, 120, 90)),
#|    ((10, 10, 40), (84, 40, 124), (100, 80, 140), (70, 50, 100), (200, 150, 255), (40, 30, 82), (200, 150, 255)),
#|)
#|# Vilka tecken som är fasta block
#|AV_SOLID = bytearray(128)
#|for _c in "#BXcI":
#|    AV_SOLID[ord(_c)] = 1
#|AV_TOP = bytearray(AV_SOLID)        # går att stå på
#|AV_TOP[ord("=")] = 1
#|AV_TOP[ord("S")] = 1
#|C_SP, C_X, C_CR, C_PL, C_ICE, C_SPK, C_LAVA, C_SPR = 32, 88, 99, 61, 73, 94, 76, 83
#|C_COIN, C_GEM, C_CHK, C_EXIT = 111, 71, 67, 69
#|STONE = (rgb(132, 132, 148), rgb(176, 176, 192), rgb(84, 84, 100))
#|CRACK = (rgb(156, 104, 62), rgb(96, 60, 32))
#|CRUMB = (rgb(226, 196, 136), rgb(170, 140, 90))
#|ICE = (rgb(190, 226, 255), rgb(240, 250, 255), rgb(140, 180, 220))
#|LAVA = (rgb(255, 110, 20), rgb(255, 220, 60))
#|SPIKE = rgb(220, 220, 236)
#|GEMC = rgb(60, 255, 210)
#|TRUNK = rgb(96, 62, 30)
#|
#|
#|def gem(fb, x, y, r, c):
#|    tri(fb, x - r, y, x + r, y, x, y - r, c)
#|    tri(fb, x - r, y, x + r, y, x, y + r + r // 2, c)
#|    fb.line(x - r // 2, y - r // 2, x, y - r + 1, WHITE)
#|
#|
#|class AvLevel:
#|    def __init__(self, n):
#|        name, pal, hint, rows = AV_LEVELS[n]
#|        self.name, self.hint = name, hint
#|        self.w = len(rows[0])
#|        self.g = [bytearray(r.encode()) for r in rows]
#|        self.enemies = []
#|        self.coins = 0
#|        for ty in range(len(rows)):
#|            row = self.g[ty]
#|            for tx in range(self.w):
#|                ch = row[tx]
#|                if ch == 80:                        # P
#|                    self.start = (tx * TS + 3, ty * TS + 2)
#|                    row[tx] = C_SP
#|                elif ch in (119, 107):              # w, k
#|                    self.enemies.append([tx * TS + 1.0, ty * TS + 4.0, -0.8 if ch == 119 else -0.6, ch, True, 0, 0])
#|                    row[tx] = C_SP
#|                elif ch == 102:                     # f
#|                    self.enemies.append([tx * TS + 1.0, ty * TS + 2.0, 0, ch, True, tx * TS, ty * TS])
#|                    row[tx] = C_SP
#|                elif ch == C_COIN:
#|                    self.coins += 1
#|        p = AV_PAL[pal]
#|        self.pal = pal
#|        self.bg = [mix(p[0], p[1], y / (H - 1)) for y in range(H)]
#|        self.dirt, self.dark, self.top = rgb(*p[2]), rgb(*p[3]), rgb(*p[4])
#|        self.hill, self.plank = rgb(*p[5]), rgb(*p[6])
#|        self.cache = av_cache(self)
#|        self.hills = bytearray(64)
#|        for i in range(64):
#|            a = i * 6.2832 / 64
#|            self.hills[i] = 50 + int(22 * math.sin(a * 2 + pal) + 14 * math.sin(a * 5 + 1))
#|
#|    def at(self, tx, ty):
#|        if tx < 0 or tx >= self.w:
#|            return 66
#|        if ty < 0 or ty >= 15:
#|            return C_SP
#|        return self.g[ty][tx]
#|
#|
#|KEY = rgb(255, 0, 255)                  # genomskinlig färg i förritade brickor
#|
#|
#|def av_cache(lv):
#|    """Förritar brickorna (16x16) en gång per bana, så blir det en blit per bricka."""
#|    out = []
#|    for i in range(13):
#|        buf = bytearray(TS * TS * 2)
#|        f = framebuf.FrameBuffer(buf, TS, TS, framebuf.RGB565)
#|        f.fill(KEY)
#|        if i <= 2:                                          # mark: topp, mitt, mitt 2
#|            f.fill(lv.dirt)
#|            if i == 0:
#|                f.fill_rect(0, 0, TS, 4, lv.top)
#|                f.fill_rect(0, 4, TS, 1, lv.dark)
#|            if i != 2:
#|                f.fill_rect(5, 8, 2, 2, lv.dark)
#|            f.fill_rect(11, 12, 2, 2, lv.dark)
#|        elif i <= 4:                                        # sten (två mönster)
#|            f.fill(STONE[0])
#|            f.hline(0, 0, TS, STONE[1])
#|            f.vline(0, 0, TS, STONE[1])
#|            f.hline(0, 15, TS, STONE[2])
#|            f.vline(15, 0, TS, STONE[2])
#|            f.hline(1, 8, 14, STONE[2])
#|            f.vline(4 if i == 3 else 11, 1, 7, STONE[2])
#|        elif i == 5:                                        # spricka
#|            f.fill(CRACK[0])
#|            f.rect(0, 0, TS, TS, CRACK[1])
#|            f.line(3, 3, 8, 9, CRACK[1])
#|            f.line(8, 9, 12, 5, CRACK[1])
#|            f.line(8, 9, 7, 14, CRACK[1])
#|        elif i == 6:                                        # smular
#|            f.fill_rect(0, 0, TS, 9, CRUMB[0])
#|            f.hline(0, 8, TS, CRUMB[1])
#|            f.fill_rect(3, 3, 2, 2, CRUMB[1])
#|            f.fill_rect(10, 5, 2, 2, CRUMB[1])
#|        elif i == 7:                                        # planka / moln
#|            if lv.pal == 2:
#|                f.ellipse(8, 4, 9, 5, WHITE, True)
#|            else:
#|                f.fill_rect(0, 0, TS, 5, lv.plank)
#|                f.hline(0, 5, TS, lv.dark)
#|        elif i <= 9:                                        # is: topp, mitt
#|            f.fill(ICE[0])
#|            if i == 8:
#|                f.fill_rect(0, 0, TS, 3, ICE[1])
#|            f.line(3, 12, 9, 6, ICE[2])
#|        elif i == 10:                                       # spikar
#|            for k in range(3):
#|                tri(f, k * 5, 15, k * 5 + 5, 15, k * 5 + 2, 6, SPIKE)
#|        elif i == 11:                                       # lava
#|            f.fill(LAVA[0])
#|        else:                                               # trädstam
#|            f.fill_rect(5, 0, 6, TS, TRUNK)
#|        out.append(f)
#|    return out
#|
#|
#|@native
#|def av_tiles(lcd, lv, cam, t, crum, flags):
#|    c0 = cam // TS
#|    g = lv.g
#|    w = lv.w
#|    cc = lv.cache
#|    for ty in range(15):
#|        row = g[ty]
#|        up = g[ty - 1] if ty else None
#|        y = ty * TS
#|        for tx in range(c0, c0 + 21):
#|            if tx >= w:
#|                break
#|            ch = row[tx]
#|            if ch == 32:
#|                continue
#|            x = tx * TS - cam
#|            if ch == 35:                                    # mark
#|                if ty == 0 or not AV_SOLID[up[tx]]:
#|                    lcd.blit(cc[0], x, y)
#|                else:
#|                    lcd.blit(cc[1 if (tx * 7 + ty * 3) % 4 == 0 else 2], x, y)
#|            elif ch == 66:                                  # sten
#|                lcd.blit(cc[3 + ty % 2], x, y)
#|            elif ch == 88:                                  # spricka
#|                lcd.blit(cc[5], x, y)
#|            elif ch == 99:                                  # smular
#|                k = crum.get(tx + ty * 1000, 0)
#|                lcd.blit(cc[6], x + ((t % 3) - 1 if k else 0), y, KEY)
#|            elif ch == 61:                                  # planka / moln
#|                lcd.blit(cc[7], x, y, KEY)
#|            elif ch == 73:                                  # is
#|                lcd.blit(cc[8 if ty == 0 or not AV_SOLID[up[tx]] else 9], x, y)
#|            elif ch == 94:                                  # spikar
#|                lcd.blit(cc[10], x, y, KEY)
#|            elif ch == 76:                                  # lava
#|                lcd.blit(cc[11], x, y)
#|                if ty == 0 or up[tx] != 76:
#|                    lcd.fill_rect(x + ((t // 3 + tx * 5) % 12), y, 5, 2, LAVA[1])
#|            elif ch == 84:                                  # trädstam
#|                lcd.blit(cc[12], x, y, KEY)
#|            elif ch == 83:                                  # fjäder
#|                lcd.fill_rect(x + 2, y + 13, 12, 3, STONE[2])
#|                lcd.line(x + 4, y + 13, x + 12, y + 10, GRAY)
#|                lcd.line(x + 12, y + 10, x + 4, y + 7, GRAY)
#|                lcd.fill_rect(x + 1, y + 4, 14, 3, CORAL)
#|            elif ch == 111:                                 # mynt
#|                r = int(5 * abs(math.sin(t * 0.12 + tx)))
#|                lcd.ellipse(x + 8, y + 8, r + 1, 6, YELLOW, True)
#|                if r > 2:
#|                    lcd.ellipse(x + 8, y + 8, r - 2, 3, AMBER, True)
#|            elif ch == 71:                                  # ädelsten
#|                gem(lcd, x + 8, y + 7 + int(2 * math.sin(t * 0.15)), 6, GEMC)
#|            elif ch == 67:                                  # flagga
#|                lcd.vline(x + 3, y - 6, 22, GRAY)
#|                c = LIME if (tx + ty * 1000) in flags else CORAL
#|                wv = 1 if (t // 6) % 2 else 0
#|                tri(lcd, x + 4, y - 6, x + 4, y + 3, x + 13, y - 2 + wv, c)
#|            elif ch == 69:                                  # dörr
#|                lcd.fill_rect(x, y - 12, TS, 28, rgb(120, 70, 30))
#|                lcd.ellipse(x + 8, y - 12, 8, 6, rgb(120, 70, 30), True)
#|                lcd.fill_rect(x + 3, y - 10, 10, 26, rgb(60, 30, 10))
#|                lcd.fill_rect(x + 10, y + 4, 2, 2, YELLOW)
#|                if (t // 8) % 2:
#|                    lcd.pixel(x + 8 + (t % 7) - 3, y - 18, YELLOW)
#|
#|
#|def av_enemy(lcd, e, cam, t):
#|    x, y = int(e[0]) - cam, int(e[1])
#|    if x < -20 or x > W + 4:
#|        return
#|    k = e[3]
#|    if k == 119:                                            # vandrare (svamp)
#|        lcd.ellipse(x + 7, y + 5, 8, 5, CORAL, True)
#|        lcd.fill_rect(x + 3, y + 1, 3, 2, WHITE)
#|        lcd.fill_rect(x + 3, y + 6, 8, 5, rgb(250, 220, 180))
#|        lcd.fill_rect(x + 4, y + 7, 2, 2, BLACK)
#|        lcd.fill_rect(x + 9, y + 7, 2, 2, BLACK)
#|        s = (t // 5) % 2
#|        lcd.fill_rect(x + 2 + s, y + 11, 4, 2, rgb(80, 50, 30))
#|        lcd.fill_rect(x + 9 - s, y + 11, 4, 2, rgb(80, 50, 30))
#|    elif k == 107:                                          # igelkott
#|        for i in range(4):
#|            tri(lcd, x + i * 3, y + 5, x + i * 3 + 5, y + 5, x + i * 3 + 2, y - 1 - (i % 2) * 2, rgb(200, 200, 220))
#|        lcd.ellipse(x + 7, y + 7, 7, 5, VIOLET, True)
#|        ex = x + (3 if e[2] < 0 else 10)
#|        lcd.fill_rect(ex, y + 6, 2, 2, WHITE)
#|        lcd.fill_rect(x + 3, y + 11, 3, 2, BLACK)
#|        lcd.fill_rect(x + 9, y + 11, 3, 2, BLACK)
#|    else:                                                   # fladdermus
#|        fl = 4 if (t // 4) % 2 else -3
#|        tri(lcd, x + 6, y + 6, x - 4, y + 2 + fl, x + 2, y + 9, rgb(70, 40, 110))
#|        tri(lcd, x + 8, y + 6, x + 18, y + 2 + fl, x + 12, y + 9, rgb(70, 40, 110))
#|        lcd.ellipse(x + 7, y + 7, 5, 5, rgb(110, 60, 160), True)
#|        lcd.fill_rect(x + 4, y + 5, 2, 2, YELLOW)
#|        lcd.fill_rect(x + 9, y + 5, 2, 2, YELLOW)
#|
#|
#|def av_time(f):
#|    s = f // 30
#|    return "%d:%02d" % (s // 60, s % 60)
#|
#|
#|def play(lcd, keys):
#|    n = len(AV_LEVELS)
#|    best = SCORES.get("av_time", [0] * n)
#|    gems = SCORES.get("av_gem", [0] * n)
#|    best = (best + [0] * n)[:n]
#|    gems = (gems + [0] * n)[:n]
#|    sel = 0
#|    while sel < n - 1 and best[sel]:
#|        sel += 1
#|    while True:
#|        sel = av_select(lcd, keys, best, gems, sel)
#|        if sel is None:
#|            return None
#|        res = av_run(lcd, keys, sel)
#|        if res:
#|            frames, gotgems = res
#|            if not best[sel] or frames < best[sel]:
#|                best[sel] = frames
#|            gems[sel] |= gotgems
#|            SCORES["av_time"] = best
#|            SCORES["av_gem"] = gems
#|            save_scores()
#|            if sel >= 1:
#|                goal("aventyr", 0)
#|            if gotgems == 7:
#|                goal("aventyr", 1)
#|            if all(best):
#|                goal("aventyr", 2)
#|            if sel < n - 1:
#|                sel += 1
#|
#|
#|def av_select(lcd, keys, best, gems, sel):
#|    n = len(AV_LEVELS)
#|    stars = Stars(30)
#|    t = 0
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        unlocked = 0
#|        while unlocked < n and best[unlocked]:
#|            unlocked += 1
#|        if keys.repeat(K0, 10, 4):
#|            sel = (sel - 1) % n
#|        if keys.repeat(K1, 10, 4):
#|            sel = (sel + 1) % n
#|        if keys.pressed(K2) and sel <= unlocked:
#|            keys.wait_release()
#|            return sel
#|        if keys.pressed(K3):
#|            return None
#|        gradient(lcd, theme_bg())
#|        stars.draw(lcd)
#|        big(lcd, "AVENTYR", 12, 10, SHADOW, 3)
#|        big(lcd, "AVENTYR", 10, 8, LIME, 3)
#|        rtext(lcd, "0/1 valj", W - 8, 10, GRAY)
#|        rtext(lcd, "2 spela 3 ut", W - 8, 22, GRAY)
#|        for i in range(n):
#|            x = 8 + (i % 4) * 78
#|            y = 42 + (i // 4) * 84
#|            p = AV_PAL[AV_LEVELS[i][1]]
#|            open_ = i <= unlocked
#|            if i == sel:
#|                lcd.fill_rect(x - 3, y - 3, 76, 80, WHITE)
#|            for yy in range(0, 74, 4):
#|                lcd.fill_rect(x, y + yy, 70, 4, mix(p[0], p[1], yy / 74) if open_ else LINE)
#|            if open_:
#|                lcd.fill_rect(x, y + 56, 70, 18, rgb(*p[2]))
#|                lcd.fill_rect(x, y + 56, 70, 3, rgb(*p[4]))
#|            ctext(lcd, str(i + 1), y + 6, BG if open_ else DIM, 3, x + 35)
#|            ctext(lcd, AV_LEVELS[i][0], y + 34, WHITE if open_ else DIM, 1, x + 35)
#|            for k in range(3):
#|                c = GEMC if gems[i] & (1 << k) else (SHADOW if open_ else LINE)
#|                gem(lcd, x + 21 + k * 14, y + 64, 4, c)
#|        lcd.fill_rect(8, 214, 304, 22, PANEL)
#|        if sel > unlocked:
#|            ctext(lcd, "Klara banan innan forst", 221, AMBER)
#|        elif best[sel]:
#|            ctext(lcd, "%s   Basta tid %s" % (AV_LEVELS[sel][0], av_time(best[sel])), 221, WHITE)
#|        else:
#|            ctext(lcd, "%s   Ny bana!" % AV_LEVELS[sel][0], 221, WHITE)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|class NoFx:
#|    """Tomma effekter (används när spelet räknas utan skärm, t.ex. i tester)."""
#|    def burst(self, *a):
#|        pass
#|
#|    def add(self, *a):
#|        pass
#|
#|    def hit(self, *a):
#|        pass
#|
#|
#|class Av:
#|    """Allt som händer i en bana, utan att rita något."""
#|    def __init__(self, lv, fx=None):
#|        self.lv = lv
#|        self.px, self.py = float(lv.start[0]), float(lv.start[1])
#|        self.spawn = (self.px, self.py)
#|        self.vx = self.vy = 0.0
#|        self.face = self.ddir = 1
#|        self.ground = False
#|        self.spring_up = False
#|        self.can_dash = True
#|        self.gtile = self.coy = self.jbuf = self.dash = 0
#|        self.coins = self.gotgems = self.deaths = self.dead = self.frames = self.t = 0
#|        self.won = False
#|        self.crum = {}          # smulande block: nyckel -> nedräkning
#|        self.gone = {}          # smulade block som kommer tillbaka
#|        self.flags = set()
#|        self.trail = []
#|        self.parts = self.pops = self.shake = fx or NoFx()
#|        self.gempos = []
#|        for ty in range(15):
#|            for tx in range(lv.w):
#|                if lv.g[ty][tx] == C_GEM:
#|                    self.gempos.append(tx + ty * 1000)
#|
#|    def step(self, L, R, J, Jp, D):
#|        """En bildruta. L/R/J = knappar nere, Jp/D = nyss tryckta (hopp, dash)."""
#|        lv = self.lv
#|        parts, pops, shake = self.parts, self.pops, self.shake
#|        self.t += 1
#|        t = self.t
#|        if self.dead:
#|            self.dead -= 1
#|            if self.dead == 0:
#|                self.px, self.py = self.spawn
#|                self.vx = self.vy = 0.0
#|                self.dash = 0
#|            self.crumble()
#|            return
#|        self.frames += 1
#|        px, py, vx, vy = self.px, self.py, self.vx, self.vy
#|        ground = self.ground
#|        if Jp:
#|            self.jbuf = 6
#|        if D and self.can_dash and not self.dash:
#|            self.dash = 9
#|            self.ddir = -1 if L and not R else 1 if R and not L else self.face
#|            self.can_dash = False
#|            shake.hit(2)
#|        ice = ground and self.gtile == C_ICE
#|        if self.dash:
#|            vx = 6.6 * self.ddir
#|            vy = 0.0
#|            self.dash -= 1
#|            self.trail.append((int(px), int(py)))
#|            if self.dash == 0:
#|                vx = 3.0 * self.ddir
#|        else:
#|            acc = 0.16 if ice else 0.7 if ground else 0.45
#|            top = 3.6 if ice else 3.1
#|            if L and not R:
#|                vx -= acc
#|                self.face = -1
#|            elif R and not L:
#|                vx += acc
#|                self.face = 1
#|            else:
#|                vx *= 0.97 if ice else 0.6 if ground else 0.9
#|            if vx > top:
#|                vx = top
#|            if vx < -top:
#|                vx = -top
#|            vy += 0.55
#|            if vy > 7.5:
#|                vy = 7.5
#|            if not J and vy < -3.0 and not self.spring_up:
#|                vy = -3.0
#|        if len(self.trail) > 5 or (self.trail and not self.dash):
#|            self.trail.pop(0)
#|        self.coy = 6 if ground else self.coy - 1
#|        if self.jbuf:
#|            self.jbuf -= 1
#|            if self.coy > 0:
#|                vy = -7.4
#|                self.jbuf = self.coy = 0
#|                ground = False
#|                self.spring_up = False
#|                parts.burst(px + 5, py + PH, WHITE, 5, 1.5, 8)
#|        # --- flytta i x ---
#|        nx = px + vx
#|        if vx:
#|            tx = int(nx + PW - 1) // TS if vx > 0 else int(nx) // TS
#|            for ty in range(int(py) // TS, int(py + PH - 1) // TS + 1):
#|                c = lv.at(tx, ty)
#|                if c == C_X and self.dash:
#|                    lv.g[ty][tx] = C_SP
#|                    parts.burst(tx * TS + 8, ty * TS + 8, CRACK[0], 14, 3, 18, 0.2)
#|                    shake.hit(4)
#|                elif AV_SOLID[c]:
#|                    nx = tx * TS - PW if vx > 0 else (tx + 1) * TS
#|                    vx = 0.0
#|                    self.dash = 0
#|        px = nx
#|        # --- flytta i y ---
#|        ny = py + vy
#|        was_ground = ground
#|        ground = False
#|        tx0, tx1 = int(px) // TS, int(px + PW - 1) // TS
#|        if vy >= 0:
#|            ty = int(ny + PH) // TS             # rutan precis under fötterna
#|            for tx in range(tx0, tx1 + 1):
#|                c = lv.at(tx, ty)
#|                if AV_SOLID[c] or (AV_TOP[c] and py + PH <= ty * TS + 0.5):
#|                    ny = ty * TS - PH
#|                    self.gtile = c
#|                    if c == C_SPR:
#|                        vy = -11.6
#|                        self.spring_up = True
#|                        parts.burst(px + 5, ny + PH, CORAL, 8, 2, 10)
#|                    else:
#|                        vy = 0.0
#|                        ground = True
#|                        self.spring_up = False
#|                        self.can_dash = True
#|                        if not was_ground:
#|                            parts.burst(px + 5, ny + PH, WHITE, 4, 1.2, 6)
#|                    if c == C_CR and (tx + ty * 1000) not in self.crum:
#|                        self.crum[tx + ty * 1000] = 22
#|                    break
#|        else:
#|            ty = int(ny) // TS
#|            for tx in range(tx0, tx1 + 1):
#|                c = lv.at(tx, ty)
#|                if AV_SOLID[c]:
#|                    if c == C_X:
#|                        lv.g[ty][tx] = C_SP
#|                        parts.burst(tx * TS + 8, ty * TS + 8, CRACK[0], 12, 3, 16, 0.2)
#|                    ny = (ty + 1) * TS
#|                    vy = 0.0
#|                    break
#|        py = ny
#|        self.px, self.py, self.vx, self.vy, self.ground = px, py, vx, vy, ground
#|        # --- saker och faror ---
#|        hurt = py > H + 8
#|        for ty in range(int(py + 3) // TS, int(py + PH - 1) // TS + 1):
#|            for tx in range(int(px + 1) // TS, int(px + PW - 2) // TS + 1):
#|                c = lv.at(tx, ty)
#|                k = tx + ty * 1000
#|                if c == C_COIN:
#|                    lv.g[ty][tx] = C_SP
#|                    self.coins += 1
#|                    parts.burst(tx * TS + 8, ty * TS + 8, YELLOW, 6, 1.6, 10)
#|                elif c == C_GEM:
#|                    lv.g[ty][tx] = C_SP
#|                    if k in self.gempos:
#|                        self.gotgems |= 1 << self.gempos.index(k)
#|                    parts.burst(tx * TS + 8, ty * TS + 8, GEMC, 18, 2.5, 20)
#|                    pops.add(tx * TS + 8, ty * TS - 4, "STEN!", GEMC)
#|                elif c == C_CHK and k not in self.flags:
#|                    self.flags.add(k)
#|                    self.spawn = (float(tx * TS + 3), float(ty * TS + 2))
#|                    pops.add(tx * TS + 8, ty * TS - 10, "SPARAT", LIME)
#|                elif c == C_EXIT:
#|                    self.won = True
#|                elif c == C_SPK or c == C_LAVA:
#|                    hurt = True
#|        # --- monster ---
#|        for e in lv.enemies:
#|            if not e[4]:
#|                continue
#|            if e[3] == 102:
#|                e[0] = e[5] + 40 * math.sin(t * 0.025 + e[5])
#|                e[1] = e[6] + 12 * math.sin(t * 0.08 + e[5])
#|            elif abs(e[0] - px) < 400:
#|                nx = e[0] + e[2]
#|                ax = int(nx if e[2] < 0 else nx + 13) // TS
#|                if AV_SOLID[lv.at(ax, int(e[1] + 6) // TS)] or not AV_TOP[lv.at(ax, int(e[1] + 13) // TS)]:
#|                    e[2] = -e[2]
#|                else:
#|                    e[0] = nx
#|            if px + PW > e[0] + 1 and px < e[0] + 13 and py + PH > e[1] + 1 and py < e[1] + 12:
#|                if self.dash or (e[3] != 107 and self.vy > 0 and py + PH - e[1] < 10):
#|                    e[4] = False
#|                    parts.burst(e[0] + 7, e[1] + 6, CORAL if e[3] == 119 else VIOLET, 14, 2.5, 16)
#|                    pops.add(e[0] + 7, e[1] - 6, "POFF!", WHITE)
#|                    if not self.dash:
#|                        self.vy = -9.0 if J else -6.5
#|                        self.spring_up = J
#|                    self.can_dash = True
#|                    shake.hit(3)
#|                else:
#|                    hurt = True
#|        if hurt and not self.won:
#|            self.dead = 26
#|            self.deaths += 1
#|            shake.hit(6)
#|            parts.burst(px + 5, min(py, H - 10) + 7, rgb(255, 90, 90), 24, 3.5, 24, 0.15)
#|        self.crumble()
#|
#|    def crumble(self):
#|        lv = self.lv
#|        for k in list(self.crum.keys()):
#|            self.crum[k] -= 1
#|            if self.crum[k] <= 0:
#|                del self.crum[k]
#|                lv.g[k // 1000][k % 1000] = C_SP
#|                self.gone[k] = 150
#|                self.parts.burst((k % 1000) * TS + 8, (k // 1000) * TS + 4, CRUMB[0], 8, 1.5, 12, 0.3)
#|        for k in list(self.gone.keys()):
#|            self.gone[k] -= 1
#|            if self.gone[k] <= 0:
#|                kx, ky = (k % 1000) * TS, (k // 1000) * TS
#|                if self.px + PW > kx and self.px < kx + TS and self.py + PH > ky and self.py < ky + TS:
#|                    self.gone[k] = 10
#|                else:
#|                    del self.gone[k]
#|                    lv.g[k // 1000][k % 1000] = C_CR
#|
#|
#|class AvFx:
#|    def __init__(self):
#|        self.p = Particles(70)
#|        self.q = Popups()
#|        self.s = Shake()
#|
#|    def burst(self, *a):
#|        self.p.burst(*a)
#|
#|    def add(self, *a):
#|        self.q.add(*a)
#|
#|    def hit(self, a):
#|        self.s.hit(a)
#|
#|
#|def av_run(lcd, keys, n):
#|    lv = AvLevel(n)
#|    gc.collect()
#|    fx = AvFx()
#|    a = Av(lv, fx)
#|    cam = 0.0
#|    t = 0
#|    keys.wait_release()
#|    # Bannamn
#|    for f in range(40):
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        gradient(lcd, lv.bg)
#|        av_tiles(lcd, lv, 0, t, a.crum, a.flags)
#|        lcd.fill_rect(0, 76, W, 74, BG)
#|        stext(lcd, "BANA %d: %s" % (n + 1, lv.name), 88, LIME, 2)
#|        ctext(lcd, lv.hint, 120, WHITE)
#|        lcd.show()
#|        t += 1
#|        if f > 8 and any(keys.now):
#|            break
#|        wait(t0)
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pause():
#|            if pause(lcd, keys):
#|                return None
#|        now, prev = keys.now, keys.prev
#|        L, R = now[K0], now[K1]
#|        a.step(L, R, now[K2], now[K2] and not prev[K2], now[K3] and not prev[K3])
#|        if a.won:
#|            return av_win(lcd, lv, cam, t, a, n)
#|        # kamera
#|        cam += (a.px - 140 - cam) * 0.25
#|        mx = lv.w * TS - W
#|        if cam < 0:
#|            cam = 0.0
#|        if cam > mx:
#|            cam = float(mx)
#|        ox, oy = fx.s.offset()
#|        c = int(cam) - ox
#|        # --- rita ---
#|        gradient(lcd, lv.bg)
#|        hs = lv.hills
#|        sc = c // 3
#|        for i in range(0, W, 8):
#|            h = hs[((i + sc) // 8) % 64]
#|            lcd.fill_rect(i, H - h, 8, h, lv.hill)
#|        av_tiles(lcd, lv, c, t, a.crum, a.flags)
#|        for e in lv.enemies:
#|            if e[4]:
#|                av_enemy(lcd, e, c, t)
#|        for i, (tx_, ty_) in enumerate(a.trail):
#|            hero(lcd, tx_ + 5 - c, ty_ + 7, a.ddir, t, SKY if i % 2 else VIOLET)
#|        if not a.dead:
#|            hx, hy = int(a.px) + 5 - c, int(a.py) + 7
#|            if a.dash:
#|                hero(lcd, hx, hy, a.ddir, t, SKY)
#|            else:
#|                hero(lcd, hx, hy, a.face, t if (L or R) and a.ground else 0)
#|        fx.p.draw(lcd, -c, 0)
#|        fx.q.draw(lcd, -c, 0)
#|        lcd.fill_rect(0, 0, W, 14, BG)
#|        lcd.text("%d %s" % (n + 1, lv.name), 4, 3, LIME)
#|        lcd.ellipse(124, 6, 4, 5, YELLOW, True)
#|        lcd.text("%d/%d" % (a.coins, lv.coins), 132, 3, WHITE)
#|        for k in range(3):
#|            gem(lcd, 210 + k * 12, 7, 4, GEMC if a.gotgems & (1 << k) else DIM)
#|        rtext(lcd, av_time(a.frames), W - 4, 3, WHITE)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def av_win(lcd, lv, cam, t, a, n):
#|    c = int(cam)
#|    frames, coins, gotgems, deaths, crum, flags = a.frames, a.coins, a.gotgems, a.deaths, a.crum, a.flags
#|    for f in range(75):
#|        t0 = time.ticks_ms()
#|        gradient(lcd, lv.bg)
#|        av_tiles(lcd, lv, c, t + f, crum, flags)
#|        for _ in range(8):
#|            lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3, random.choice(CONFETTI))
#|        lcd.fill_rect(40, 50, 240, 140, PANEL)
#|        lcd.rect(40, 50, 240, 140, LIME)
#|        stext(lcd, "BANAN KLAR!", 62, LIME, 2)
#|        ctext(lcd, "Tid: " + av_time(frames), 96, WHITE, 2)
#|        ctext(lcd, "Mynt: %d/%d" % (coins, lv.coins), 124, YELLOW)
#|        for k in range(3):
#|            gem(lcd, 136 + k * 24, 150, 7, GEMC if gotgems & (1 << k) else DIM)
#|        ctext(lcd, "Missar: %d" % deaths, 172, GRAY)
#|        lcd.show()
#|        wait(t0)
#|    return frames, gotgems
#@@ studs
#|# STUDS: 0 vänster, 1 höger, 2 skjut.
#|# Ju högre du kommer, desto fler världar: NATTEN, HIMLEN, RYMDEN, GALAXEN.
#|# Power-ups: jetpack (flyger rakt upp), fjäderskor (6 superstudsar), stjärnor (+50).
#|S_GRAV = 0.36
#|S_JUMP = -8.6
#|S_SPRING = -13.5
#|# namn, höjd, himmel uppe, himmel nere, rutnät/dekor
#|S_WORLDS = (
#|    ("NATTEN", 0, (16, 20, 44), (36, 18, 56), (30, 32, 66)),
#|    ("HIMLEN", 300, (60, 120, 220), (150, 200, 255), (130, 180, 245)),
#|    ("RYMDEN", 800, (4, 4, 16), (20, 10, 40), (60, 60, 90)),
#|    ("GALAXEN", 1500, (30, 0, 50), (90, 20, 90), (160, 80, 200)),
#|)
#|
#|
#|def play(lcd, keys):
#|    parts = Particles(70)
#|    pops = Popups()
#|    stars = Stars(40)
#|    px, py, vx, vy = W / 2, 200.0, 0.0, S_JUMP
#|    face = 1
#|    cam = 0.0
#|    best_y = py
#|    bonus = 0
#|    plats = [[W / 2 - 22, 220.0, 0, 0.0, False]]      # x, y, typ, fart, trasig
#|    items = []                                         # platta, sort (0 jetpack, 1 skor, 2 stjärna)
#|    monsters = []                                      # x, y, fart, fas
#|    bats = []                                          # x, y, fart, fas
#|    bullets = []
#|    top = 220.0
#|    squash = 0
#|    jet = 0
#|    shoes = 0
#|    world = 0
#|    bg = [mix(S_WORLDS[0][2], S_WORLDS[0][3], y / (H - 1)) for y in range(H)]
#|    banner = 0
#|    t = 0
#|    keys.wait_release()
#|
#|    def spawn_until(limit):
#|        nonlocal top
#|        while top > limit:
#|            height = (200 - top) / 10
#|            gmax = min(88, 40 + height * 0.04)
#|            gmin = min(60, 22 + height * 0.02)
#|            top -= random.uniform(gmin, gmax)
#|            r = random.random()
#|            if height > 300 and r < 0.15 + min(0.2, height / 8000):
#|                typ, spd = 1, random.choice((-1, 1)) * random.uniform(0.8, 1.8 + height / 2000)
#|            elif r > 0.92:
#|                typ, spd = 3, 0.0
#|            elif height > 300 and r > 0.78:
#|                typ, spd = 4, 0.0                           # moln: håller för ett studs
#|            else:
#|                typ, spd = 0, 0.0
#|            p = [random.uniform(4, W - 48), top, typ, spd, False]
#|            plats.append(p)
#|            if typ in (0, 1) and height > 60:
#|                q = random.random()
#|                if q < 0.025:
#|                    items.append([p, 0])
#|                elif q < 0.05:
#|                    items.append([p, 1])
#|                elif q < 0.16:
#|                    items.append([p, 2])
#|            if height > 150 and random.random() < 0.25:           # extra platta som går sönder
#|                plats.append([random.uniform(4, W - 48), top + random.uniform(10, 25), 2, 0.0, False])
#|            if height > 500 and random.random() < 0.05 + min(0.06, height / 30000):
#|                monsters.append([random.uniform(20, W - 20), top - 30, random.choice((-1, 1)) * 0.8, 0.0])
#|            if height > 350 and random.random() < 0.04 + min(0.05, height / 40000):
#|                d = random.choice((-1, 1))
#|                bats.append([-20.0 if d > 0 else W + 20.0, top - 20, d * random.uniform(1.2, 2.2), 0.0])
#|
#|    def score():
#|        return int((200 - best_y) / 10) + bonus
#|
#|    def die():
#|        for k in range(30):
#|            t1 = time.ticks_ms()
#|            draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
#|                       px, py + k * 6, cam, face, 0, t, score(), 0, 0)
#|            lcd.show()
#|            wait(t1)
#|        return score()
#|
#|    spawn_until(cam - 40)
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pause() and pause(lcd, keys):
#|            return score()
#|        if keys.held(K0):
#|            vx -= 0.7
#|            face = -1
#|        if keys.held(K1):
#|            vx += 0.7
#|            face = 1
#|        vx *= 0.86
#|        vx = max(-5.5, min(5.5, vx))
#|        if keys.pressed(K2):
#|            bullets.append([px, py - 10])
#|        px += vx
#|        if px < -8:
#|            px += W + 16
#|        elif px > W + 8:
#|            px -= W + 16
#|        oy = py
#|        if jet:
#|            jet -= 1
#|            vy = -11.0
#|            parts.burst(px, py + 12, random.choice((AMBER, CORAL, YELLOW)), 2, 1.5, 10, 0.2)
#|        else:
#|            vy += S_GRAV
#|        py += vy
#|        if squash > 0:
#|            squash -= 1
#|        # Landa på plattor (bara på väg ner)
#|        if vy > 0:
#|            for p in plats:
#|                if p[4]:
#|                    continue
#|                if p[0] - 6 <= px <= p[0] + 50 and oy + 10 <= p[1] <= py + 10:
#|                    if p[2] == 2:
#|                        p[4] = True
#|                        parts.burst(p[0] + 22, p[1], S_PLAT_C[2], 10, 2, 16, 0.2)
#|                        continue
#|                    py = p[1] - 10
#|                    if p[2] == 3 or shoes:
#|                        vy = S_SPRING
#|                        pops.add(px, py - 20, "BOING!", AMBER)
#|                        if shoes and p[2] != 3:
#|                            shoes -= 1
#|                    else:
#|                        vy = S_JUMP
#|                    squash = 5
#|                    if p[2] == 4:                           # molnet går upp i rök
#|                        p[4] = True
#|                        parts.burst(p[0] + 22, p[1] + 3, WHITE, 14, 2, 18)
#|                    break
#|        for p in plats:
#|            if p[2] == 1:
#|                p[0] += p[3]
#|                if p[0] < 2 or p[0] > W - 46:
#|                    p[3] = -p[3]
#|            if p[4]:
#|                p[1] += 4
#|        # Power-ups
#|        for it in items:
#|            p = it[0]
#|            ix, iy = p[0] + 22, p[1] - 12
#|            if abs(px - ix) < 14 and abs(py - iy) < 16:
#|                if it[1] == 0:
#|                    jet = max(jet, 80)
#|                    pops.add(px, py - 20, "JETPACK!", AMBER, 2)
#|                elif it[1] == 1:
#|                    shoes = 6
#|                    pops.add(px, py - 20, "FJADERSKOR!", CORAL)
#|                else:
#|                    bonus += 50
#|                    pops.add(px, py - 20, "+50", YELLOW)
#|                parts.burst(ix, iy, YELLOW, 12, 2.5, 14)
#|                it[1] = -1
#|        items = [it for it in items if it[1] >= 0 and not it[0][4] and it[0][1] < cam + H + 20]
#|        # Monster
#|        for m in monsters:
#|            m[3] += 0.08
#|            m[0] += m[2]
#|            if m[0] < 14 or m[0] > W - 14:
#|                m[2] = -m[2]
#|            my = m[1] + math.sin(m[3]) * 4
#|            if abs(px - m[0]) < 14 and abs(py - my) < 14:
#|                if jet or (vy > 0 and py < my):
#|                    if not jet:
#|                        vy = S_JUMP * 1.1
#|                    m[1] = 1e9
#|                    parts.burst(px, py + 8, VIOLET, 16, 3, 18)
#|                    pops.add(px, py - 10, "+200", VIOLET)
#|                    bonus += 200
#|                    goal("studs", 1)
#|                else:
#|                    return die()
#|        for b in bats:
#|            b[3] += 0.2
#|            b[0] += b[2]
#|            by = b[1] + math.sin(b[3]) * 6
#|            if abs(px - b[0]) < 12 and abs(py - by) < 11:
#|                if jet or (vy > 0 and py < by):
#|                    if not jet:
#|                        vy = S_JUMP
#|                    b[1] = 1e9
#|                    parts.burst(px, py + 8, rgb(110, 60, 160), 12, 2.5, 14)
#|                    pops.add(px, py - 10, "+100", VIOLET)
#|                    bonus += 100
#|                else:
#|                    return die()
#|        for b in bullets:
#|            b[1] -= 9
#|            for m in monsters + bats:
#|                if abs(b[0] - m[0]) < 12 and abs(b[1] - m[1]) < 14:
#|                    parts.burst(m[0], m[1], VIOLET, 14, 3, 16)
#|                    pops.add(m[0], m[1] - 10, "+200", VIOLET)
#|                    m[1] = 1e9
#|                    b[1] = -1e9
#|                    bonus += 200
#|                    goal("studs", 1)
#|        bullets = [b for b in bullets if b[1] > cam - 20]
#|        monsters = [m for m in monsters if m[1] < cam + H + 40]
#|        bats = [b for b in bats if b[1] < cam + H + 40 and -40 < b[0] < W + 40]
#|        # Kameran följer med uppåt
#|        if py < cam + 100:
#|            cam = py - 100
#|        best_y = min(best_y, py)
#|        h = int((200 - best_y) / 10)
#|        if world < len(S_WORLDS) - 1 and h >= S_WORLDS[world + 1][1]:
#|            world += 1
#|            wd = S_WORLDS[world]
#|            bg = [mix(wd[2], wd[3], y / (H - 1)) for y in range(H)]
#|            banner = 70
#|        sc = score()
#|        if sc >= 500:
#|            goal("studs", 0)
#|        if sc >= 2000:
#|            goal("studs", 2)
#|        plats = [p for p in plats if p[1] < cam + H + 20]
#|        spawn_until(cam - 40)
#|        if py > cam + H + 20:
#|            return die()
#|        draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
#|                   px, py, cam, face, squash, t, sc, jet, shoes)
#|        parts.draw(lcd, 0, -int(cam))
#|        pops.draw(lcd, 0, -int(cam))
#|        if banner:
#|            banner -= 1
#|            if (banner // 6) % 2 or banner > 40:
#|                stext(lcd, S_WORLDS[world][0], 100, YELLOW, 3)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
#|               px, py, cam, face, squash, t, score, jet, shoes):
#|    gradient(lcd, bg)
#|    dec = rgb(*S_WORLDS[world][4])
#|    c = int(cam)
#|    if world == 0:
#|        off = -c % 20
#|        for y in range(off, H, 20):
#|            lcd.hline(0, y, W, dec)
#|        for x in range(0, W, 20):
#|            lcd.vline(x, 0, H, dec)
#|    elif world == 1:
#|        for k in range(5):
#|            cy = (k * 70 - c // 3) % (H + 60) - 30
#|            cx = (k * 97) % W
#|            lcd.ellipse(cx, cy, 30, 9, dec, True)
#|            lcd.ellipse(cx + 18, cy - 5, 16, 8, dec, True)
#|    else:
#|        stars.draw(lcd, 0.0, 0.6 if world == 2 else 1.2)
#|        if world == 3:
#|            pyy = (40 - c // 6) % (H + 80) - 40
#|            lcd.ellipse(250, pyy, 26, 26, rgb(200, 90, 160), True)
#|            lcd.ellipse(250, pyy, 40, 6, rgb(240, 200, 120))
#|    for p in plats:
#|        x, y = int(p[0]), int(p[1]) - c
#|        col = S_PLAT_C[p[2]]
#|        if p[4]:
#|            if p[2] != 4:
#|                lcd.fill_rect(x, y, 20, 6, col)
#|                lcd.fill_rect(x + 24, y + 2, 20, 6, col)
#|            continue
#|        if p[2] == 4:
#|            lcd.ellipse(x + 12, y + 4, 12, 5, col, True)
#|            lcd.ellipse(x + 30, y + 4, 14, 6, col, True)
#|            lcd.ellipse(x + 22, y + 1, 10, 5, col, True)
#|            continue
#|        lcd.fill_rect(x + 2, y, 40, 7, col)
#|        lcd.fill_rect(x, y + 2, 44, 3, col)
#|        lcd.hline(x + 3, y + 1, 38, WHITE if p[2] != 2 else rgb(220, 170, 120))
#|        if p[2] == 2:
#|            lcd.vline(x + 15, y, 7, BG)
#|            lcd.vline(x + 30, y, 7, BG)
#|        if p[2] == 3:
#|            lcd.fill_rect(x + 16, y - 6, 12, 6, GRAY)
#|            lcd.fill_rect(x + 14, y - 8, 16, 3, CORAL)
#|    for it in items:
#|        ix, iy = int(it[0][0]) + 22, int(it[0][1]) - 12 - c + int(2 * math.sin(t * 0.2))
#|        if it[1] == 0:                                      # jetpack
#|            lcd.fill_rect(ix - 7, iy - 7, 6, 12, GRAY)
#|            lcd.fill_rect(ix + 1, iy - 7, 6, 12, GRAY)
#|            lcd.fill_rect(ix - 7, iy - 8, 14, 3, CORAL)
#|            lcd.fill_rect(ix - 6, iy + 5, 4, 3, AMBER)
#|            lcd.fill_rect(ix + 2, iy + 5, 4, 3, AMBER)
#|        elif it[1] == 1:                                    # fjäderskor
#|            lcd.fill_rect(ix - 8, iy, 7, 4, CORAL)
#|            lcd.fill_rect(ix + 1, iy, 7, 4, CORAL)
#|            for k in range(3):
#|                lcd.hline(ix - 7, iy + 5 + k * 2, 5, GRAY)
#|                lcd.hline(ix + 2, iy + 5 + k * 2, 5, GRAY)
#|        else:
#|            star(lcd, ix, iy, 7, YELLOW)
#|    for m in monsters:
#|        mx, my = int(m[0]), int(m[1] + math.sin(m[3]) * 4) - c
#|        lcd.ellipse(mx, my, 12, 10, VIOLET, True)
#|        lcd.ellipse(mx - 4, my - 3, 3, 3, WHITE, True)
#|        lcd.ellipse(mx + 4, my - 3, 3, 3, WHITE, True)
#|        lcd.pixel(mx - 4, my - 2, BLACK)
#|        lcd.pixel(mx + 4, my - 2, BLACK)
#|        lcd.hline(mx - 5, my + 5, 10, BLACK)
#|        for k in (-8, -2, 4):
#|            lcd.fill_rect(mx + k, my + 8 + (t // 5 + k) % 2, 3, 4, VIOLET)
#|    for b in bats:
#|        bx, by = int(b[0]), int(b[1] + math.sin(b[3]) * 6) - c
#|        fl = 5 if (t // 3) % 2 else -4
#|        tri(lcd, bx, by, bx - 13, by - 3 + fl, bx - 4, by + 4, rgb(70, 40, 110))
#|        tri(lcd, bx, by, bx + 13, by - 3 + fl, bx + 4, by + 4, rgb(70, 40, 110))
#|        lcd.ellipse(bx, by, 5, 5, rgb(110, 60, 160), True)
#|        lcd.fill_rect(bx - 3, by - 2, 2, 2, YELLOW)
#|        lcd.fill_rect(bx + 2, by - 2, 2, 2, YELLOW)
#|    for b in bullets:
#|        lcd.ellipse(int(b[0]), int(b[1]) - c, 3, 3, AMBER, True)
#|    # Hopparen
#|    x, y = int(px), int(py) - c
#|    sq = 3 if squash else 0
#|    if jet:
#|        lcd.fill_rect(x - 13, y - 6, 5, 12, GRAY)
#|        lcd.fill_rect(x - 13, y + 6, 5, 4 + t % 3, AMBER)
#|    lcd.ellipse(x, y - 2 + sq, 9, 9 - sq, LIME, True)
#|    lcd.fill_rect(x - 9, y + 2, 18, 6 - sq, LIME)
#|    lcd.fill_rect(x - 9, y + 6 - sq, 18, 2, rgb(60, 150, 70))
#|    lcd.fill_rect(x + 8 if face > 0 else x - 14, y - 4, 6, 4, LIME)      # näsa
#|    lcd.fill_rect(x + face * 3 - 1, y - 6, 3, 3, WHITE)
#|    lcd.pixel(x + face * 4, y - 5, BLACK)
#|    fc = CORAL if shoes else rgb(60, 150, 70)
#|    for k in (-6, -1, 4):
#|        lcd.fill_rect(x + k, y + 8 - sq, 2, 4 + sq, fc)
#|    big(lcd, str(score), 6, 6, WHITE, 2)
#|    lcd.text("REKORD %d" % SCORES.get("studs", 0), 6, 26, GRAY if world == 1 else DIM)
#|    if shoes:
#|        rtext(lcd, "SKOR x%d" % shoes, W - 6, 6, CORAL)
#@@ pac
#|# SPOKJAKT: pilarna i hörnen, 0 upp, 1 höger, 2 ner, 3 vänster.
#|P_HALVES = (
#|    (
#|        "###########", "#o........#", "#.###.###.#", "#..........", "#.###.#.###",
#|        "#.....#...#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
#|        "#####.#.###", "    #.#....", "#####.#.###", "#.........#", "#.###.###.#",
#|        "#o..#......", "###.#.#.###", "#.....#...#", "#.#######.#", "#..........",
#|        "###########",
#|    ),
#|    (
#|        "###########", "#o..##.....", "#.#.##.###.", "#.#........", "#.#.#####.#",
#|        "#.........#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
#|        "#####.#.###", "    #.#....", "#####.#.###", "#..........", "#.##.###.#.",
#|        "#o.#.......", "##.#.#.###.", "#....#.....", "#.######.#.", "#..........",
#|        "###########",
#|    ),
#|    (
#|        "###########", "#.........#", "#.##.####.#", "#o##.......", "#.##.#.##.#",
#|        "#.........#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
#|        "#####.#.###", "    #.#....", "#####.#.###", "#.....#...#", "#o###.#.#.#",
#|        "#...#......", "###.#.###.#", "#.........#", "#.###.#####", "#..........",
#|        "###########",
#|    ),
#|)
#|P_MAZE = None
#|
#|
#|def p_set_maze(n):
#|    """Byter labyrint (spegla vänster halva)."""
#|    global P_MAZE
#|    h = P_HALVES[n % len(P_HALVES)]
#|    P_MAZE = tuple(r + "".join(r[9 - i] for i in range(10)) for r in h)
#|
#|
#|p_set_maze(0)
#|MW, MH = 21, 21
#|PT = 10
#|PX0, PY0 = (W - MW * PT) // 2, 26
#|P_WALL_D = rgb(14, 18, 70)
#|P_WALLS = (P_WALL, rgb(220, 50, 140), rgb(40, 180, 100))
#|FRIGHT_C = rgb(50, 70, 255)
#|SCATTER = ((19, -2), (1, -2), (19, 22), (1, 22))
#|HOUSE = (10, 9)
#|EXIT = (10, 7)
#|
#|
#|def p_walk(x, y):
#|    """0 vägg, 1 gång, 2 spökhus, 3 dörr."""
#|    if y < 0 or y >= MH:
#|        return 0
#|    ch = P_MAZE[y][x % MW]
#|    if ch == "." or ch == "o":
#|        return 1
#|    if ch == "G":
#|        return 2
#|    if ch == "-":
#|        return 3
#|    return 0
#|
#|
#|def p_wall_rects():
#|    """Förberäknar väggarnas rektanglar (fyllning + kantlinjer)."""
#|    fills = []
#|    edges = []
#|    for y in range(MH):
#|        x = 0
#|        while x < MW:
#|            if P_MAZE[y][x] == "#":
#|                s = x
#|                while x < MW and P_MAZE[y][x] == "#":
#|                    x += 1
#|                fills.append((PX0 + s * PT, PY0 + y * PT, (x - s) * PT, PT))
#|            else:
#|                x += 1
#|    for y in range(MH):
#|        for x in range(MW):
#|            if P_MAZE[y][x] != "#":
#|                continue
#|            px, py = PX0 + x * PT, PY0 + y * PT
#|            for d, (dx, dy) in enumerate(DIRS4):
#|                nx, ny = x + dx, y + dy
#|                if 0 <= nx < MW and 0 <= ny < MH and P_MAZE[ny][nx] not in "# ":
#|                    if d == 0:
#|                        edges.append((px, py, PT, 2))
#|                    elif d == 1:
#|                        edges.append((px + PT - 2, py, 2, PT))
#|                    elif d == 2:
#|                        edges.append((px, py + PT - 2, PT, 2))
#|                    else:
#|                        edges.append((px, py, 2, PT))
#|    return tuple(fills), tuple(edges)
#|
#|
#|@native
#|def p_draw_maze(fb, fills, edges, dots, blink, wall_c):
#|    for r in fills:
#|        fb.fill_rect(r[0], r[1], r[2], r[3], P_WALL_D)
#|    for r in edges:
#|        fb.fill_rect(r[0], r[1], r[2], r[3], wall_c)
#|    for y in range(MH):
#|        for x in range(MW):
#|            v = dots[y * MW + x]
#|            if v == 1:
#|                fb.fill_rect(PX0 + x * PT + 4, PY0 + y * PT + 4, 2, 2, P_DOT)
#|            elif v == 2 and blink:
#|                fb.ellipse(PX0 + x * PT + 5, PY0 + y * PT + 5, 3, 3, P_DOT, True)
#|    fb.fill_rect(PX0 + 10 * PT, PY0 + 8 * PT + 4, PT, 2, rgb(255, 150, 210))
#|
#|
#|def turn_back(e):
#|    """Vänd mitt i en ruta utan att hoppa."""
#|    if e.d < 0:
#|        return
#|    dx, dy = DIRS4[e.d]
#|    if e.p > 0:
#|        e.x = (e.x + dx) % MW
#|        e.y += dy
#|        e.p = 1 - e.p
#|    e.d = (e.d + 2) % 4
#|
#|
#|class Ent:
#|    def __init__(self, x, y, d, speed):
#|        self.x, self.y, self.d, self.p, self.speed = x, y, d, 0.0, speed
#|
#|    def pos(self):
#|        if self.d < 0:
#|            return self.x, self.y
#|        dx, dy = DIRS4[self.d]
#|        return self.x + dx * self.p, self.y + dy * self.p
#|
#|
#|def g_decide(g, ghosts, pac, face, chase):
#|    """Spöket står mitt i en ruta och väljer nästa riktning."""
#|    if g.state == "leave":
#|        tx, ty = EXIT
#|    elif g.state == "eyes":
#|        tx, ty = HOUSE
#|    elif not chase:
#|        tx, ty = SCATTER[g.i]
#|    else:
#|        pdx, pdy = DIRS4[face]
#|        if g.i == 0:                                  # röd: jagar Pac direkt
#|            tx, ty = pac.x, pac.y
#|        elif g.i == 1:                                # rosa: siktar framför Pac
#|            tx, ty = pac.x + 4 * pdx, pac.y + 4 * pdy
#|        elif g.i == 2:                                # blå: knipa tillsammans med röd
#|            b = ghosts[0]
#|            tx, ty = 2 * (pac.x + 2 * pdx) - b.x, 2 * (pac.y + 2 * pdy) - b.y
#|        else:                                         # orange: blyg när den är nära
#|            if (g.x - pac.x) ** 2 + (g.y - pac.y) ** 2 > 36:
#|                tx, ty = pac.x, pac.y
#|            else:
#|                tx, ty = SCATTER[3]
#|    inside = g.state in ("leave", "eyes")
#|    opts = []
#|    for d in (0, 3, 2, 1):
#|        if d == (g.d + 2) % 4:
#|            continue
#|        ddx, ddy = DIRS4[d]
#|        w = p_walk(g.x + ddx, g.y + ddy)
#|        if w == 1 or (inside and w in (2, 3)):
#|            opts.append(d)
#|    if not opts:
#|        opts = [(g.d + 2) % 4]
#|    if g.fright and g.state == "normal":
#|        g.d = random.choice(opts)
#|        return
#|    best = None
#|    for d in opts:
#|        ddx, ddy = DIRS4[d]
#|        dist = (g.x + ddx - tx) ** 2 + (g.y + ddy - ty) ** 2
#|        if best is None or dist < best:
#|            best = dist
#|            g.d = d
#|
#|
#|def p_cherry(fb, x, y):
#|    fb.line(x, y - 6, x - 3, y, LIME)
#|    fb.line(x, y - 6, x + 3, y + 1, LIME)
#|    fb.ellipse(x - 3, y + 1, 3, 3, CORAL, True)
#|    fb.ellipse(x + 3, y + 2, 3, 3, CORAL, True)
#|    fb.pixel(x - 4, y, WHITE)
#|
#|
#|def play(lcd, keys):
#|    p_set_maze(0)
#|    fills, edges = p_wall_rects()
#|    wall = P_WALLS[0]
#|    score = 0
#|    lives = 3
#|    level = 1
#|    pops = Popups()
#|    parts = Particles(60)
#|
#|    def new_dots():
#|        d = bytearray(MW * MH)
#|        for y in range(MH):
#|            for x in range(MW):
#|                ch = P_MAZE[y][x]
#|                if ch == ".":
#|                    d[y * MW + x] = 1
#|                elif ch == "o":
#|                    d[y * MW + x] = 2
#|        d[15 * MW + 10] = 0                                  # där Pac börjar
#|        return d
#|
#|    dots = new_dots()
#|    left = sum(1 for v in dots if v)
#|    total = left
#|    fruit_t = 0
#|    fruits = 0
#|
#|    while True:                                              # ett liv
#|        pac = Ent(10, 15, -1, min(0.13 + level * 0.006, 0.17))
#|        face = 3
#|        want = -1
#|        ghosts = []
#|        for i, (x, y) in enumerate(((10, 7), (10, 9), (9, 9), (11, 9))):
#|            g = Ent(x, y, 3 if i == 0 else 0, 0.12)
#|            g.i = i
#|            g.state = "normal" if i == 0 else "house"
#|            g.release = (0, 60, 160, 260)[i]
#|            g.fright = 0
#|            ghosts.append(g)
#|        mode_t = 0
#|        fright_t = 0
#|        eat_n = 0
#|        ready = 60
#|        t = 0
#|        dead = 0
#|        keys.wait_release()
#|        while True:
#|            t0 = time.ticks_ms()
#|            keys.update()
#|            if keys.pause() and pause(lcd, keys):
#|                return score
#|            for k, d in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
#|                if keys.pressed(k):
#|                    want = d
#|            if ready > 0:
#|                ready -= 1
#|            elif dead == 0:
#|                # --- Pac ---
#|                if pac.d >= 0 and want == (pac.d + 2) % 4:          # vänd direkt
#|                    dx, dy = DIRS4[pac.d]
#|                    pac.x = (pac.x + dx) % MW
#|                    pac.y += dy
#|                    pac.p = 1 - pac.p
#|                    pac.d = want
#|                if pac.d < 0 and want >= 0:
#|                    dx, dy = DIRS4[want]
#|                    if p_walk(pac.x + dx, pac.y + dy) == 1:
#|                        pac.d = want
#|                if pac.d >= 0:
#|                    face = pac.d
#|                    pac.p += pac.speed
#|                    while pac.p >= 1:
#|                        pac.p -= 1
#|                        dx, dy = DIRS4[pac.d]
#|                        pac.x = (pac.x + dx) % MW
#|                        pac.y += dy
#|                        k = pac.y * MW + pac.x
#|                        if dots[k]:
#|                            if dots[k] == 2:
#|                                score += 50
#|                                fright_t = max(60, 200 - level * 20)
#|                                eat_n = 0
#|                                for g in ghosts:
#|                                    if g.state == "normal":
#|                                        g.fright = 1
#|                                        turn_back(g)
#|                            else:
#|                                score += 10
#|                            dots[k] = 0
#|                            left -= 1
#|                            if (total - left in (70, 160)) and fruits < 2:
#|                                fruits += 1
#|                                fruit_t = 300
#|                        if fruit_t and (pac.x, pac.y) == (10, 11):
#|                            pts = min(100 * level, 1000)
#|                            score += pts
#|                            fruit_t = 0
#|                            pops.add(PX0 + 105, PY0 + 108, str(pts), CORAL)
#|                            parts.burst(PX0 + 105, PY0 + 115, CORAL, 14, 2.5, 16)
#|                        if want >= 0:
#|                            dx, dy = DIRS4[want]
#|                            if p_walk(pac.x + dx, pac.y + dy) == 1:
#|                                pac.d = want
#|                        dx, dy = DIRS4[pac.d]
#|                        if p_walk(pac.x + dx, pac.y + dy) != 1:
#|                            pac.d = -1
#|                            pac.p = 0.0
#|                            break
#|                # --- Läge: spridning eller jakt ---
#|                mode_t += 1
#|                cycle = mode_t % 900
#|                chase = cycle >= 210
#|                if mode_t % 900 in (0, 210) and mode_t > 1:
#|                    for g in ghosts:
#|                        if g.state == "normal" and not g.fright:
#|                            turn_back(g)
#|                if fright_t > 0:
#|                    fright_t -= 1
#|                    if fright_t == 0:
#|                        for g in ghosts:
#|                            g.fright = 0
#|                # --- Spöken ---
#|                for g in ghosts:
#|                    if g.state == "house":
#|                        if t >= g.release:
#|                            g.state = "leave"
#|                            g.p = 0.0
#|                            g.d = 0
#|                            g_decide(g, ghosts, pac, face, chase)
#|                        continue
#|                    if g.state == "eyes":
#|                        sp = 0.3
#|                    elif g.fright:
#|                        sp = 0.08
#|                    else:
#|                        sp = min(0.12 + level * 0.007, 0.16)
#|                    if g.y == 9 and (g.x < 4 or g.x > 16):
#|                        sp *= 0.6                                    # långsamt i tunneln
#|                    if g.d < 0:
#|                        g.d = 0
#|                    g.p += sp
#|                    while g.p >= 1:
#|                        g.p -= 1
#|                        dx, dy = DIRS4[g.d]
#|                        g.x = (g.x + dx) % MW
#|                        g.y += dy
#|                        if g.state == "leave" and (g.x, g.y) == EXIT:
#|                            g.state = "normal"
#|                        if g.state == "eyes" and (g.x, g.y) == HOUSE:
#|                            g.state = "leave"
#|                            g.fright = 0
#|                        g_decide(g, ghosts, pac, face, chase)
#|                # --- Krockar ---
#|                ppx, ppy = pac.pos()
#|                for g in ghosts:
#|                    if g.state in ("house", "eyes", "leave"):
#|                        continue
#|                    gx, gy = g.pos()
#|                    if (gx - ppx) ** 2 + (gy - ppy) ** 2 < 0.5:
#|                        if g.fright:
#|                            g.state = "eyes"
#|                            g.fright = 0
#|                            pts = 200 << min(eat_n, 3)
#|                            eat_n += 1
#|                            if eat_n >= 4:
#|                                goal("pac", 1)
#|                            score += pts
#|                            sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
#|                            pops.add(sx, sy - 8, str(pts), TEAL)
#|                            parts.burst(sx, sy, FRIGHT_C, 12, 2.5, 14)
#|                        else:
#|                            dead = 1
#|                if left == 0:
#|                    goal("pac", 0)
#|                    for k in range(8):
#|                        lcd.fill(P_BGC)
#|                        p_draw_maze(lcd, fills, edges, dots, False, WHITE if k % 2 == 0 else wall)
#|                        lcd.show()
#|                        time.sleep_ms(160)
#|                    level += 1
#|                    p_set_maze(level - 1)
#|                    fills, edges = p_wall_rects()
#|                    wall = P_WALLS[(level - 1) % len(P_WALLS)]
#|                    dots = new_dots()
#|                    left = total = sum(1 for v in dots if v)
#|                    fruits = fruit_t = 0
#|                    pops.add(W // 2, 120, "NIVA %d" % level, LIME, 2)
#|                    break
#|            else:
#|                dead += 1
#|                if dead > 50:
#|                    lives -= 1
#|                    if lives <= 0:
#|                        return score
#|                    break
#|            # --- Rita ---
#|            lcd.fill(P_BGC)
#|            p_draw_maze(lcd, fills, edges, dots, (t // 8) % 2 == 0, wall)
#|            if fruit_t:
#|                fruit_t -= 1
#|                if fruit_t > 60 or (t // 4) % 2:
#|                    p_cherry(lcd, PX0 + 105, PY0 + 115)
#|            for g in ghosts:
#|                gx, gy = g.pos()
#|                sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
#|                if g.state == "house":
#|                    sy += int(2 * math.sin(t * 0.2 + g.i))
#|                if dead and dead > 10:
#|                    continue
#|                if g.state == "eyes":
#|                    draw_ghost(lcd, sx, sy, 0, g.d, t, True)
#|                elif g.fright:
#|                    flash = fright_t < 50 and (t // 5) % 2
#|                    draw_ghost(lcd, sx, sy, WHITE if flash else FRIGHT_C, g.d, t, False, True)
#|                else:
#|                    draw_ghost(lcd, sx, sy, GHOST_C[g.i], g.d, t)
#|            ppx, ppy = pac.pos()
#|            sx, sy = PX0 + int(ppx * PT) + 5, PY0 + int(ppy * PT) + 5
#|            if dead:
#|                m = min(3.1, 0.5 + dead * 0.07)
#|                if m < 3.0:
#|                    draw_pac(lcd, sx, sy, 0, m)
#|            else:
#|                mouth = abs(math.sin(t * 0.5)) if pac.d >= 0 else 0.4
#|                draw_pac(lcd, sx, sy, face, mouth)
#|            parts.draw(lcd)
#|            pops.draw(lcd)
#|            # Poäng och liv
#|            if score >= 5000:
#|                goal("pac", 2)
#|            big(lcd, str(score), PX0, 6, WHITE, 2)
#|            rtext(lcd, "NIVA %d" % level, PX0 + MW * PT, 10, LIME)
#|            for i in range(lives - 1):
#|                draw_pac(lcd, 140 + i * 14, 13, 1, 0.6, P_YEL, 4)
#|            if ready > 0:
#|                ctext(lcd, "REDO!", PY0 + 13 * PT + 1, P_YEL, 1)
#|            arrow(lcd, 14, 14, 0, DIM)
#|            arrow(lcd, W - 14, 14, 1, DIM)
#|            arrow(lcd, W - 14, H - 14, 2, DIM)
#|            arrow(lcd, 14, H - 14, 3, DIM)
#|            lcd.show()
#|            t += 1
#|            wait(t0)
#@@ 2048
#|# 2048: pilarna i hörnen, 0 upp, 1 höger, 2 ner, 3 vänster.
#|G_N = 4
#|G_S = 46
#|G_GAP = 6
#|G_X = (W - (G_N * G_S + (G_N + 1) * G_GAP)) // 2
#|G_Y = 16
#|G_BOARD = rgb(60, 52, 80)
#|G_EMPTY = rgb(80, 72, 104)
#|G_BGC = [mix((30, 22, 46), (16, 26, 46), y / (H - 1)) for y in range(H)]
#|
#|
#|def play(lcd, keys):
#|    grid = [[0] * G_N for _ in range(G_N)]
#|    score = 0
#|    won = False
#|    pops = Popups()
#|    parts = Particles(80)
#|
#|    def spawn():
#|        empty = [(r, c) for r in range(G_N) for c in range(G_N) if grid[r][c] == 0]
#|        if empty:
#|            r, c = random.choice(empty)
#|            grid[r][c] = 1 if random.random() < 0.9 else 2
#|            return (r, c)
#|        return None
#|
#|    def cell_xy(r, c):
#|        return G_X + G_GAP + c * (G_S + G_GAP), G_Y + G_GAP + r * (G_S + G_GAP)
#|
#|    def can_move():
#|        for r in range(G_N):
#|            for c in range(G_N):
#|                if grid[r][c] == 0:
#|                    return True
#|                if c + 1 < G_N and grid[r][c] == grid[r][c + 1]:
#|                    return True
#|                if r + 1 < G_N and grid[r][c] == grid[r + 1][c]:
#|                    return True
#|        return False
#|
#|    def move(d):
#|        """d: 0 upp, 1 höger, 2 ner, 3 vänster. Returnerar (rörelser, sammanslagna, poäng)."""
#|        nonlocal grid
#|        dr, dc = ((-1, 0), (0, 1), (1, 0), (0, -1))[d]
#|        moves = []
#|        merged = []
#|        gain = 0
#|        new = [[0] * G_N for _ in range(G_N)]
#|        for i in range(G_N):
#|            # gå längs raden/kolumnen från den sida brickorna glider mot
#|            if dr:
#|                line = [(r, i) for r in (range(G_N) if dr < 0 else range(G_N - 1, -1, -1))]
#|            else:
#|                line = [(i, c) for c in (range(G_N) if dc < 0 else range(G_N - 1, -1, -1))]
#|            target = 0
#|            last = None                       # (värde, index i linjen, kan slås ihop)
#|            for (r, c) in line:
#|                v = grid[r][c]
#|                if not v:
#|                    continue
#|                if last and last[0] == v and last[2]:
#|                    tr, tc = line[last[1]]
#|                    new[tr][tc] = v + 1
#|                    gain += 1 << (v + 1)
#|                    merged.append((tr, tc))
#|                    moves.append((r, c, tr, tc, v))
#|                    last = (v + 1, last[1], False)
#|                else:
#|                    tr, tc = line[target]
#|                    new[tr][tc] = v
#|                    moves.append((r, c, tr, tc, v))
#|                    last = (v, target, True)
#|                    target += 1
#|        changed = any(m[0] != m[2] or m[1] != m[3] for m in moves)
#|        if changed:
#|            grid = new
#|        return (moves if changed else None), merged, gain
#|
#|    spawn()
#|    spawn()
#|    pop = []
#|    t = 0
#|    keys.wait_release()
#|    while True:
#|        t0 = time.ticks_ms()
#|        keys.update()
#|        if keys.pause() and pause(lcd, keys):
#|            return score
#|        d = -1
#|        for k, dd in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
#|            if keys.pressed(k):
#|                d = dd
#|        if d >= 0:
#|            moves, merged, gain = move(d)
#|            if moves:
#|                # Glid-animation
#|                for f in range(1, 6):
#|                    p = f / 5
#|                    draw_2048(lcd, None, score, t)
#|                    for (r, c, tr, tc, v) in moves:
#|                        x0, y0 = cell_xy(r, c)
#|                        x1, y1 = cell_xy(tr, tc)
#|                        g_tile(lcd, int(x0 + (x1 - x0) * p), int(y0 + (y1 - y0) * p), v)
#|                    lcd.show()
#|                    time.sleep_ms(14)
#|                score += gain
#|                if gain:
#|                    pops.add(W // 2, 6, "+%d" % gain, AMBER)
#|                pop = [(r, c, 6) for r, c in merged]
#|                for r, c in merged:
#|                    x, y = cell_xy(r, c)
#|                    parts.burst(x + G_S // 2, y + G_S // 2, G_COL[min(grid[r][c] - 1, 13)], 8, 2.5, 12)
#|                    e = grid[r][c]
#|                    if e >= 8:
#|                        goal("2048", 0)
#|                    if e >= 10:
#|                        goal("2048", 1)
#|                    if e >= 11:
#|                        goal("2048", 2)
#|                    if grid[r][c] == 11 and not won:
#|                        won = True
#|                        pops.add(W // 2, 100, "2048! DU VANN!", YELLOW, 2)
#|                s = spawn()
#|                if s:
#|                    pop.append((s[0], s[1], -6))
#|                if not can_move():
#|                    draw_2048(lcd, None, score, t)
#|                    lcd.show()
#|                    time.sleep_ms(900)
#|                    return score
#|        draw_2048(lcd, grid, score, t, pop)
#|        pop = [(r, c, k - 1 if k > 0 else k + 1) for r, c, k in pop if k != 0]
#|        parts.draw(lcd)
#|        pops.draw(lcd)
#|        lcd.show()
#|        t += 1
#|        wait(t0)
#|
#|
#|def draw_2048(lcd, grid, score, t, pop=()):
#|    gradient(lcd, G_BGC)
#|    size = G_N * G_S + (G_N + 1) * G_GAP
#|    lcd.fill_rect(G_X, G_Y, size, size, G_BOARD)
#|    for r in range(G_N):
#|        for c in range(G_N):
#|            x = G_X + G_GAP + c * (G_S + G_GAP)
#|            y = G_Y + G_GAP + r * (G_S + G_GAP)
#|            lcd.fill_rect(x + 2, y, G_S - 4, G_S, G_EMPTY)
#|            lcd.fill_rect(x, y + 2, G_S, G_S - 4, G_EMPTY)
#|            if grid and grid[r][c]:
#|                g_tile(lcd, x, y, grid[r][c])
#|    for r, c, k in pop:
#|        if grid and grid[r][c]:
#|            x = G_X + G_GAP + c * (G_S + G_GAP)
#|            y = G_Y + G_GAP + r * (G_S + G_GAP)
#|            if k > 0:                                     # sammanslagen: blir större
#|                g = k // 2
#|                g_tile(lcd, x - g, y - g, grid[r][c], G_S + 2 * g)
#|            else:                                         # ny: växer fram
#|                s = G_S + k * 6
#|                if s > 8:
#|                    g_tile(lcd, x + (G_S - s) // 2, y + (G_S - s) // 2, grid[r][c], s)
#|    # Poäng till höger, pilar i hörnen
#|    lcd.text("POANG", 8, 40, GRAY)
#|    big(lcd, str(score), 8, 52, WHITE, 2 if score < 100 else 1)
#|    lcd.text("REKORD", 8, 84, DIM)
#|    lcd.text(str(SCORES.get("2048", 0)), 8, 96, DIM)
#|    arrow(lcd, 12, 12, 0, AMBER)
#|    arrow(lcd, W - 12, 12, 1, AMBER)
#|    arrow(lcd, W - 12, H - 12, 2, AMBER)
#|    arrow(lcd, 12, H - 12, 3, AMBER)
#@@ invasion
#|# INVASION: 0 vänster, 1 höger, 2 skjut, 3 superlaser.
#|SPR_SQUID = (("...##...", "..####..", ".######.", "##.##.##", "########", "..#..#..", ".#.##.#.", "#.#..#.#"),
#|             ("...##...", "..####..", ".######.", "##.##.##", "########", ".#.##.#.", "#......#", ".#....#."))
#|SPR_CRAB = (("..#.....#..", "...#...#...", "..#######..", ".##.###.##.", "###########", "#.#######.#", "#.#.....#.#", "...##.##..."),
#|            ("..#.....#..", "#..#...#..#", "#.#######.#", "###.###.###", "###########", ".#########.", "..#.....#..", ".#.......#."))
#|SPR_OCTO = (("....####....", ".##########.", "############", "###..##..###", "############", "...##..##...", "..##.##.##..", "##........##"),
#|            ("....####....", ".##########.", "############", "###..##..###", "############", "..###..###..", ".##..##..##.", "..##....##.."))
#|SPR_SHIP = ("......#......", ".....###.....", ".....###.....", ".###########.", "#############", "#############", "#############")
#|SPR_UFO = (".....######.....", "...##########...", "..############..", ".##.##.##.##.##.", "################", "..###..##..###..", "...#........#...")
#|I_COLS = (PINK, TEAL, TEAL, LIME, LIME)
#|I_POINTS = (30, 20, 20, 10, 10)
#|
#|
#|def sprite(rows, col, s=2):
#|    """Gör en liten bild (FrameBuffer) av en textmall. Svart = genomskinligt."""
#|    w, h = len(rows[0]) * s, len(rows) * s
#|    buf = bytearray(w * h * 2)
#|    fb = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
#|    for y, r in enumerate(rows):
#|        for x, ch in enumerate(r):
#|            if ch == "#":
#|                fb.fill_rect(x * s, y * s, s, s, col)
#|    return (fb, w, h, buf)
#|
#|
#|def bunker():
#|    b = bytearray(12 * 8)
#|    for y in range(8):
#|        for x in range(12):
#|            corner = (y == 0 and (x < 2 or x > 9)) or (y == 1 and (x == 0 or x == 11))
#|            hole = y >= 5 and 3 <= x <= 8
#|            b[y * 12 + x] = 0 if corner or hole else 1
#|    return b
#|
#|
#|BUNK_X = (34, 106, 178, 250)
#|BUNK_Y = 176
#|BUNK_C = rgb(90, 230, 120)
#|
#|
#|@native
#|def draw_bunkers(fb, bunks):
#|    for i in range(4):
#|        b = bunks[i]
#|        bx = BUNK_X[i]
#|        for y in range(8):
#|            for x in range(12):
#|                if b[y * 12 + x]:
#|                    fb.fill_rect(bx + x * 3, BUNK_Y + y * 3, 3, 3, BUNK_C)
#|
#|
#|def bunker_hit(bunks, x, y):
#|    """Träffar punkten ett skydd? Gör då ett hål och returnerar True."""
#|    for i in range(4):
#|        bx = BUNK_X[i]
#|        if bx <= x < bx + 36 and BUNK_Y <= y < BUNK_Y + 24:
#|            cx, cy = int(x - bx) // 3, int(y - BUNK_Y) // 3
#|            b = bunks[i]
#|            if b[cy * 12 + cx]:
#|                for dy in (-1, 0, 1):
#|                    for dx in (-1, 0, 1):
#|                        nx, ny = cx + dx, cy + dy
#|                        if 0 <= nx < 12 and 0 <= ny < 8 and (dx == 0 and dy == 0 or random.random() < 0.5):
#|                            b[ny * 12 + nx] = 0
#|                return True
#|    return False
#|
#|
#|def play(lcd, keys):
#|    spr = [[sprite(SPR_SQUID[f], PINK) for f in (0, 1)],
#|           [sprite(SPR_CRAB[f], TEAL) for f in (0, 1)],
#|           [sprite(SPR_OCTO[f], LIME) for f in (0, 1)]]
#|    kind_of_row = (0, 1, 1, 2, 2)
#|    ship = sprite(SPR_SHIP, SKY)
#|    ufo_s = sprite(SPR_UFO, CORAL)
#|    stars = Stars(40)
#|    parts = Particles(160)
#|    pops = Popups()
#|    shake = Shake()
#|    score, lives, wave = 0, 3, 0
#|    px = W / 2
#|    inv = 0
#|    cool = 0
#|    power, power_t = "", 0
#|    shield = False
#|    meter = 0
#|    beam = 0
#|    t = 0
#|    keys.wait_release()
#|    while True:                                           # en våg
#|        wave += 1
#|        alive = [[True] * 8 for _ in range(5)]
#|        fx, fy = 26.0, 30.0 + min(wave - 1, 5) * 8
#|        fdir = 1
#|        step_t = 0
#|        frame = 0
#|        shots, aliens_shots, drops = [], [], []
#|        bunks = [bunker() for _ in range(4)]
#|        ufo = None
#|        banner = 60
#|        while True:
#|            t0 = time.ticks_ms()
#|            keys.update()
#|            if keys.pause() and pause(lcd, keys):
#|                return score
#|            n_alive = sum(sum(1 for a in r if a) for r in alive)
#|            if n_alive == 0:
#|                break
#|            # --- Spelaren ---
#|            if keys.held(K0):
#|                px -= 3.2
#|            if keys.held(K1):
#|                px += 3.2
#|            px = max(14, min(W - 14, px))
#|            if cool > 0:
#|                cool -= 1
#|            if keys.held(K2) and cool == 0 and len(shots) < 6:
#|                shots.append([px, 206.0, 0.0])
#|                if power == "T":
#|                    shots.append([px, 206.0, -1.5])
#|                    shots.append([px, 206.0, 1.5])
#|                cool = 6 if power == "R" else 14
#|            if keys.pressed(K3) and meter >= 10:
#|                goal("invasion", 1)
#|                meter = 0
#|                beam = 20
#|                shake.hit(6)
#|            if power_t > 0:
#|                power_t -= 1
#|                if power_t == 0:
#|                    power = ""
#|            # --- Formationen ---
#|            step_t += 1
#|            interval = max(1, n_alive // 3)
#|            if step_t >= interval:
#|                step_t = 0
#|                frame ^= 1
#|                minx, maxx = W, 0
#|                maxy = 0
#|                for r in range(5):
#|                    for c in range(8):
#|                        if alive[r][c]:
#|                            x = fx + c * 28
#|                            minx = min(minx, x)
#|                            maxx = max(maxx, x + 24)
#|                            maxy = max(maxy, fy + r * 20 + 16)
#|                if (fdir > 0 and maxx + 4 > W - 4) or (fdir < 0 and minx - 4 < 4):
#|                    fdir = -fdir
#|                    fy += 8
#|                else:
#|                    fx += 4 * fdir
#|                if maxy >= BUNK_Y:                         # rensar skydden de rör vid
#|                    for i in range(4):
#|                        for y in range(8):
#|                            if BUNK_Y + y * 3 < maxy:
#|                                for x in range(12):
#|                                    bunks[i][y * 12 + x] = 0
#|                if maxy >= 206:
#|                    lives = 0
#|            if random.random() < 0.025 + wave * 0.005 and len(aliens_shots) < 2 + wave // 2:
#|                cols = [c for c in range(8) if any(alive[r][c] for r in range(5))]
#|                if cols:
#|                    c = random.choice(cols)
#|                    r = max(r for r in range(5) if alive[r][c])
#|                    aliens_shots.append([fx + c * 28 + 11, fy + r * 20 + 16])
#|            # --- UFO ---
#|            if ufo is None and random.random() < 0.003:
#|                d = random.choice((-1, 1))
#|                ufo = [-34.0 if d > 0 else W + 2.0, 1.6 * d]
#|            if ufo:
#|                ufo[0] += ufo[1]
#|                if ufo[0] < -40 or ufo[0] > W + 8:
#|                    ufo = None
#|            # --- Skott ---
#|            for s in shots:
#|                s[1] -= 7
#|                s[0] += s[2]
#|                if s[1] < 16 or bunker_hit(bunks, s[0], s[1]):
#|                    s[1] = -99
#|                    continue
#|                if ufo and ufo[0] <= s[0] <= ufo[0] + 32 and 18 <= s[1] <= 32:
#|                    pts = random.choice((50, 100, 150, 300))
#|                    score += pts
#|                    pops.add(ufo[0] + 16, 20, str(pts), CORAL)
#|                    parts.burst(ufo[0] + 16, 25, CORAL, 24, 3.5, 22)
#|                    shake.hit(5)
#|                    ufo = None
#|                    s[1] = -99
#|                    continue
#|                r = int((s[1] - fy) // 20)
#|                c = int((s[0] - fx) // 28)
#|                if 0 <= r < 5 and 0 <= c < 8 and alive[r][c]:
#|                    ax, ay = fx + c * 28, fy + r * 20
#|                    w = spr[kind_of_row[r]][0][1]
#|                    if ax <= s[0] <= ax + w and ay <= s[1] <= ay + 16:
#|                        alive[r][c] = False
#|                        s[1] = -99
#|                        score += I_POINTS[r]
#|                        meter = min(10, meter + 1)
#|                        parts.burst(ax + w / 2, ay + 8, I_COLS[r], 12, 2.5, 14)
#|                        pops.add(ax + w / 2, ay, str(I_POINTS[r]), I_COLS[r])
#|                        if random.random() < 0.08:
#|                            drops.append([ax + w / 2, ay + 8, random.choice("TRS")])
#|            shots = [s for s in shots if s[1] > 0]
#|            for s in aliens_shots:
#|                s[1] += 3.2 + wave * 0.2
#|                if bunker_hit(bunks, s[0], s[1]):
#|                    s[1] = H + 99
#|                elif inv == 0 and abs(s[0] - px) < 12 and 204 <= s[1] <= 220:
#|                    s[1] = H + 99
#|                    if shield:
#|                        shield = False
#|                        parts.burst(px, 210, TEAL, 14, 2.5, 14)
#|                    else:
#|                        lives -= 1
#|                        inv = 90
#|                        parts.burst(px, 210, SKY, 30, 4, 28)
#|                        parts.burst(px, 210, AMBER, 20, 3, 22)
#|                        shake.hit(9)
#|            aliens_shots = [s for s in aliens_shots if s[1] < H]
#|            for d in drops:
#|                d[1] += 1.6
#|                if abs(d[0] - px) < 16 and 204 <= d[1] <= 222:
#|                    d[1] = H + 99
#|                    if d[2] == "S":
#|                        shield = True
#|                        pops.add(px, 190, "SKOLD", TEAL)
#|                    else:
#|                        power, power_t = d[2], 420
#|                        pops.add(px, 190, "TRIPPEL" if d[2] == "T" else "SNABB", AMBER)
#|            drops = [d for d in drops if d[1] < H]
#|            # --- Superlaser ---
#|            if beam > 0:
#|                beam -= 1
#|                for r in range(5):
#|                    for c in range(8):
#|                        ax = fx + c * 28
#|                        w = spr[kind_of_row[r]][0][1]
#|                        if alive[r][c] and ax - 6 <= px <= ax + w + 6:
#|                            alive[r][c] = False
#|                            score += I_POINTS[r]
#|                            parts.burst(ax + w / 2, fy + r * 20 + 8, I_COLS[r], 10, 3, 14)
#|                aliens_shots = [s for s in aliens_shots if abs(s[0] - px) > 8]
#|                if ufo and ufo[0] <= px <= ufo[0] + 32:
#|                    score += 300
#|                    pops.add(ufo[0] + 16, 20, "300", CORAL)
#|                    ufo = None
#|            if inv > 0:
#|                inv -= 1
#|            if score >= 3000:
#|                goal("invasion", 2)
#|            if lives <= 0:
#|                lcd.show()
#|                time.sleep_ms(600)
#|                return score
#|
#|            # --- Rita ---
#|            ox, oy = shake.offset()
#|            lcd.fill(BLACK)
#|            stars.draw(lcd, 0.0, 0.3)
#|            for r in range(5):
#|                sp = spr[kind_of_row[r]][frame]
#|                for c in range(8):
#|                    if alive[r][c]:
#|                        lcd.blit(sp[0], int(fx + c * 28) + ox, int(fy + r * 20) + oy, 0)
#|            if ufo:
#|                lcd.blit(ufo_s[0], int(ufo[0]) + ox, 18 + oy, 0)
#|            draw_bunkers(lcd, bunks)
#|            for s in shots:
#|                lcd.fill_rect(int(s[0]) - 1 + ox, int(s[1]) + oy, 2, 7, YELLOW)
#|            for s in aliens_shots:
#|                zz = (t // 3) % 2
#|                lcd.fill_rect(int(s[0]) - 1 + zz + ox, int(s[1]) + oy, 2, 4, CORAL)
#|                lcd.fill_rect(int(s[0]) - zz + ox, int(s[1]) + 4 + oy, 2, 4, CORAL)
#|            for d in drops:
#|                c = {"T": CORAL, "R": AMBER, "S": TEAL}[d[2]]
#|                lcd.fill_rect(int(d[0]) - 6, int(d[1]) - 5, 12, 10, c)
#|                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
#|            if beam > 0:
#|                w = 4 + (beam % 3) * 2
#|                lcd.fill_rect(int(px) - w // 2 - 2, 16, w + 4, 196, PINK)
#|                lcd.fill_rect(int(px) - w // 2, 16, w, 196, WHITE)
#|            if inv == 0 or (t // 4) % 2:
#|                lcd.blit(ship[0], int(px) - 13 + ox, 206 + oy, 0)
#|                if shield:
#|                    lcd.ellipse(int(px) + ox, 212 + oy, 18, 11, TEAL)
#|            parts.draw(lcd, ox, oy)
#|            pops.draw(lcd, ox, oy)
#|            lcd.fill_rect(0, 0, W, 14, BG)
#|            lcd.text(str(score), 4, 3, WHITE)
#|            lcd.text("VAG %d" % wave, 132, 3, GRAY)
#|            for i in range(lives):
#|                lcd.blit(ship[0], W - 30 - i * 30, 0, 0)
#|            lcd.fill_rect(4, H - 6, 60, 4, LINE)
#|            lcd.fill_rect(4, H - 6, meter * 6, 4, PINK if meter >= 10 else VIOLET)
#|            if meter >= 10 and (t // 6) % 2:
#|                lcd.text("3 LASER!", 70, H - 9, PINK)
#|            if power:
#|                lcd.text("TRIPPEL" if power == "T" else "SNABB", W - 60, H - 9, AMBER)
#|            if banner > 0:
#|                banner -= 1
#|                stext(lcd, "VAG %d" % wave, 110, WHITE, 3)
#|            lcd.show()
#|            t += 1
#|            wait(t0)
#|        score += 100 * wave
#|        if wave >= 3:
#|            goal("invasion", 0)
#|        pops.add(W // 2, 130, "VAG KLAR +%d" % (100 * wave), LIME, 2)
#@@ kross
#|# KROSS: 0 vänster, 1 höger, 2/3 skjut iväg bollen (2 = laser).
#|K_LEVELS = (
#|    ("1111111111", "2222222222", "3333333333", "4444444444", "5555555555"),
#|    ("..AAAAAA..", ".A111111A.", "A11XXXX11A", "A11111111A", ".AAAAAAAA."),
#|    ("M..1111..M", "M.1BBBB1.M", "M.1B33B1.M", "M.1BBBB1.M", "M..1111..M"),
#|    ("X1X1X1X1X1", "1A1A1A1A1A", "2B2B2B2B2B", "1A1A1A1A1A", "X1X1X1X1X1"),
#|    ("....11....", "...1221...", "..123321..", ".12344321.", "1234554321", ".AAAAAAAA.", "MM......MM"),
#|    ("AXAXAXAXAX", "1111111111", "MMMM..MMMM", "2222222222", "B........B", "BBBBBBBBBB"),
#|)
#|BR_RAW = ((255, 95, 100), (255, 170, 60), (255, 225, 70), (125, 230, 110), (80, 165, 255))
#|BR_N = [rgb(*c) for c in BR_RAW]
#|BR_L = [mix(c, (255, 255, 255), 0.5) for c in BR_RAW]
#|BR_D = [mix(c, (0, 0, 0), 0.4) for c in BR_RAW]
#|BR_HARD = (rgb(120, 70, 210), rgb(160, 110, 255), rgb(200, 160, 255))
#|BR_METAL = rgb(150, 155, 175)
#|BR_X = rgb(255, 120, 40)
#|B_BW, B_BH = 30, 11
#|B_TOP = 26
#|PADY = 222
#|
#|
#|def play(lcd, keys):
#|    parts = Particles(140)
#|    pops = Popups()
#|    shake = Shake()
#|    score, lives, lvl = 0, 3, 0
#|    bg = [mix((18, 14, 40), (8, 22, 44), y / (H - 1)) for y in range(H)]
#|    while True:                                   # en bana
#|        layout = K_LEVELS[lvl % len(K_LEVELS)]
#|        speed0 = min(3.6 + lvl * 0.3, 6.0)
#|        typ = bytearray(10 * 8)                   # 0 ingen, 1-5 vanlig, 6 hård, 8 metall, 9 sprängsten
#|        hp = bytearray(10 * 8)
#|        for r, row in enumerate(layout):
#|            for c, ch in enumerate(row):
#|                i = r * 10 + c
#|                if ch in "12345":
#|                    typ[i], hp[i] = int(ch), 1
#|                elif ch == "A":
#|                    typ[i], hp[i] = 6, 2
#|                elif ch == "B":
#|                    typ[i], hp[i] = 6, 3
#|                elif ch == "M":
#|                    typ[i], hp[i] = 8, 255
#|                elif ch == "X":
#|                    typ[i], hp[i] = 9, 1
#|        pw, pdx = 48, (W - 48) / 2
#|        balls = [[0.0, 0.0, 0.0, 0.0]]
#|        attached = True
#|        drops = []
#|        lasers = []
#|        effects = {}                              # namn -> bilder kvar
#|        banner = 50
#|        t = 0
#|        keys.wait_release()
#|
#|        def left():
#|            for i in range(80):
#|                if typ[i] and typ[i] != 8:
#|                    return True
#|            return False
#|
#|        def destroy(i, chain=0):
#|            nonlocal score
#|            tp = typ[i]
#|            typ[i] = 0
#|            hp[i] = 0
#|            r, c = i // 10, i % 10
#|            bx, by = c * 32 + 1 + B_BW / 2, B_TOP + r * 13 + B_BH / 2
#|            col = BR_N[tp - 1] if tp <= 5 else (BR_X if tp == 9 else BR_HARD[1])
#|            parts.burst(bx, by, col, 8, 2.5, 14)
#|            gain = 10 if tp <= 5 else (30 if tp == 6 else 40)
#|            score += gain
#|            if random.random() < 0.14:
#|                drops.append([bx, by, random.choice("WMSL+W")])
#|            if tp == 9:                               # sprängsten tar grannarna
#|                shake.hit(5)
#|                parts.burst(bx, by, AMBER, 18, 4, 18)
#|                for dr in (-1, 0, 1):
#|                    for dc in (-1, 0, 1):
#|                        nr, nc = r + dr, c + dc
#|                        if 0 <= nr < 8 and 0 <= nc < 10:
#|                            j = nr * 10 + nc
#|                            if typ[j] and typ[j] != 8:
#|                                destroy(j, chain + 1)
#|
#|        def hit_brick(x, y):
#|            r = int((y - B_TOP) // 13)
#|            c = int(x // 32)
#|            if 0 <= r < 8 and 0 <= c < 10:
#|                i = r * 10 + c
#|                if typ[i]:
#|                    if typ[i] != 8:
#|                        hp[i] -= 1
#|                        if hp[i] == 0:
#|                            destroy(i)
#|                    return True
#|            return False
#|
#|        while True:
#|            t0 = time.ticks_ms()
#|            keys.update()
#|            if keys.pause() and pause(lcd, keys):
#|                return score
#|            wide = effects.get("W", 0) > 0
#|            pw = 72 if wide else 48
#|            if keys.held(K0):
#|                pdx -= 6
#|            if keys.held(K1):
#|                pdx += 6
#|            pdx = max(0, min(W - pw, pdx))
#|            slow = 0.7 if effects.get("S", 0) else 1.0
#|            spd = speed0 * slow
#|            if attached:
#|                balls = [[pdx + pw / 2, PADY - 5.0, 0.0, 0.0]]
#|                if banner == 0 and (keys.pressed(K2) or keys.pressed(K3)):
#|                    attached = False
#|                    a = random.uniform(-0.5, 0.5)
#|                    balls[0][2], balls[0][3] = math.sin(a) * spd, -math.cos(a) * spd
#|            elif effects.get("L", 0) and keys.pressed(K2):
#|                lasers.append([pdx + 4, PADY - 4.0])
#|                lasers.append([pdx + pw - 4, PADY - 4.0])
#|            for k in list(effects):
#|                effects[k] -= 1
#|                if effects[k] <= 0:
#|                    del effects[k]
#|            # --- Bollar ---
#|            keep = []
#|            for b in balls:
#|                if attached:
#|                    keep.append(b)
#|                    continue
#|                sp = math.sqrt(b[2] * b[2] + b[3] * b[3])
#|                if sp > 0:
#|                    b[2] *= spd / sp
#|                    b[3] *= spd / sp
#|                for _ in range(2):
#|                    b[0] += b[2] / 2
#|                    if b[0] < 3 or b[0] > W - 3:
#|                        b[2] = -b[2]
#|                        b[0] = max(3, min(W - 3, b[0]))
#|                    elif hit_brick(b[0] + (3 if b[2] > 0 else -3), b[1]):
#|                        b[2] = -b[2]
#|                        b[0] += b[2] / 2
#|                    b[1] += b[3] / 2
#|                    if b[1] < 20:
#|                        b[3] = abs(b[3])
#|                    elif hit_brick(b[0], b[1] + (3 if b[3] > 0 else -3)):
#|                        b[3] = -b[3]
#|                        b[1] += b[3] / 2
#|                if b[3] > 0 and PADY - 4 <= b[1] <= PADY + 4 and pdx - 3 <= b[0] <= pdx + pw + 3:
#|                    rel = (b[0] - (pdx + pw / 2)) / (pw / 2)
#|                    a = max(-1.0, min(1.0, rel)) * 1.1
#|                    b[2], b[3] = math.sin(a) * spd, -math.cos(a) * spd
#|                    b[1] = PADY - 5
#|                if b[1] < H + 5:
#|                    keep.append(b)
#|            balls = keep
#|            if not balls:
#|                lives -= 1
#|                shake.hit(8)
#|                if lives <= 0:
#|                    return score
#|                attached = True
#|                effects = {}
#|                balls = [[0.0, 0.0, 0.0, 0.0]]
#|            for l in lasers:
#|                l[1] -= 7
#|                if hit_brick(l[0], l[1]):
#|                    l[1] = -9
#|            lasers = [l for l in lasers if l[1] > 18]
#|            for d in drops:
#|                d[1] += 1.8
#|                if PADY - 6 <= d[1] <= PADY + 6 and pdx - 6 <= d[0] <= pdx + pw + 6:
#|                    d[1] = H + 99
#|                    score += 50
#|                    k = d[2]
#|                    if k == "M" and balls and not attached:
#|                        b = balls[0]
#|                        for a in (-0.6, 0.6):
#|                            balls.append([b[0], b[1], math.sin(a) * spd, -math.cos(a) * spd])
#|                        pops.add(d[0], PADY - 20, "MULTIBOLL", PINK)
#|                        goal("kross", 1)
#|                    elif k == "+":
#|                        lives += 1
#|                        pops.add(d[0], PADY - 20, "+1 LIV", LIME)
#|                    else:
#|                        effects[k] = 500
#|                        pops.add(d[0], PADY - 20, {"W": "BRED", "S": "LANGSAM", "L": "LASER"}.get(k, ""), AMBER)
#|            drops = [d for d in drops if d[1] < H]
#|            if not left():
#|                score += 500
#|                lvl += 1
#|                if lvl >= 2:
#|                    goal("kross", 0)
#|                if lvl >= 5:
#|                    goal("kross", 2)
#|                pops.add(W // 2, 120, "BANAN KLAR! +500", LIME, 2)
#|                for _ in range(40):
#|                    t1 = time.ticks_ms()
#|                    gradient(lcd, bg)
#|                    pops.draw(lcd)
#|                    parts.draw(lcd)
#|                    lcd.show()
#|                    wait(t1)
#|                break
#|            if banner > 0:
#|                banner -= 1
#|
#|            # --- Rita ---
#|            ox, oy = shake.offset()
#|            gradient(lcd, bg)
#|            for i in range(80):
#|                tp = typ[i]
#|                if not tp:
#|                    continue
#|                x = (i % 10) * 32 + 1 + ox
#|                y = B_TOP + (i // 10) * 13 + oy
#|                if tp <= 5:
#|                    lcd.fill_rect(x, y, B_BW, B_BH, BR_N[tp - 1])
#|                    lcd.hline(x, y, B_BW, BR_L[tp - 1])
#|                    lcd.hline(x, y + B_BH - 1, B_BW, BR_D[tp - 1])
#|                elif tp == 6:
#|                    lcd.fill_rect(x, y, B_BW, B_BH, BR_HARD[min(2, hp[i] - 1)])
#|                    lcd.rect(x, y, B_BW, B_BH, WHITE if hp[i] >= 3 else BR_HARD[2])
#|                elif tp == 8:
#|                    lcd.fill_rect(x, y, B_BW, B_BH, BR_METAL)
#|                    lcd.hline(x, y + 2, B_BW, WHITE)
#|                    lcd.rect(x, y, B_BW, B_BH, DIM)
#|                else:
#|                    lcd.fill_rect(x, y, B_BW, B_BH, BR_X if (t // 6) % 2 else CORAL)
#|                    lcd.text("X", x + 11, y + 2, WHITE)
#|            for d in drops:
#|                c = {"W": SKY, "M": PINK, "S": TEAL, "L": CORAL, "+": LIME}[d[2]]
#|                lcd.fill_rect(int(d[0]) - 8, int(d[1]) - 5, 16, 10, c)
#|                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
#|            for l in lasers:
#|                lcd.fill_rect(int(l[0]) - 1, int(l[1]), 2, 8, CORAL)
#|            pc = CORAL if effects.get("L", 0) else SKY
#|            lcd.fill_rect(int(pdx) + ox, PADY + oy, pw, 7, pc)
#|            lcd.hline(int(pdx) + 2 + ox, PADY + 1 + oy, pw - 4, WHITE)
#|            for b in balls:
#|                lcd.ellipse(int(b[0]) + ox, int(b[1]) + oy, 3, 3, WHITE, True)
#|            parts.draw(lcd, ox, oy)
#|            pops.draw(lcd, ox, oy)
#|            lcd.fill_rect(0, 0, W, 16, BG)
#|            lcd.text(str(score), 4, 4, WHITE)
#|            lcd.text("BANA %d" % (lvl + 1), 130, 4, AMBER)
#|            for i in range(lives):
#|                lcd.ellipse(W - 10 - i * 12, 8, 4, 4, CORAL, True)
#|            if banner > 0:
#|                stext(lcd, "BANA %d" % (lvl + 1), 130, WHITE, 3)
#|            elif attached and (t // 10) % 2 == 0:
#|                ctext(lcd, "2  skjut ivag bollen", 170, GRAY)
#|            lcd.show()
#|            t += 1
#|            wait(t0)
#@@ kurvan
#|# KURVAN: P1 0/3, P2 1/2.
#|KY0 = 20
#|KW, KH = W // 2, (H - KY0) // 2
#|K_SPEED = 1.5
#|K_TURN = 0.085
#|
#|
#|def play(lcd, keys):
#|    mode = choose(lcd, keys, "KURVAN", ("MOT DATORN", "MOT 2 DATORER", "2 SPELARE"), TEAL,
#|                  "Sist kvar vinner rundan. Forst till 5!")
#|    if mode is None:
#|        return None
#|    n = 3 if mode == 1 else 2
#|    cpu = [False, mode != 2, True][:n]
#|    names = ["DU" if mode != 2 else "SPELARE 1", "DATORN" if mode == 0 else ("DATOR 1" if mode == 1 else "SPELARE 2"),
#|             "DATOR 2"][:n]
#|    ctrl = [(K0, K3), (K1, K2), None]
#|    points = [0] * n
#|    target = 5
#|    grid = bytearray(KW * KH)
#|
#|    def free(px, py):
#|        if px < 1 or py < KY0 + 1 or px >= W - 1 or py >= H - 1:
#|            return False
#|        return grid[(int(py - KY0) >> 1) * KW + (int(px) >> 1)] == 0
#|
#|    def look(p, turn, steps=34):
#|        x, y, a = p[0], p[1], p[2]
#|        for i in range(steps):
#|            a += turn * K_TURN
#|            x += math.cos(a) * K_SPEED * 2
#|            y += math.sin(a) * K_SPEED * 2
#|            if not free(x, y):
#|                return i
#|        return steps
#|
#|    while True:                                    # en runda
#|        for i in range(len(grid)):
#|            grid[i] = 0
#|        pl = []
#|        for i in range(n):
#|            while True:
#|                x = random.uniform(50, W - 50)
#|                y = random.uniform(KY0 + 40, H - 40)
#|                if all((x - q[0]) ** 2 + (y - q[1]) ** 2 > 3600 for q in pl):
#|                    break
#|            a = math.atan2(KY0 + (H - KY0) / 2 - y, W / 2 - x) + random.uniform(-0.8, 0.8)
#|            pl.append([x, y, a, True, random.randint(60, 140), 0, 0, x, y])   # x,y,vinkel,lever,till glapp,glapp,ai-sväng,förra x,y
#|        for c in range(75):                        # nedräkning
#|            t0 = time.ticks_ms()
#|            keys.update()
#|            k_field(lcd, names, points, n)
#|            for i, p in enumerate(pl):
#|                ex, ey = p[0] + math.cos(p[2]) * 14, p[1] + math.sin(p[2]) * 14
#|                lcd.line(int(p[0]), int(p[1]), int(ex), int(ey), K_COLS[i])
#|                lcd.ellipse(int(p[0]), int(p[1]), 3, 3, K_COLS[i], True)
#|                if not cpu[i] and (c // 8) % 2 == 0:
#|                    lab = "%d/%d" % ctrl[i]
#|                    lcd.text(lab, int(p[0]) - 12, int(p[1]) + 8, WHITE)
#|            stext(lcd, str(3 - c // 25), 100, WHITE, 5)
#|            lcd.show()
#|            wait(t0)
#|        k_field(lcd, names, points, n)
#|        t = 0
#|        keys.wait_release()
#|        while True:
#|            t0 = time.ticks_ms()
#|            keys.update()
#|            if keys.pause() and pause(lcd, keys):
#|                return points[0]
#|            for i, p in enumerate(pl):
#|                if not p[3]:
#|                    continue
#|                if cpu[i]:
#|                    if t % 3 == i % 3:
#|                        best, bt = -1, 0
#|                        for turn in (0, -1, 1):
#|                            s = look(p, turn) + random.random() * 2
#|                            if s > best:
#|                                best, bt = s, turn
#|                        p[6] = bt
#|                    turn = p[6]
#|                else:
#|                    turn = (-1 if keys.held(ctrl[i][0]) else 0) + (1 if keys.held(ctrl[i][1]) else 0)
#|                p[2] += turn * K_TURN
#|                p[7], p[8] = p[0], p[1]
#|                p[0] += math.cos(p[2]) * K_SPEED
#|                p[1] += math.sin(p[2]) * K_SPEED
#|                ax = p[0] + math.cos(p[2]) * 2.5
#|                ay = p[1] + math.sin(p[2]) * 2.5
#|                if not free(ax, ay):
#|                    p[3] = False
#|                    lcd.ellipse(int(p[0]), int(p[1]), 6, 6, WHITE, False)
#|                    lcd.ellipse(int(p[0]), int(p[1]), 4, 4, K_COLS[i], True)
#|                    continue
#|                # Glapp i svansen ibland
#|                p[4] -= 1
#|                if p[4] <= 0:
#|                    p[5] = 7
#|                    p[4] = random.randint(70, 150)
#|                if p[5] > 0:
#|                    p[5] -= 1
#|                    if grid[(int(p[8] - KY0) >> 1) * KW + (int(p[7]) >> 1)] == 0:
#|                        lcd.fill_rect(int(p[7]) - 1, int(p[8]) - 1, 3, 3, BG)
#|                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, WHITE)
#|                else:
#|                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, K_COLS[i])
#|                    grid[(int(p[1] - KY0) >> 1) * KW + (int(p[0]) >> 1)] = i + 1
#|            alive = [i for i, p in enumerate(pl) if p[3]]
#|            hud_k(lcd, names, points, n)
#|            lcd.show()
#|            t += 1
#|            wait(t0, 25)
#|            if len(alive) <= 1:
#|                if alive:
#|                    points[alive[0]] += 1
#|                    if alive[0] == 0 and mode != 2:
#|                        goal("kurvan", 0)
#|                    msg = "%s TAR RUNDAN" % names[alive[0]]
#|                    col = K_COLS[alive[0]]
#|                else:
#|                    msg, col = "OAVGJORT", GRAY
#|                lcd.fill_rect(30, 96, 260, 44, BG)
#|                lcd.rect(30, 96, 260, 44, col)
#|                ctext(lcd, msg, 106, col, 1 if len(msg) > 18 else 2)
#|                ctext(lcd, "  ".join("%d" % q for q in points), 126, WHITE)
#|                hud_k(lcd, names, points, n)
#|                lcd.show()
#|                time.sleep_ms(1600)
#|                break
#|        if max(points) >= target:
#|            w = points.index(max(points))
#|            if w == 0 and mode == 0:
#|                goal("kurvan", 1)
#|            if w == 0 and mode == 1:
#|                goal("kurvan", 2)
#|            return ("%s VANN!" % names[w], points[0], "kurvan" if mode != 2 else None,
#|                    "Dina vunna rundor:", False, str)
#|
#|
#|def k_field(lcd, names, points, n):
#|    lcd.fill(BG)
#|    lcd.rect(0, KY0, W, H - KY0, LINE)
#|    lcd.rect(1, KY0 + 1, W - 2, H - KY0 - 2, LINE)
#|    hud_k(lcd, names, points, n)
#|
#|
#|def hud_k(lcd, names, points, n):
#|    lcd.fill_rect(0, 0, W, KY0, BG)
#|    for i in range(n):
#|        x = 6 + i * 106
#|        lcd.fill_rect(x, 6, 8, 8, K_COLS[i])
#|        lcd.text("%s %d" % (names[i], points[i]), x + 12, 6, K_COLS[i])
#@@ slut
