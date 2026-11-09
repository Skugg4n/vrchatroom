# PICO SPEL - massor av spel i en enda fil
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Spara filen som main.py på Picon så startar den av sig själv.
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
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


# ---------------------------------------------------------------
# Knappar
# ---------------------------------------------------------------
K0, K1, K2, K3 = 0, 1, 2, 3


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


SCORES = load_scores()


def save_scores():
    try:
        with open(SAVE, "w") as f:
            json.dump(SCORES, f)
    except Exception:
        pass


def submit(key, score):
    """Returnerar (rekord, nytt_rekord?)."""
    best = SCORES.get(key, 0)
    if score > best:
        SCORES[key] = score
        save_scores()
        return score, True
    return best, False


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


def game_over(lcd, keys, key, score, col, head="GAME OVER", sub=""):
    """Slutskärm. True = spela igen."""
    best, new = submit(key, score)
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
        s = str(score)
        stext(lcd, s, 90, WHITE, 6 if len(s) <= 5 else 4)
        if new:
            if (t // 7) % 2 == 0:
                ctext(lcd, "NYTT REKORD!", 156, YELLOW, 2)
        else:
            ctext(lcd, "Rekord: %d" % best, 160, GRAY)
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


# ===============================================================
# TETRIS
#   0 vänster   1 höger   2 vrid   3 släpp (direkt ner)
# ===============================================================
TC = 11                         # rutstorlek
TW, TH = 10, 20
TX, TY = 105, 10
SHAPES = (
    ((-1, 0), (0, 0), (1, 0), (2, 0)),      # I
    ((0, 0), (1, 0), (0, 1), (1, 1)),       # O
    ((-1, 0), (0, 0), (1, 0), (0, -1)),     # T
    ((-1, 0), (0, 0), (0, -1), (1, -1)),    # S
    ((-1, -1), (0, -1), (0, 0), (1, 0)),    # Z
    ((-1, -1), (-1, 0), (0, 0), (1, 0)),    # J
    ((1, -1), (-1, 0), (0, 0), (1, 0)),     # L
)
T_RAW = ((40, 215, 235), (255, 210, 60), (175, 95, 255), (110, 225, 100),
         (255, 85, 95), (75, 125, 255), (255, 150, 50))
T_FILL = [rgb(*c) for c in T_RAW]
T_LIGHT = [mix(c, (255, 255, 255), 0.5) for c in T_RAW]
T_DARK = [mix(c, (0, 0, 0), 0.45) for c in T_RAW]
T_GHOST = [mix(c, C_BG, 0.6) for c in T_RAW]
T_BOARD = rgb(16, 16, 38)
T_GRID = rgb(28, 28, 58)
T_BG = [mix((20, 18, 50), (8, 30, 50), y / (H - 1)) for y in range(H)]
T_POINTS = (0, 100, 300, 500, 800)


@native
def t_cell(fb, x, y, ci, s=10):
    fb.fill_rect(x, y, s, s, T_FILL[ci])
    fb.hline(x, y, s, T_LIGHT[ci])
    fb.vline(x, y, s, T_LIGHT[ci])
    fb.hline(x, y + s - 1, s, T_DARK[ci])
    fb.vline(x + s - 1, y, s, T_DARK[ci])
    if s > 6:
        fb.fill_rect(x + 2, y + 2, 2, 2, WHITE)


@native
def t_board(fb, board):
    for y in range(TH):
        row = board[y]
        for x in range(TW):
            v = row[x]
            if v:
                t_cell(fb, TX + x * TC, TY + y * TC, v - 1)


def tetris(lcd, keys):
    board = [bytearray(TW) for _ in range(TH)]
    bag = []

    def nxt():
        if not bag:
            bag.extend(shuffled(7))
        return bag.pop()

    def fits(cells, px, py):
        for cx, cy in cells:
            x = px + cx
            y = py + cy
            if x < 0 or x >= TW or y >= TH:
                return False
            if y >= 0 and board[y][x]:
                return False
        return True

    queue = [nxt(), nxt(), nxt()]
    cur = nxt()
    cells = SHAPES[cur]
    px, py = 4, 1
    score = lines = 0
    level = 1
    fall = 0
    lock = 0
    resets = 0
    combo = -1
    parts = Particles(160)
    pops = Popups()
    shake = Shake()
    banner, btxt, bcol = 0, "", WHITE
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return score
        moved = False
        if keys.repeat(K0, 8, 2) and fits(cells, px - 1, py):
            px -= 1
            moved = True
        if keys.repeat(K1, 8, 2) and fits(cells, px + 1, py):
            px += 1
            moved = True
        if keys.pressed(K2) and cur != 1:
            r = tuple((-cy, cx) for cx, cy in cells)
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)):
                if fits(r, px + dx, py + dy):
                    cells = r
                    px += dx
                    py += dy
                    moved = True
                    break
        if moved and lock and resets < 15:        # man hinner flytta lite på marken
            lock = 1
            resets += 1
        drop = False
        if keys.pressed(K3):                      # släpp direkt
            n = 0
            while fits(cells, px, py + 1):
                py += 1
                n += 1
            score += n * 2
            drop = True
            shake.hit(3)
            for cx, cy in cells:
                parts.burst(TX + (px + cx) * TC + 5, TY + (py + cy) * TC + 10,
                            T_LIGHT[cur], 2, 1.5, 10)
        # Tyngdkraft
        fall += 1
        interval = max(2, int(30 * (0.84 ** (level - 1))))
        if fall >= interval:
            fall = 0
            if fits(cells, px, py + 1):
                py += 1
        on_ground = not fits(cells, px, py + 1)
        lock = lock + 1 if on_ground else 0
        if on_ground and (lock > 16 or drop):
            for cx, cy in cells:
                if py + cy >= 0:
                    board[py + cy][px + cx] = cur + 1
            full = []
            for y in range(TH):
                if all(board[y]):
                    full.append(y)
            if full:
                combo += 1
                for k in range(8):                # blinka raderna
                    gradient(lcd, T_BG)
                    lcd.fill_rect(TX - 1, TY - 1, TW * TC + 1, TH * TC + 1, T_BOARD)
                    t_board(lcd, board)
                    for y in full:
                        if k % 2 == 0:
                            lcd.fill_rect(TX, TY + y * TC, TW * TC - 1, TC - 1, WHITE)
                    lcd.show()
                    time.sleep_ms(30)
                for y in full:
                    for x in range(TW):
                        parts.burst(TX + x * TC + 5, TY + y * TC + 5, T_FILL[board[y][x] - 1], 3, 3, 16)
                    del board[y]
                    board.insert(0, bytearray(TW))
                gain = T_POINTS[len(full)] * level + max(0, combo) * 50 * level
                score += gain
                lines += len(full)
                new_level = lines // 10 + 1
                pops.add(TX + TW * TC // 2, TY + full[0] * TC, "+%d" % gain, AMBER)
                if len(full) == 4:
                    banner, btxt, bcol = 50, "TETRIS!", PINK
                    shake.hit(8)
                elif combo >= 2:
                    banner, btxt, bcol = 35, "KOMBO x%d" % combo, TEAL
                if new_level > level:
                    level = new_level
                    banner, btxt, bcol = 50, "NIVA %d" % level, LIME
            else:
                combo = -1
            cur = queue.pop(0)
            queue.append(nxt())
            cells = SHAPES[cur]
            px, py = 4, 1
            lock = resets = 0
            fall = 0
            if not fits(cells, px, py):
                for k in range(20):
                    lcd.fill_rect(TX, TY + (19 - k) * TC, TW * TC - 1, TC - 1, DIM)
                    lcd.show()
                    time.sleep_ms(30)
                return score

        # --- Rita ---
        ox, oy = shake.offset()
        gradient(lcd, T_BG)
        lcd.fill_rect(TX - 4 + ox, TY - 4 + oy, TW * TC + 7, TH * TC + 7, LINE)
        lcd.fill_rect(TX - 1 + ox, TY - 1 + oy, TW * TC + 1, TH * TC + 1, T_BOARD)
        for x in range(1, TW):
            lcd.vline(TX + x * TC - 1 + ox, TY + oy, TH * TC - 1, T_GRID)
        for y in range(1, TH):
            lcd.hline(TX + ox, TY + y * TC - 1 + oy, TW * TC - 1, T_GRID)
        if ox or oy:
            for y in range(TH):
                for x in range(TW):
                    v = board[y][x]
                    if v:
                        t_cell(lcd, TX + x * TC + ox, TY + y * TC + oy, v - 1)
        else:
            t_board(lcd, board)
        gy = py
        while fits(cells, px, gy + 1):
            gy += 1
        for cx, cy in cells:
            if gy + cy >= 0:
                lcd.rect(TX + (px + cx) * TC, TY + (gy + cy) * TC, 10, 10, T_GHOST[cur])
        for cx, cy in cells:
            if py + cy >= 0:
                t_cell(lcd, TX + (px + cx) * TC + ox, TY + (py + cy) * TC + oy, cur)
        # Nästa bitar
        lcd.fill_rect(228, 10, 84, 136, PANEL)
        lcd.text("NASTA", 250, 16, GRAY)
        for i, q in enumerate(queue):
            s = 10 if i == 0 else 7
            bx, by = 262, 46 + i * 34 + (0 if i == 0 else 6)
            for cx, cy in SHAPES[q]:
                t_cell(lcd, bx + cx * (s + 1), by + cy * (s + 1), q, s)
        # Poäng
        lcd.fill_rect(8, 10, 88, 160, PANEL)
        lcd.text("POANG", 16, 18, GRAY)
        big(lcd, str(score), 16, 30, WHITE, 2 if score < 100000 else 1)
        lcd.text("RADER", 16, 62, GRAY)
        big(lcd, str(lines), 16, 74, WHITE, 2)
        lcd.text("NIVA", 16, 106, GRAY)
        big(lcd, str(level), 16, 118, LIME, 3)
        lcd.text("REKORD", 16, 150, DIM)
        lcd.text(str(SCORES.get("tetris", 0)), 16, 160, DIM)
        lcd.text("0 <  > 1", 18, 196, DIM)
        lcd.text("3 slapp", 18, 208, DIM)
        lcd.text("2 vrid", 18, 220, DIM)
        parts.draw(lcd, ox, oy)
        pops.draw(lcd, ox, oy)
        if banner > 0:
            banner -= 1
            stext(lcd, btxt, 100, bcol, 3, TX + TW * TC // 2)
        lcd.show()
        t += 1
        wait(t0)


def icon_tetris(fb, x, y, t):
    stack = ((0, 5, 3), (1, 5, 3), (2, 5, 5), (3, 5, 1), (4, 5, 1), (6, 5, 2), (7, 5, 4),
             (8, 5, 4), (0, 4, 3), (1, 4, 5), (6, 4, 2), (7, 4, 2), (8, 4, 6), (9, 5, 6))
    fb.fill_rect(x, y, 160, 72, T_BOARD)
    ox = x + 25
    for cx, cy, ci in stack:
        t_cell(fb, ox + cx * 11, y + cy * 11 + 5, ci)
    fy = (t // 5) % 6
    for cx, cy in SHAPES[0]:
        if fy - 1 + cy >= 0:
            t_cell(fb, ox + (4 + cx) * 11, y + (fy - 1 + cy) * 11 + 5, 0)


# ===============================================================
# 2048
#   pilarna i hörnen: 0 upp, 1 höger, 2 ner, 3 vänster
# ===============================================================
G_N = 4
G_S = 46
G_GAP = 6
G_X = (W - (G_N * G_S + (G_N + 1) * G_GAP)) // 2
G_Y = 16
G_BOARD = rgb(60, 52, 80)
G_EMPTY = rgb(80, 72, 104)
G_RAW = ((238, 228, 218), (237, 224, 200), (242, 177, 121), (245, 149, 99), (246, 124, 95),
         (246, 94, 59), (237, 207, 114), (237, 204, 97), (237, 200, 80), (237, 197, 63),
         (237, 194, 46), (170, 110, 255), (120, 90, 255), (60, 200, 220))
G_COL = [rgb(*c) for c in G_RAW]
G_TXT_DARK = rgb(119, 110, 101)
G_BGC = [mix((30, 22, 46), (16, 26, 46), y / (H - 1)) for y in range(H)]


def g_tile(fb, x, y, e, s=G_S):
    """Ritar en bricka med värdet 2**e."""
    col = G_COL[min(e - 1, len(G_COL) - 1)]
    fb.fill_rect(x + 2, y, s - 4, s, col)
    fb.fill_rect(x, y + 2, s, s - 4, col)
    v = str(1 << e)
    sc = 3 if len(v) == 1 else (2 if len(v) <= 3 else 1)
    if s < G_S:
        sc = max(1, sc - 1)
    tc = G_TXT_DARK if e <= 2 else WHITE
    ctext(fb, v, y + s // 2 - 4 * sc, tc, sc, x + s // 2)


def g2048(lcd, keys):
    grid = [[0] * G_N for _ in range(G_N)]
    score = 0
    won = False
    pops = Popups()
    parts = Particles(80)

    def spawn():
        empty = [(r, c) for r in range(G_N) for c in range(G_N) if grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            grid[r][c] = 1 if random.random() < 0.9 else 2
            return (r, c)
        return None

    def cell_xy(r, c):
        return G_X + G_GAP + c * (G_S + G_GAP), G_Y + G_GAP + r * (G_S + G_GAP)

    def can_move():
        for r in range(G_N):
            for c in range(G_N):
                if grid[r][c] == 0:
                    return True
                if c + 1 < G_N and grid[r][c] == grid[r][c + 1]:
                    return True
                if r + 1 < G_N and grid[r][c] == grid[r + 1][c]:
                    return True
        return False

    def move(d):
        """d: 0 upp, 1 höger, 2 ner, 3 vänster. Returnerar (rörelser, sammanslagna, poäng)."""
        nonlocal grid
        dr, dc = ((-1, 0), (0, 1), (1, 0), (0, -1))[d]
        moves = []
        merged = []
        gain = 0
        new = [[0] * G_N for _ in range(G_N)]
        for i in range(G_N):
            # gå längs raden/kolumnen från den sida brickorna glider mot
            if dr:
                line = [(r, i) for r in (range(G_N) if dr < 0 else range(G_N - 1, -1, -1))]
            else:
                line = [(i, c) for c in (range(G_N) if dc < 0 else range(G_N - 1, -1, -1))]
            target = 0
            last = None                       # (värde, index i linjen, kan slås ihop)
            for (r, c) in line:
                v = grid[r][c]
                if not v:
                    continue
                if last and last[0] == v and last[2]:
                    tr, tc = line[last[1]]
                    new[tr][tc] = v + 1
                    gain += 1 << (v + 1)
                    merged.append((tr, tc))
                    moves.append((r, c, tr, tc, v))
                    last = (v + 1, last[1], False)
                else:
                    tr, tc = line[target]
                    new[tr][tc] = v
                    moves.append((r, c, tr, tc, v))
                    last = (v, target, True)
                    target += 1
        changed = any(m[0] != m[2] or m[1] != m[3] for m in moves)
        if changed:
            grid = new
        return (moves if changed else None), merged, gain

    spawn()
    spawn()
    pop = []
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return score
        d = -1
        for k, dd in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
            if keys.pressed(k):
                d = dd
        if d >= 0:
            moves, merged, gain = move(d)
            if moves:
                # Glid-animation
                for f in range(1, 6):
                    p = f / 5
                    draw_2048(lcd, None, score, t)
                    for (r, c, tr, tc, v) in moves:
                        x0, y0 = cell_xy(r, c)
                        x1, y1 = cell_xy(tr, tc)
                        g_tile(lcd, int(x0 + (x1 - x0) * p), int(y0 + (y1 - y0) * p), v)
                    lcd.show()
                    time.sleep_ms(14)
                score += gain
                if gain:
                    pops.add(W // 2, 6, "+%d" % gain, AMBER)
                pop = [(r, c, 6) for r, c in merged]
                for r, c in merged:
                    x, y = cell_xy(r, c)
                    parts.burst(x + G_S // 2, y + G_S // 2, G_COL[min(grid[r][c] - 1, 13)], 8, 2.5, 12)
                    if grid[r][c] == 11 and not won:
                        won = True
                        pops.add(W // 2, 100, "2048! DU VANN!", YELLOW, 2)
                s = spawn()
                if s:
                    pop.append((s[0], s[1], -6))
                if not can_move():
                    draw_2048(lcd, None, score, t)
                    lcd.show()
                    time.sleep_ms(900)
                    return score
        draw_2048(lcd, grid, score, t, pop)
        pop = [(r, c, k - 1 if k > 0 else k + 1) for r, c, k in pop if k != 0]
        parts.draw(lcd)
        pops.draw(lcd)
        lcd.show()
        t += 1
        wait(t0)


def draw_2048(lcd, grid, score, t, pop=()):
    gradient(lcd, G_BGC)
    size = G_N * G_S + (G_N + 1) * G_GAP
    lcd.fill_rect(G_X, G_Y, size, size, G_BOARD)
    for r in range(G_N):
        for c in range(G_N):
            x = G_X + G_GAP + c * (G_S + G_GAP)
            y = G_Y + G_GAP + r * (G_S + G_GAP)
            lcd.fill_rect(x + 2, y, G_S - 4, G_S, G_EMPTY)
            lcd.fill_rect(x, y + 2, G_S, G_S - 4, G_EMPTY)
            if grid and grid[r][c]:
                g_tile(lcd, x, y, grid[r][c])
    for r, c, k in pop:
        if grid and grid[r][c]:
            x = G_X + G_GAP + c * (G_S + G_GAP)
            y = G_Y + G_GAP + r * (G_S + G_GAP)
            if k > 0:                                     # sammanslagen: blir större
                g = k // 2
                g_tile(lcd, x - g, y - g, grid[r][c], G_S + 2 * g)
            else:                                         # ny: växer fram
                s = G_S + k * 6
                if s > 8:
                    g_tile(lcd, x + (G_S - s) // 2, y + (G_S - s) // 2, grid[r][c], s)
    # Poäng till höger, pilar i hörnen
    lcd.text("POANG", 8, 40, GRAY)
    big(lcd, str(score), 8, 52, WHITE, 2 if score < 100 else 1)
    lcd.text("REKORD", 8, 84, DIM)
    lcd.text(str(SCORES.get("2048", 0)), 8, 96, DIM)
    arrow(lcd, 12, 12, 0, AMBER)
    arrow(lcd, W - 12, 12, 1, AMBER)
    arrow(lcd, W - 12, H - 12, 2, AMBER)
    arrow(lcd, 12, H - 12, 3, AMBER)


def icon_2048(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, G_BOARD)
    vals = (1, 2, 3, 4, 5, 6, 7, 11)
    for i in range(8):
        e = vals[(i + t // 30) % 8]
        g_tile(fb, x + 6 + (i % 4) * 38, y + 4 + (i // 4) * 34, e, 32)


def choose(lcd, keys, title, options, col, sub=""):
    """Liten valmeny. Returnerar index, eller None (3 = tillbaka)."""
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
        if keys.pressed(K2):
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            return None
        gradient(lcd, NIGHT)
        stars.draw(lcd)
        stext(lcd, title, 26 + int(3 * math.sin(t * 0.15)), col, 4)
        if sub:
            ctext(lcd, sub, 72, GRAY)
        for i, o in enumerate(options):
            y = 100 + i * 34
            if i == sel:
                lcd.fill_rect(40, y - 8, 240, 28, col)
                ctext(lcd, o, y, BG, 2)
            else:
                lcd.rect(40, y - 8, 240, 28, LINE)
                ctext(lcd, o, y, WHITE, 2)
        ctext(lcd, "0/1 valj   2 ok   3 tillbaka", 222, GRAY)
        lcd.show()
        t += 1
        wait(t0)


# ===============================================================
# SPÖKJAKT (Pac-Man)
#   pilarna i hörnen: 0 upp, 1 höger, 2 ner, 3 vänster
# ===============================================================
P_HALF = (
    "###########", "#o........#", "#.###.###.#", "#..........", "#.###.#.###",
    "#.....#...#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
    "#####.#.###", "    #.#....", "#####.#.###", "#.........#", "#.###.###.#",
    "#o..#......", "###.#.#.###", "#.....#...#", "#.#######.#", "#..........",
    "###########",
)
P_MAZE = tuple(h + "".join(h[9 - i] for i in range(10)) for h in P_HALF)   # spegla vänster halva
MW, MH = 21, 21
PT = 10
PX0, PY0 = (W - MW * PT) // 2, 26
DIRS4 = ((0, -1), (1, 0), (0, 1), (-1, 0))         # upp, höger, ner, vänster
P_WALL = rgb(40, 60, 200)
P_WALL_D = rgb(14, 18, 70)
P_DOT = rgb(255, 200, 170)
P_YEL = rgb(255, 225, 40)
P_BGC = rgb(4, 4, 14)
GHOST_C = (rgb(255, 50, 60), rgb(255, 150, 210), rgb(60, 230, 240), rgb(255, 170, 60))
FRIGHT_C = rgb(50, 70, 255)
SCATTER = ((19, -2), (1, -2), (19, 22), (1, 22))
HOUSE = (10, 9)
EXIT = (10, 7)


def p_walk(x, y):
    """0 vägg, 1 gång, 2 spökhus, 3 dörr."""
    if y < 0 or y >= MH:
        return 0
    ch = P_MAZE[y][x % MW]
    if ch == "." or ch == "o":
        return 1
    if ch == "G":
        return 2
    if ch == "-":
        return 3
    return 0


def p_wall_rects():
    """Förberäknar väggarnas rektanglar (fyllning + kantlinjer)."""
    fills = []
    edges = []
    for y in range(MH):
        x = 0
        while x < MW:
            if P_MAZE[y][x] == "#":
                s = x
                while x < MW and P_MAZE[y][x] == "#":
                    x += 1
                fills.append((PX0 + s * PT, PY0 + y * PT, (x - s) * PT, PT))
            else:
                x += 1
    for y in range(MH):
        for x in range(MW):
            if P_MAZE[y][x] != "#":
                continue
            px, py = PX0 + x * PT, PY0 + y * PT
            for d, (dx, dy) in enumerate(DIRS4):
                nx, ny = x + dx, y + dy
                if 0 <= nx < MW and 0 <= ny < MH and P_MAZE[ny][nx] not in "# ":
                    if d == 0:
                        edges.append((px, py, PT, 2))
                    elif d == 1:
                        edges.append((px + PT - 2, py, 2, PT))
                    elif d == 2:
                        edges.append((px, py + PT - 2, PT, 2))
                    else:
                        edges.append((px, py, 2, PT))
    return tuple(fills), tuple(edges)


@native
def p_draw_maze(fb, fills, edges, dots, blink, wall_c):
    for r in fills:
        fb.fill_rect(r[0], r[1], r[2], r[3], P_WALL_D)
    for r in edges:
        fb.fill_rect(r[0], r[1], r[2], r[3], wall_c)
    for y in range(MH):
        for x in range(MW):
            v = dots[y * MW + x]
            if v == 1:
                fb.fill_rect(PX0 + x * PT + 4, PY0 + y * PT + 4, 2, 2, P_DOT)
            elif v == 2 and blink:
                fb.ellipse(PX0 + x * PT + 5, PY0 + y * PT + 5, 3, 3, P_DOT, True)
    fb.fill_rect(PX0 + 10 * PT, PY0 + 8 * PT + 4, PT, 2, rgb(255, 150, 210))


def turn_back(e):
    """Vänd mitt i en ruta utan att hoppa."""
    if e.d < 0:
        return
    dx, dy = DIRS4[e.d]
    if e.p > 0:
        e.x = (e.x + dx) % MW
        e.y += dy
        e.p = 1 - e.p
    e.d = (e.d + 2) % 4


class Ent:
    def __init__(self, x, y, d, speed):
        self.x, self.y, self.d, self.p, self.speed = x, y, d, 0.0, speed

    def pos(self):
        if self.d < 0:
            return self.x, self.y
        dx, dy = DIRS4[self.d]
        return self.x + dx * self.p, self.y + dy * self.p


def g_decide(g, ghosts, pac, face, chase):
    """Spöket står mitt i en ruta och väljer nästa riktning."""
    if g.state == "leave":
        tx, ty = EXIT
    elif g.state == "eyes":
        tx, ty = HOUSE
    elif not chase:
        tx, ty = SCATTER[g.i]
    else:
        pdx, pdy = DIRS4[face]
        if g.i == 0:                                  # röd: jagar Pac direkt
            tx, ty = pac.x, pac.y
        elif g.i == 1:                                # rosa: siktar framför Pac
            tx, ty = pac.x + 4 * pdx, pac.y + 4 * pdy
        elif g.i == 2:                                # blå: knipa tillsammans med röd
            b = ghosts[0]
            tx, ty = 2 * (pac.x + 2 * pdx) - b.x, 2 * (pac.y + 2 * pdy) - b.y
        else:                                         # orange: blyg när den är nära
            if (g.x - pac.x) ** 2 + (g.y - pac.y) ** 2 > 36:
                tx, ty = pac.x, pac.y
            else:
                tx, ty = SCATTER[3]
    inside = g.state in ("leave", "eyes")
    opts = []
    for d in (0, 3, 2, 1):
        if d == (g.d + 2) % 4:
            continue
        ddx, ddy = DIRS4[d]
        w = p_walk(g.x + ddx, g.y + ddy)
        if w == 1 or (inside and w in (2, 3)):
            opts.append(d)
    if not opts:
        opts = [(g.d + 2) % 4]
    if g.fright and g.state == "normal":
        g.d = random.choice(opts)
        return
    best = None
    for d in opts:
        ddx, ddy = DIRS4[d]
        dist = (g.x + ddx - tx) ** 2 + (g.y + ddy - ty) ** 2
        if best is None or dist < best:
            best = dist
            g.d = d


def draw_pac(fb, px, py, face, mouth, col=P_YEL, r=5):
    fb.ellipse(px, py, r, r, col, True)
    if mouth > 0.05:
        a = DIRS4[face if face >= 0 else 3]
        ang = math.atan2(a[1], a[0])
        m = mouth * 0.9
        tri(fb, px, py, px + int(math.cos(ang - m) * (r + 2)), py + int(math.sin(ang - m) * (r + 2)),
            px + int(math.cos(ang + m) * (r + 2)), py + int(math.sin(ang + m) * (r + 2)), P_BGC)


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


def spokjakt(lcd, keys):
    fills, edges = p_wall_rects()
    score = 0
    lives = 3
    level = 1
    pops = Popups()
    parts = Particles(60)

    def new_dots():
        d = bytearray(MW * MH)
        for y in range(MH):
            for x in range(MW):
                ch = P_MAZE[y][x]
                if ch == ".":
                    d[y * MW + x] = 1
                elif ch == "o":
                    d[y * MW + x] = 2
        d[15 * MW + 10] = 0                                  # där Pac börjar
        return d

    dots = new_dots()
    left = sum(1 for v in dots if v)

    while True:                                              # ett liv
        pac = Ent(10, 15, -1, min(0.13 + level * 0.006, 0.17))
        face = 3
        want = -1
        ghosts = []
        for i, (x, y) in enumerate(((10, 7), (10, 9), (9, 9), (11, 9))):
            g = Ent(x, y, 3 if i == 0 else 0, 0.12)
            g.i = i
            g.state = "normal" if i == 0 else "house"
            g.release = (0, 60, 160, 260)[i]
            g.fright = 0
            ghosts.append(g)
        mode_t = 0
        fright_t = 0
        eat_n = 0
        ready = 60
        t = 0
        dead = 0
        keys.wait_release()
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            for k, d in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
                if keys.pressed(k):
                    want = d
            if ready > 0:
                ready -= 1
            elif dead == 0:
                # --- Pac ---
                if pac.d >= 0 and want == (pac.d + 2) % 4:          # vänd direkt
                    dx, dy = DIRS4[pac.d]
                    pac.x = (pac.x + dx) % MW
                    pac.y += dy
                    pac.p = 1 - pac.p
                    pac.d = want
                if pac.d < 0 and want >= 0:
                    dx, dy = DIRS4[want]
                    if p_walk(pac.x + dx, pac.y + dy) == 1:
                        pac.d = want
                if pac.d >= 0:
                    face = pac.d
                    pac.p += pac.speed
                    while pac.p >= 1:
                        pac.p -= 1
                        dx, dy = DIRS4[pac.d]
                        pac.x = (pac.x + dx) % MW
                        pac.y += dy
                        k = pac.y * MW + pac.x
                        if dots[k]:
                            if dots[k] == 2:
                                score += 50
                                fright_t = max(60, 200 - level * 20)
                                eat_n = 0
                                for g in ghosts:
                                    if g.state == "normal":
                                        g.fright = 1
                                        turn_back(g)
                            else:
                                score += 10
                            dots[k] = 0
                            left -= 1
                        if want >= 0:
                            dx, dy = DIRS4[want]
                            if p_walk(pac.x + dx, pac.y + dy) == 1:
                                pac.d = want
                        dx, dy = DIRS4[pac.d]
                        if p_walk(pac.x + dx, pac.y + dy) != 1:
                            pac.d = -1
                            pac.p = 0.0
                            break
                # --- Läge: spridning eller jakt ---
                mode_t += 1
                cycle = mode_t % 900
                chase = cycle >= 210
                if mode_t % 900 in (0, 210) and mode_t > 1:
                    for g in ghosts:
                        if g.state == "normal" and not g.fright:
                            turn_back(g)
                if fright_t > 0:
                    fright_t -= 1
                    if fright_t == 0:
                        for g in ghosts:
                            g.fright = 0
                # --- Spöken ---
                for g in ghosts:
                    if g.state == "house":
                        if t >= g.release:
                            g.state = "leave"
                            g.p = 0.0
                            g.d = 0
                            g_decide(g, ghosts, pac, face, chase)
                        continue
                    if g.state == "eyes":
                        sp = 0.3
                    elif g.fright:
                        sp = 0.08
                    else:
                        sp = min(0.12 + level * 0.007, 0.16)
                    if g.y == 9 and (g.x < 4 or g.x > 16):
                        sp *= 0.6                                    # långsamt i tunneln
                    if g.d < 0:
                        g.d = 0
                    g.p += sp
                    while g.p >= 1:
                        g.p -= 1
                        dx, dy = DIRS4[g.d]
                        g.x = (g.x + dx) % MW
                        g.y += dy
                        if g.state == "leave" and (g.x, g.y) == EXIT:
                            g.state = "normal"
                        if g.state == "eyes" and (g.x, g.y) == HOUSE:
                            g.state = "leave"
                            g.fright = 0
                        g_decide(g, ghosts, pac, face, chase)
                # --- Krockar ---
                ppx, ppy = pac.pos()
                for g in ghosts:
                    if g.state in ("house", "eyes", "leave"):
                        continue
                    gx, gy = g.pos()
                    if (gx - ppx) ** 2 + (gy - ppy) ** 2 < 0.5:
                        if g.fright:
                            g.state = "eyes"
                            g.fright = 0
                            pts = 200 << eat_n
                            eat_n = min(eat_n + 1, 3)
                            score += pts
                            sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
                            pops.add(sx, sy - 8, str(pts), TEAL)
                            parts.burst(sx, sy, FRIGHT_C, 12, 2.5, 14)
                        else:
                            dead = 1
                if left == 0:
                    for k in range(8):
                        lcd.fill(P_BGC)
                        p_draw_maze(lcd, fills, edges, dots, False, WHITE if k % 2 == 0 else P_WALL)
                        lcd.show()
                        time.sleep_ms(160)
                    level += 1
                    dots = new_dots()
                    left = sum(1 for v in dots if v)
                    pops.add(W // 2, 120, "NIVA %d" % level, LIME, 2)
                    break
            else:
                dead += 1
                if dead > 50:
                    lives -= 1
                    if lives <= 0:
                        return score
                    break
            # --- Rita ---
            lcd.fill(P_BGC)
            p_draw_maze(lcd, fills, edges, dots, (t // 8) % 2 == 0, P_WALL)
            for g in ghosts:
                gx, gy = g.pos()
                sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
                if g.state == "house":
                    sy += int(2 * math.sin(t * 0.2 + g.i))
                if dead and dead > 10:
                    continue
                if g.state == "eyes":
                    draw_ghost(lcd, sx, sy, 0, g.d, t, True)
                elif g.fright:
                    flash = fright_t < 50 and (t // 5) % 2
                    draw_ghost(lcd, sx, sy, WHITE if flash else FRIGHT_C, g.d, t, False, True)
                else:
                    draw_ghost(lcd, sx, sy, GHOST_C[g.i], g.d, t)
            ppx, ppy = pac.pos()
            sx, sy = PX0 + int(ppx * PT) + 5, PY0 + int(ppy * PT) + 5
            if dead:
                m = min(3.1, 0.5 + dead * 0.07)
                if m < 3.0:
                    draw_pac(lcd, sx, sy, 0, m)
            else:
                mouth = abs(math.sin(t * 0.5)) if pac.d >= 0 else 0.4
                draw_pac(lcd, sx, sy, face, mouth)
            parts.draw(lcd)
            pops.draw(lcd)
            # Poäng och liv
            big(lcd, str(score), PX0, 6, WHITE, 2)
            rtext(lcd, "NIVA %d" % level, PX0 + MW * PT, 10, LIME)
            for i in range(lives - 1):
                draw_pac(lcd, 140 + i * 14, 13, 1, 0.6, P_YEL, 4)
            if ready > 0:
                ctext(lcd, "REDO!", PY0 + 13 * PT + 1, P_YEL, 1)
            arrow(lcd, 14, 14, 0, DIM)
            arrow(lcd, W - 14, 14, 1, DIM)
            arrow(lcd, W - 14, H - 14, 2, DIM)
            arrow(lcd, 14, H - 14, 3, DIM)
            lcd.show()
            t += 1
            wait(t0)


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


# ===============================================================
# KURVAN (Achtung die Kurve)
#   Spelare 1: 0 sväng vänster, 3 sväng höger
#   Spelare 2: 1 sväng vänster, 2 sväng höger
# ===============================================================
KY0 = 20
KW, KH = W // 2, (H - KY0) // 2
K_COLS = (TEAL, PINK, AMBER)
K_SPEED = 1.5
K_TURN = 0.085


def kurvan(lcd, keys):
    mode = choose(lcd, keys, "KURVAN", ("MOT DATORN", "MOT 2 DATORER", "2 SPELARE"), TEAL,
                  "Sist kvar vinner rundan. Forst till 5!")
    if mode is None:
        return None
    n = 3 if mode == 1 else 2
    cpu = [False, mode != 2, True][:n]
    names = ["DU" if mode != 2 else "SPELARE 1", "DATORN" if mode == 0 else ("DATOR 1" if mode == 1 else "SPELARE 2"),
             "DATOR 2"][:n]
    ctrl = [(K0, K3), (K1, K2), None]
    points = [0] * n
    goal = 5
    grid = bytearray(KW * KH)

    def free(px, py):
        if px < 1 or py < KY0 + 1 or px >= W - 1 or py >= H - 1:
            return False
        return grid[(int(py - KY0) >> 1) * KW + (int(px) >> 1)] == 0

    def look(p, turn, steps=34):
        x, y, a = p[0], p[1], p[2]
        for i in range(steps):
            a += turn * K_TURN
            x += math.cos(a) * K_SPEED * 2
            y += math.sin(a) * K_SPEED * 2
            if not free(x, y):
                return i
        return steps

    while True:                                    # en runda
        for i in range(len(grid)):
            grid[i] = 0
        pl = []
        for i in range(n):
            while True:
                x = random.uniform(50, W - 50)
                y = random.uniform(KY0 + 40, H - 40)
                if all((x - q[0]) ** 2 + (y - q[1]) ** 2 > 3600 for q in pl):
                    break
            a = math.atan2(KY0 + (H - KY0) / 2 - y, W / 2 - x) + random.uniform(-0.8, 0.8)
            pl.append([x, y, a, True, random.randint(60, 140), 0, 0, x, y])   # x,y,vinkel,lever,till glapp,glapp,ai-sväng,förra x,y
        for c in range(75):                        # nedräkning
            t0 = time.ticks_ms()
            keys.update()
            k_field(lcd, names, points, n)
            for i, p in enumerate(pl):
                ex, ey = p[0] + math.cos(p[2]) * 14, p[1] + math.sin(p[2]) * 14
                lcd.line(int(p[0]), int(p[1]), int(ex), int(ey), K_COLS[i])
                lcd.ellipse(int(p[0]), int(p[1]), 3, 3, K_COLS[i], True)
                if not cpu[i] and (c // 8) % 2 == 0:
                    lab = "%d/%d" % ctrl[i]
                    lcd.text(lab, int(p[0]) - 12, int(p[1]) + 8, WHITE)
            stext(lcd, str(3 - c // 25), 100, WHITE, 5)
            lcd.show()
            wait(t0)
        k_field(lcd, names, points, n)
        t = 0
        keys.wait_release()
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return points[0]
            for i, p in enumerate(pl):
                if not p[3]:
                    continue
                if cpu[i]:
                    if t % 3 == i % 3:
                        best, bt = -1, 0
                        for turn in (0, -1, 1):
                            s = look(p, turn) + random.random() * 2
                            if s > best:
                                best, bt = s, turn
                        p[6] = bt
                    turn = p[6]
                else:
                    turn = (-1 if keys.held(ctrl[i][0]) else 0) + (1 if keys.held(ctrl[i][1]) else 0)
                p[2] += turn * K_TURN
                p[7], p[8] = p[0], p[1]
                p[0] += math.cos(p[2]) * K_SPEED
                p[1] += math.sin(p[2]) * K_SPEED
                ax = p[0] + math.cos(p[2]) * 2.5
                ay = p[1] + math.sin(p[2]) * 2.5
                if not free(ax, ay):
                    p[3] = False
                    lcd.ellipse(int(p[0]), int(p[1]), 6, 6, WHITE, False)
                    lcd.ellipse(int(p[0]), int(p[1]), 4, 4, K_COLS[i], True)
                    continue
                # Glapp i svansen ibland
                p[4] -= 1
                if p[4] <= 0:
                    p[5] = 7
                    p[4] = random.randint(70, 150)
                if p[5] > 0:
                    p[5] -= 1
                    if grid[(int(p[8] - KY0) >> 1) * KW + (int(p[7]) >> 1)] == 0:
                        lcd.fill_rect(int(p[7]) - 1, int(p[8]) - 1, 3, 3, BG)
                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, WHITE)
                else:
                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, K_COLS[i])
                    grid[(int(p[1] - KY0) >> 1) * KW + (int(p[0]) >> 1)] = i + 1
            alive = [i for i, p in enumerate(pl) if p[3]]
            hud_k(lcd, names, points, n)
            lcd.show()
            t += 1
            wait(t0, 25)
            if len(alive) <= 1:
                if alive:
                    points[alive[0]] += 1
                    msg = "%s TAR RUNDAN" % names[alive[0]]
                    col = K_COLS[alive[0]]
                else:
                    msg, col = "OAVGJORT", GRAY
                lcd.fill_rect(30, 96, 260, 44, BG)
                lcd.rect(30, 96, 260, 44, col)
                ctext(lcd, msg, 106, col, 1 if len(msg) > 18 else 2)
                ctext(lcd, "  ".join("%d" % q for q in points), 126, WHITE)
                hud_k(lcd, names, points, n)
                lcd.show()
                time.sleep_ms(1600)
                break
        if max(points) >= goal:
            w = points.index(max(points))
            return ("WIN", names[w], K_COLS[w], points[0])


def k_field(lcd, names, points, n):
    lcd.fill(BG)
    lcd.rect(0, KY0, W, H - KY0, LINE)
    lcd.rect(1, KY0 + 1, W - 2, H - KY0 - 2, LINE)
    hud_k(lcd, names, points, n)


def hud_k(lcd, names, points, n):
    lcd.fill_rect(0, 0, W, KY0, BG)
    for i in range(n):
        x = 6 + i * 106
        lcd.fill_rect(x, 6, 8, 8, K_COLS[i])
        lcd.text("%s %d" % (names[i], points[i]), x + 12, 6, K_COLS[i])


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


# ===============================================================
# INVASION (Space Invaders)
#   0 vänster   1 höger   2 skjut   3 superlaser (när mätaren är full)
# ===============================================================
SPR_SQUID = (("...##...", "..####..", ".######.", "##.##.##", "########", "..#..#..", ".#.##.#.", "#.#..#.#"),
             ("...##...", "..####..", ".######.", "##.##.##", "########", ".#.##.#.", "#......#", ".#....#."))
SPR_CRAB = (("..#.....#..", "...#...#...", "..#######..", ".##.###.##.", "###########", "#.#######.#", "#.#.....#.#", "...##.##..."),
            ("..#.....#..", "#..#...#..#", "#.#######.#", "###.###.###", "###########", ".#########.", "..#.....#..", ".#.......#."))
SPR_OCTO = (("....####....", ".##########.", "############", "###..##..###", "############", "...##..##...", "..##.##.##..", "##........##"),
            ("....####....", ".##########.", "############", "###..##..###", "############", "..###..###..", ".##..##..##.", "..##....##.."))
SPR_SHIP = ("......#......", ".....###.....", ".....###.....", ".###########.", "#############", "#############", "#############")
SPR_UFO = (".....######.....", "...##########...", "..############..", ".##.##.##.##.##.", "################", "..###..##..###..", "...#........#...")
I_COLS = (PINK, TEAL, TEAL, LIME, LIME)
I_POINTS = (30, 20, 20, 10, 10)


def sprite(rows, col, s=2):
    """Gör en liten bild (FrameBuffer) av en textmall. Svart = genomskinligt."""
    w, h = len(rows[0]) * s, len(rows) * s
    buf = bytearray(w * h * 2)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                fb.fill_rect(x * s, y * s, s, s, col)
    return (fb, w, h, buf)


def bunker():
    b = bytearray(12 * 8)
    for y in range(8):
        for x in range(12):
            corner = (y == 0 and (x < 2 or x > 9)) or (y == 1 and (x == 0 or x == 11))
            hole = y >= 5 and 3 <= x <= 8
            b[y * 12 + x] = 0 if corner or hole else 1
    return b


BUNK_X = (34, 106, 178, 250)
BUNK_Y = 176
BUNK_C = rgb(90, 230, 120)


@native
def draw_bunkers(fb, bunks):
    for i in range(4):
        b = bunks[i]
        bx = BUNK_X[i]
        for y in range(8):
            for x in range(12):
                if b[y * 12 + x]:
                    fb.fill_rect(bx + x * 3, BUNK_Y + y * 3, 3, 3, BUNK_C)


def bunker_hit(bunks, x, y):
    """Träffar punkten ett skydd? Gör då ett hål och returnerar True."""
    for i in range(4):
        bx = BUNK_X[i]
        if bx <= x < bx + 36 and BUNK_Y <= y < BUNK_Y + 24:
            cx, cy = int(x - bx) // 3, int(y - BUNK_Y) // 3
            b = bunks[i]
            if b[cy * 12 + cx]:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < 12 and 0 <= ny < 8 and (dx == 0 and dy == 0 or random.random() < 0.5):
                            b[ny * 12 + nx] = 0
                return True
    return False


def invasion(lcd, keys):
    spr = [[sprite(SPR_SQUID[f], PINK) for f in (0, 1)],
           [sprite(SPR_CRAB[f], TEAL) for f in (0, 1)],
           [sprite(SPR_OCTO[f], LIME) for f in (0, 1)]]
    kind_of_row = (0, 1, 1, 2, 2)
    ship = sprite(SPR_SHIP, SKY)
    ufo_s = sprite(SPR_UFO, CORAL)
    stars = Stars(40)
    parts = Particles(160)
    pops = Popups()
    shake = Shake()
    score, lives, wave = 0, 3, 0
    px = W / 2
    inv = 0
    cool = 0
    power, power_t = "", 0
    shield = False
    meter = 0
    beam = 0
    t = 0
    keys.wait_release()
    while True:                                           # en våg
        wave += 1
        alive = [[True] * 8 for _ in range(5)]
        fx, fy = 26.0, 30.0 + min(wave - 1, 5) * 8
        fdir = 1
        step_t = 0
        frame = 0
        shots, aliens_shots, drops = [], [], []
        bunks = [bunker() for _ in range(4)]
        ufo = None
        banner = 60
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            n_alive = sum(sum(1 for a in r if a) for r in alive)
            if n_alive == 0:
                break
            # --- Spelaren ---
            if keys.held(K0):
                px -= 3.2
            if keys.held(K1):
                px += 3.2
            px = max(14, min(W - 14, px))
            if cool > 0:
                cool -= 1
            if keys.held(K2) and cool == 0 and len(shots) < 6:
                shots.append([px, 206.0, 0.0])
                if power == "T":
                    shots.append([px, 206.0, -1.5])
                    shots.append([px, 206.0, 1.5])
                cool = 6 if power == "R" else 14
            if keys.pressed(K3) and meter >= 10:
                meter = 0
                beam = 20
                shake.hit(6)
            if power_t > 0:
                power_t -= 1
                if power_t == 0:
                    power = ""
            # --- Formationen ---
            step_t += 1
            interval = max(1, n_alive // 3)
            if step_t >= interval:
                step_t = 0
                frame ^= 1
                minx, maxx = W, 0
                maxy = 0
                for r in range(5):
                    for c in range(8):
                        if alive[r][c]:
                            x = fx + c * 28
                            minx = min(minx, x)
                            maxx = max(maxx, x + 24)
                            maxy = max(maxy, fy + r * 20 + 16)
                if (fdir > 0 and maxx + 4 > W - 4) or (fdir < 0 and minx - 4 < 4):
                    fdir = -fdir
                    fy += 8
                else:
                    fx += 4 * fdir
                if maxy >= BUNK_Y:                         # rensar skydden de rör vid
                    for i in range(4):
                        for y in range(8):
                            if BUNK_Y + y * 3 < maxy:
                                for x in range(12):
                                    bunks[i][y * 12 + x] = 0
                if maxy >= 206:
                    lives = 0
            if random.random() < 0.025 + wave * 0.005 and len(aliens_shots) < 2 + wave // 2:
                cols = [c for c in range(8) if any(alive[r][c] for r in range(5))]
                if cols:
                    c = random.choice(cols)
                    r = max(r for r in range(5) if alive[r][c])
                    aliens_shots.append([fx + c * 28 + 11, fy + r * 20 + 16])
            # --- UFO ---
            if ufo is None and random.random() < 0.003:
                d = random.choice((-1, 1))
                ufo = [-34.0 if d > 0 else W + 2.0, 1.6 * d]
            if ufo:
                ufo[0] += ufo[1]
                if ufo[0] < -40 or ufo[0] > W + 8:
                    ufo = None
            # --- Skott ---
            for s in shots:
                s[1] -= 7
                s[0] += s[2]
                if s[1] < 16 or bunker_hit(bunks, s[0], s[1]):
                    s[1] = -99
                    continue
                if ufo and ufo[0] <= s[0] <= ufo[0] + 32 and 18 <= s[1] <= 32:
                    pts = random.choice((50, 100, 150, 300))
                    score += pts
                    pops.add(ufo[0] + 16, 20, str(pts), CORAL)
                    parts.burst(ufo[0] + 16, 25, CORAL, 24, 3.5, 22)
                    shake.hit(5)
                    ufo = None
                    s[1] = -99
                    continue
                r = int((s[1] - fy) // 20)
                c = int((s[0] - fx) // 28)
                if 0 <= r < 5 and 0 <= c < 8 and alive[r][c]:
                    ax, ay = fx + c * 28, fy + r * 20
                    w = spr[kind_of_row[r]][0][1]
                    if ax <= s[0] <= ax + w and ay <= s[1] <= ay + 16:
                        alive[r][c] = False
                        s[1] = -99
                        score += I_POINTS[r]
                        meter = min(10, meter + 1)
                        parts.burst(ax + w / 2, ay + 8, I_COLS[r], 12, 2.5, 14)
                        pops.add(ax + w / 2, ay, str(I_POINTS[r]), I_COLS[r])
                        if random.random() < 0.08:
                            drops.append([ax + w / 2, ay + 8, random.choice("TRS")])
            shots = [s for s in shots if s[1] > 0]
            for s in aliens_shots:
                s[1] += 3.2 + wave * 0.2
                if bunker_hit(bunks, s[0], s[1]):
                    s[1] = H + 99
                elif inv == 0 and abs(s[0] - px) < 12 and 204 <= s[1] <= 220:
                    s[1] = H + 99
                    if shield:
                        shield = False
                        parts.burst(px, 210, TEAL, 14, 2.5, 14)
                    else:
                        lives -= 1
                        inv = 90
                        parts.burst(px, 210, SKY, 30, 4, 28)
                        parts.burst(px, 210, AMBER, 20, 3, 22)
                        shake.hit(9)
            aliens_shots = [s for s in aliens_shots if s[1] < H]
            for d in drops:
                d[1] += 1.6
                if abs(d[0] - px) < 16 and 204 <= d[1] <= 222:
                    d[1] = H + 99
                    if d[2] == "S":
                        shield = True
                        pops.add(px, 190, "SKOLD", TEAL)
                    else:
                        power, power_t = d[2], 420
                        pops.add(px, 190, "TRIPPEL" if d[2] == "T" else "SNABB", AMBER)
            drops = [d for d in drops if d[1] < H]
            # --- Superlaser ---
            if beam > 0:
                beam -= 1
                for r in range(5):
                    for c in range(8):
                        ax = fx + c * 28
                        w = spr[kind_of_row[r]][0][1]
                        if alive[r][c] and ax - 6 <= px <= ax + w + 6:
                            alive[r][c] = False
                            score += I_POINTS[r]
                            parts.burst(ax + w / 2, fy + r * 20 + 8, I_COLS[r], 10, 3, 14)
                aliens_shots = [s for s in aliens_shots if abs(s[0] - px) > 8]
                if ufo and ufo[0] <= px <= ufo[0] + 32:
                    score += 300
                    pops.add(ufo[0] + 16, 20, "300", CORAL)
                    ufo = None
            if inv > 0:
                inv -= 1
            if lives <= 0:
                lcd.show()
                time.sleep_ms(600)
                return score

            # --- Rita ---
            ox, oy = shake.offset()
            lcd.fill(BLACK)
            stars.draw(lcd, 0.0, 0.3)
            for r in range(5):
                sp = spr[kind_of_row[r]][frame]
                for c in range(8):
                    if alive[r][c]:
                        lcd.blit(sp[0], int(fx + c * 28) + ox, int(fy + r * 20) + oy, 0)
            if ufo:
                lcd.blit(ufo_s[0], int(ufo[0]) + ox, 18 + oy, 0)
            draw_bunkers(lcd, bunks)
            for s in shots:
                lcd.fill_rect(int(s[0]) - 1 + ox, int(s[1]) + oy, 2, 7, YELLOW)
            for s in aliens_shots:
                zz = (t // 3) % 2
                lcd.fill_rect(int(s[0]) - 1 + zz + ox, int(s[1]) + oy, 2, 4, CORAL)
                lcd.fill_rect(int(s[0]) - zz + ox, int(s[1]) + 4 + oy, 2, 4, CORAL)
            for d in drops:
                c = {"T": CORAL, "R": AMBER, "S": TEAL}[d[2]]
                lcd.fill_rect(int(d[0]) - 6, int(d[1]) - 5, 12, 10, c)
                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
            if beam > 0:
                w = 4 + (beam % 3) * 2
                lcd.fill_rect(int(px) - w // 2 - 2, 16, w + 4, 196, PINK)
                lcd.fill_rect(int(px) - w // 2, 16, w, 196, WHITE)
            if inv == 0 or (t // 4) % 2:
                lcd.blit(ship[0], int(px) - 13 + ox, 206 + oy, 0)
                if shield:
                    lcd.ellipse(int(px) + ox, 212 + oy, 18, 11, TEAL)
            parts.draw(lcd, ox, oy)
            pops.draw(lcd, ox, oy)
            lcd.fill_rect(0, 0, W, 14, BG)
            lcd.text(str(score), 4, 3, WHITE)
            lcd.text("VAG %d" % wave, 132, 3, GRAY)
            for i in range(lives):
                lcd.blit(ship[0], W - 30 - i * 30, 0, 0)
            lcd.fill_rect(4, H - 6, 60, 4, LINE)
            lcd.fill_rect(4, H - 6, meter * 6, 4, PINK if meter >= 10 else VIOLET)
            if meter >= 10 and (t // 6) % 2:
                lcd.text("3 LASER!", 70, H - 9, PINK)
            if power:
                lcd.text("TRIPPEL" if power == "T" else "SNABB", W - 60, H - 9, AMBER)
            if banner > 0:
                banner -= 1
                stext(lcd, "VAG %d" % wave, 110, WHITE, 3)
            lcd.show()
            t += 1
            wait(t0)
        score += 100 * wave
        pops.add(W // 2, 130, "VAG KLAR +%d" % (100 * wave), LIME, 2)


def icon_invasion(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, BLACK)
    rows = (SPR_SQUID, SPR_CRAB, SPR_OCTO)
    cols = (PINK, TEAL, LIME)
    off = int(6 * math.sin(t * 0.05))
    for r in range(3):
        rr = rows[r][(t // 10) % 2]
        for c in range(5):
            bx = x + 18 + c * 26 + off
            by = y + 4 + r * 13
            for yy, row in enumerate(rr):
                for xx, ch in enumerate(row):
                    if ch == "#":
                        fb.pixel(bx + xx, by + yy, cols[r])
    sx = x + 80 + int(40 * math.sin(t * 0.04))
    fb.fill_rect(sx - 8, y + 64, 16, 5, SKY)
    fb.fill_rect(sx - 1, y + 60, 3, 4, SKY)
    k = (t * 4) % 40
    fb.fill_rect(sx, y + 56 - k, 1, 4, YELLOW)


# ===============================================================
# KROSS (Breakout)
#   0 vänster   1 höger   2 skjut iväg bollen / laser   3 skjut iväg bollen
# ===============================================================
K_LEVELS = (
    ("1111111111", "2222222222", "3333333333", "4444444444", "5555555555"),
    ("..AAAAAA..", ".A111111A.", "A11XXXX11A", "A11111111A", ".AAAAAAAA."),
    ("M..1111..M", "M.1BBBB1.M", "M.1B33B1.M", "M.1BBBB1.M", "M..1111..M"),
    ("X1X1X1X1X1", "1A1A1A1A1A", "2B2B2B2B2B", "1A1A1A1A1A", "X1X1X1X1X1"),
    ("....11....", "...1221...", "..123321..", ".12344321.", "1234554321", ".AAAAAAAA.", "MM......MM"),
    ("AXAXAXAXAX", "1111111111", "MMMM..MMMM", "2222222222", "B........B", "BBBBBBBBBB"),
)
BR_RAW = ((255, 95, 100), (255, 170, 60), (255, 225, 70), (125, 230, 110), (80, 165, 255))
BR_N = [rgb(*c) for c in BR_RAW]
BR_L = [mix(c, (255, 255, 255), 0.5) for c in BR_RAW]
BR_D = [mix(c, (0, 0, 0), 0.4) for c in BR_RAW]
BR_HARD = (rgb(120, 70, 210), rgb(160, 110, 255), rgb(200, 160, 255))
BR_METAL = rgb(150, 155, 175)
BR_X = rgb(255, 120, 40)
B_BW, B_BH = 30, 11
B_TOP = 26
PADY = 222


def kross(lcd, keys):
    parts = Particles(140)
    pops = Popups()
    shake = Shake()
    score, lives, lvl = 0, 3, 0
    bg = [mix((18, 14, 40), (8, 22, 44), y / (H - 1)) for y in range(H)]
    while True:                                   # en bana
        layout = K_LEVELS[lvl % len(K_LEVELS)]
        speed0 = min(3.6 + lvl * 0.3, 6.0)
        typ = bytearray(10 * 8)                   # 0 ingen, 1-5 vanlig, 6 hård, 8 metall, 9 sprängsten
        hp = bytearray(10 * 8)
        for r, row in enumerate(layout):
            for c, ch in enumerate(row):
                i = r * 10 + c
                if ch in "12345":
                    typ[i], hp[i] = int(ch), 1
                elif ch == "A":
                    typ[i], hp[i] = 6, 2
                elif ch == "B":
                    typ[i], hp[i] = 6, 3
                elif ch == "M":
                    typ[i], hp[i] = 8, 255
                elif ch == "X":
                    typ[i], hp[i] = 9, 1
        pw, pdx = 48, (W - 48) / 2
        balls = [[0.0, 0.0, 0.0, 0.0]]
        attached = True
        drops = []
        lasers = []
        effects = {}                              # namn -> bilder kvar
        banner = 50
        t = 0
        keys.wait_release()

        def left():
            for i in range(80):
                if typ[i] and typ[i] != 8:
                    return True
            return False

        def destroy(i, chain=0):
            nonlocal score
            tp = typ[i]
            typ[i] = 0
            hp[i] = 0
            r, c = i // 10, i % 10
            bx, by = c * 32 + 1 + B_BW / 2, B_TOP + r * 13 + B_BH / 2
            col = BR_N[tp - 1] if tp <= 5 else (BR_X if tp == 9 else BR_HARD[1])
            parts.burst(bx, by, col, 8, 2.5, 14)
            gain = 10 if tp <= 5 else (30 if tp == 6 else 40)
            score += gain
            if random.random() < 0.14:
                drops.append([bx, by, random.choice("WMSL+W")])
            if tp == 9:                               # sprängsten tar grannarna
                shake.hit(5)
                parts.burst(bx, by, AMBER, 18, 4, 18)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 10:
                            j = nr * 10 + nc
                            if typ[j] and typ[j] != 8:
                                destroy(j, chain + 1)

        def hit_brick(x, y):
            r = int((y - B_TOP) // 13)
            c = int(x // 32)
            if 0 <= r < 8 and 0 <= c < 10:
                i = r * 10 + c
                if typ[i]:
                    if typ[i] != 8:
                        hp[i] -= 1
                        if hp[i] == 0:
                            destroy(i)
                    return True
            return False

        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            wide = effects.get("W", 0) > 0
            pw = 72 if wide else 48
            if keys.held(K0):
                pdx -= 6
            if keys.held(K1):
                pdx += 6
            pdx = max(0, min(W - pw, pdx))
            slow = 0.7 if effects.get("S", 0) else 1.0
            spd = speed0 * slow
            if attached:
                balls = [[pdx + pw / 2, PADY - 5.0, 0.0, 0.0]]
                if banner == 0 and (keys.pressed(K2) or keys.pressed(K3)):
                    attached = False
                    a = random.uniform(-0.5, 0.5)
                    balls[0][2], balls[0][3] = math.sin(a) * spd, -math.cos(a) * spd
            elif effects.get("L", 0) and keys.pressed(K2):
                lasers.append([pdx + 4, PADY - 4.0])
                lasers.append([pdx + pw - 4, PADY - 4.0])
            for k in list(effects):
                effects[k] -= 1
                if effects[k] <= 0:
                    del effects[k]
            # --- Bollar ---
            keep = []
            for b in balls:
                if attached:
                    keep.append(b)
                    continue
                sp = math.sqrt(b[2] * b[2] + b[3] * b[3])
                if sp > 0:
                    b[2] *= spd / sp
                    b[3] *= spd / sp
                for _ in range(2):
                    b[0] += b[2] / 2
                    if b[0] < 3 or b[0] > W - 3:
                        b[2] = -b[2]
                        b[0] = max(3, min(W - 3, b[0]))
                    elif hit_brick(b[0] + (3 if b[2] > 0 else -3), b[1]):
                        b[2] = -b[2]
                        b[0] += b[2] / 2
                    b[1] += b[3] / 2
                    if b[1] < 20:
                        b[3] = abs(b[3])
                    elif hit_brick(b[0], b[1] + (3 if b[3] > 0 else -3)):
                        b[3] = -b[3]
                        b[1] += b[3] / 2
                if b[3] > 0 and PADY - 4 <= b[1] <= PADY + 4 and pdx - 3 <= b[0] <= pdx + pw + 3:
                    rel = (b[0] - (pdx + pw / 2)) / (pw / 2)
                    a = max(-1.0, min(1.0, rel)) * 1.1
                    b[2], b[3] = math.sin(a) * spd, -math.cos(a) * spd
                    b[1] = PADY - 5
                if b[1] < H + 5:
                    keep.append(b)
            balls = keep
            if not balls:
                lives -= 1
                shake.hit(8)
                if lives <= 0:
                    return score
                attached = True
                effects = {}
                balls = [[0.0, 0.0, 0.0, 0.0]]
            for l in lasers:
                l[1] -= 7
                if hit_brick(l[0], l[1]):
                    l[1] = -9
            lasers = [l for l in lasers if l[1] > 18]
            for d in drops:
                d[1] += 1.8
                if PADY - 6 <= d[1] <= PADY + 6 and pdx - 6 <= d[0] <= pdx + pw + 6:
                    d[1] = H + 99
                    score += 50
                    k = d[2]
                    if k == "M" and balls and not attached:
                        b = balls[0]
                        for a in (-0.6, 0.6):
                            balls.append([b[0], b[1], math.sin(a) * spd, -math.cos(a) * spd])
                        pops.add(d[0], PADY - 20, "MULTIBOLL", PINK)
                    elif k == "+":
                        lives += 1
                        pops.add(d[0], PADY - 20, "+1 LIV", LIME)
                    else:
                        effects[k] = 500
                        pops.add(d[0], PADY - 20, {"W": "BRED", "S": "LANGSAM", "L": "LASER"}.get(k, ""), AMBER)
            drops = [d for d in drops if d[1] < H]
            if not left():
                score += 500
                lvl += 1
                pops.add(W // 2, 120, "BANAN KLAR! +500", LIME, 2)
                for _ in range(40):
                    t1 = time.ticks_ms()
                    gradient(lcd, bg)
                    pops.draw(lcd)
                    parts.draw(lcd)
                    lcd.show()
                    wait(t1)
                break
            if banner > 0:
                banner -= 1

            # --- Rita ---
            ox, oy = shake.offset()
            gradient(lcd, bg)
            for i in range(80):
                tp = typ[i]
                if not tp:
                    continue
                x = (i % 10) * 32 + 1 + ox
                y = B_TOP + (i // 10) * 13 + oy
                if tp <= 5:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_N[tp - 1])
                    lcd.hline(x, y, B_BW, BR_L[tp - 1])
                    lcd.hline(x, y + B_BH - 1, B_BW, BR_D[tp - 1])
                elif tp == 6:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_HARD[min(2, hp[i] - 1)])
                    lcd.rect(x, y, B_BW, B_BH, WHITE if hp[i] >= 3 else BR_HARD[2])
                elif tp == 8:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_METAL)
                    lcd.hline(x, y + 2, B_BW, WHITE)
                    lcd.rect(x, y, B_BW, B_BH, DIM)
                else:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_X if (t // 6) % 2 else CORAL)
                    lcd.text("X", x + 11, y + 2, WHITE)
            for d in drops:
                c = {"W": SKY, "M": PINK, "S": TEAL, "L": CORAL, "+": LIME}[d[2]]
                lcd.fill_rect(int(d[0]) - 8, int(d[1]) - 5, 16, 10, c)
                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
            for l in lasers:
                lcd.fill_rect(int(l[0]) - 1, int(l[1]), 2, 8, CORAL)
            pc = CORAL if effects.get("L", 0) else SKY
            lcd.fill_rect(int(pdx) + ox, PADY + oy, pw, 7, pc)
            lcd.hline(int(pdx) + 2 + ox, PADY + 1 + oy, pw - 4, WHITE)
            for b in balls:
                lcd.ellipse(int(b[0]) + ox, int(b[1]) + oy, 3, 3, WHITE, True)
            parts.draw(lcd, ox, oy)
            pops.draw(lcd, ox, oy)
            lcd.fill_rect(0, 0, W, 16, BG)
            lcd.text(str(score), 4, 4, WHITE)
            lcd.text("BANA %d" % (lvl + 1), 130, 4, AMBER)
            for i in range(lives):
                lcd.ellipse(W - 10 - i * 12, 8, 4, 4, CORAL, True)
            if banner > 0:
                stext(lcd, "BANA %d" % (lvl + 1), 130, WHITE, 3)
            elif attached and (t // 10) % 2 == 0:
                ctext(lcd, "2  skjut ivag bollen", 170, GRAY)
            lcd.show()
            t += 1
            wait(t0)


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


# ===============================================================
# STUDS (Doodle Jump)
#   0 vänster   1 höger   2 skjut uppåt
# ===============================================================
S_GRAV = 0.36
S_JUMP = -8.6
S_SPRING = -13.5
S_PLAT_C = (LIME, SKY, rgb(170, 110, 60), AMBER)      # vanlig, rörlig, går sönder, studsmatta


def studs(lcd, keys):
    parts = Particles(60)
    pops = Popups()
    px, py, vx, vy = W / 2, 200.0, 0.0, S_JUMP
    face = 1
    cam = 0.0
    best_y = py
    plats = [[W / 2 - 22, 220.0, 0, 0.0, False]]      # x, y, typ, fart, trasig
    monsters = []                                      # x, y, fart, fas
    bullets = []
    top = 220.0
    squash = 0
    t = 0
    keys.wait_release()

    def spawn_until(limit):
        nonlocal top
        while top > limit:
            height = (200 - top) / 10
            gmax = min(88, 40 + height * 0.04)
            gmin = min(60, 22 + height * 0.02)
            top -= random.uniform(gmin, gmax)
            r = random.random()
            if height > 300 and r < 0.25:
                typ, spd = 1, random.choice((-1, 1)) * random.uniform(0.8, 1.8 + height / 2000)
            elif r > 0.92:
                typ, spd = 3, 0.0
            else:
                typ, spd = 0, 0.0
            plats.append([random.uniform(4, W - 48), top, typ, spd, False])
            if height > 150 and random.random() < 0.25:           # extra platta som går sönder
                plats.append([random.uniform(4, W - 48), top + random.uniform(10, 25), 2, 0.0, False])
            if height > 600 and random.random() < 0.06:
                monsters.append([random.uniform(20, W - 20), top - 30, random.choice((-1, 1)) * 0.8, 0.0])

    spawn_until(cam - 40)
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return int((200 - best_y) / 10)
        if keys.held(K0):
            vx -= 0.7
            face = -1
        if keys.held(K1):
            vx += 0.7
            face = 1
        vx *= 0.86
        vx = max(-5.5, min(5.5, vx))
        if keys.pressed(K2):
            bullets.append([px, py - 10])
        px += vx
        if px < -8:
            px += W + 16
        elif px > W + 8:
            px -= W + 16
        oy = py
        vy += S_GRAV
        py += vy
        if squash > 0:
            squash -= 1
        # Landa på plattor (bara på väg ner)
        if vy > 0:
            for p in plats:
                if p[4]:
                    continue
                if p[0] - 6 <= px <= p[0] + 50 and oy + 10 <= p[1] <= py + 10:
                    if p[2] == 2:
                        p[4] = True
                        parts.burst(p[0] + 22, p[1], S_PLAT_C[2], 10, 2, 16, 0.2)
                        continue
                    py = p[1] - 10
                    vy = S_SPRING if p[2] == 3 else S_JUMP
                    squash = 5
                    if p[2] == 3:
                        pops.add(px, py - 20, "BOING!", AMBER)
                    break
        for p in plats:
            if p[2] == 1:
                p[0] += p[3]
                if p[0] < 2 or p[0] > W - 46:
                    p[3] = -p[3]
            if p[4]:
                p[1] += 4
        # Monster
        for m in monsters:
            m[3] += 0.08
            m[0] += m[2]
            if m[0] < 14 or m[0] > W - 14:
                m[2] = -m[2]
            my = m[1] + math.sin(m[3]) * 4
            if abs(px - m[0]) < 14 and abs(py - my) < 14:
                if vy > 0 and py < my:
                    vy = S_JUMP * 1.1
                    m[1] = 1e9
                    parts.burst(px, py + 8, VIOLET, 16, 3, 18)
                    pops.add(px, py - 10, "+200", VIOLET)
                    best_y -= 2000
                else:
                    for k in range(30):
                        t1 = time.ticks_ms()
                        py += 6
                        draw_studs(lcd, plats, monsters, bullets, px, py, cam, face, 0, t, best_y)
                        lcd.show()
                        wait(t1)
                    return int((200 - best_y) / 10)
        for b in bullets:
            b[1] -= 9
            for m in monsters:
                if abs(b[0] - m[0]) < 12 and abs(b[1] - m[1]) < 14:
                    parts.burst(m[0], m[1], VIOLET, 14, 3, 16)
                    pops.add(m[0], m[1] - 10, "+200", VIOLET)
                    m[1] = 1e9
                    b[1] = -1e9
                    best_y -= 2000
        bullets = [b for b in bullets if b[1] > cam - 20]
        monsters = [m for m in monsters if m[1] < cam + H + 40]
        # Kameran följer med uppåt
        if py < cam + 100:
            cam = py - 100
        best_y = min(best_y, py)
        plats = [p for p in plats if p[1] < cam + H + 20]
        spawn_until(cam - 40)
        if py > cam + H + 20:
            return int((200 - best_y) / 10)
        draw_studs(lcd, plats, monsters, bullets, px, py, cam, face, squash, t, best_y)
        parts.draw(lcd, 0, -int(cam))
        pops.draw(lcd, 0, -int(cam))
        lcd.show()
        t += 1
        wait(t0)


S_BG = [mix((16, 20, 44), (36, 18, 56), y / (H - 1)) for y in range(H)]


def draw_studs(lcd, plats, monsters, bullets, px, py, cam, face, squash, t, best_y):
    gradient(lcd, S_BG)
    off = int(-cam) % 20
    for y in range(off, H, 20):
        lcd.hline(0, y, W, rgb(30, 32, 66))
    for x in range(0, W, 20):
        lcd.vline(x, 0, H, rgb(30, 32, 66))
    c = int(cam)
    for p in plats:
        x, y = int(p[0]), int(p[1]) - c
        col = S_PLAT_C[p[2]]
        if p[4]:
            lcd.fill_rect(x, y, 20, 6, col)
            lcd.fill_rect(x + 24, y + 2, 20, 6, col)
            continue
        lcd.fill_rect(x + 2, y, 40, 7, col)
        lcd.fill_rect(x, y + 2, 44, 3, col)
        lcd.hline(x + 3, y + 1, 38, WHITE if p[2] != 2 else rgb(220, 170, 120))
        if p[2] == 2:
            lcd.vline(x + 15, y, 7, BG)
            lcd.vline(x + 30, y, 7, BG)
        if p[2] == 3:
            lcd.fill_rect(x + 16, y - 6, 12, 6, GRAY)
            lcd.fill_rect(x + 14, y - 8, 16, 3, CORAL)
    for m in monsters:
        mx, my = int(m[0]), int(m[1] + math.sin(m[3]) * 4) - c
        lcd.ellipse(mx, my, 12, 10, VIOLET, True)
        lcd.ellipse(mx - 4, my - 3, 3, 3, WHITE, True)
        lcd.ellipse(mx + 4, my - 3, 3, 3, WHITE, True)
        lcd.pixel(mx - 4, my - 2, BLACK)
        lcd.pixel(mx + 4, my - 2, BLACK)
        lcd.hline(mx - 5, my + 5, 10, BLACK)
        for k in (-8, -2, 4):
            lcd.fill_rect(mx + k, my + 8 + (t // 5 + k) % 2, 3, 4, VIOLET)
    for b in bullets:
        lcd.ellipse(int(b[0]), int(b[1]) - c, 3, 3, AMBER, True)
    # Hopparen
    x, y = int(px), int(py) - c
    sq = 3 if squash else 0
    lcd.ellipse(x, y - 2 + sq, 9, 9 - sq, LIME, True)
    lcd.fill_rect(x - 9, y + 2, 18, 6 - sq, LIME)
    lcd.fill_rect(x - 9, y + 6 - sq, 18, 2, rgb(60, 150, 70))
    lcd.fill_rect(x + 8 if face > 0 else x - 14, y - 4, 6, 4, LIME)      # näsa
    lcd.fill_rect(x + face * 3 - 1, y - 6, 3, 3, WHITE)
    lcd.pixel(x + face * 4, y - 5, BLACK)
    for k in (-6, -1, 4):
        lcd.fill_rect(x + k, y + 8 - sq, 2, 4 + sq, rgb(60, 150, 70))
    score = int((200 - best_y) / 10)
    big(lcd, str(score), 6, 6, WHITE, 2)
    lcd.text("REKORD %d" % SCORES.get("studs", 0), 6, 26, DIM)


def icon_studs(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(16, 20, 44))
    for i, (cx, cy, k) in enumerate(((20, 60, 0), (90, 46, 1), (40, 30, 3), (110, 16, 0))):
        fb.fill_rect(x + cx, y + cy, 40, 5, S_PLAT_C[k])
    h = abs(math.sin(t * 0.08)) * 40
    bx = x + 40 + int(math.sin(t * 0.03) * 30)
    by = y + 58 - int(h)
    fb.ellipse(bx, by, 6, 6, LIME, True)
    fb.fill_rect(bx + 4, by - 2, 5, 3, LIME)


# ===============================================================
# MENYN
# ===============================================================
# (nyckel, namn, färg, beskrivning, knappar (0, 1, 3, 2), ikon, spel)
GAMES = (
    ("tetris", "TETRIS", TEAL, ("Fyll hela rader sa", "forsvinner de.", "4 rader = TETRIS!"),
     ("vanster", "hoger", "slapp", "vrid"), icon_tetris, tetris),
    ("pac", "SPOKJAKT", AMBER, ("At alla prickar!", "Stora prickar gor", "spokena atbara."),
     ("upp", "hoger", "vanster", "ner"), icon_pac, spokjakt),
    ("invasion", "INVASION", LIME, ("Skjut ner invasionen", "innan den landar.", "Full matare = laser"),
     ("vanster", "hoger", "laser", "skjut"), icon_invasion, invasion),
    ("kross", "KROSS", CORAL, ("Krossa alla stenar.", "Lila tal flera slag,", "X-stenar sprangs."),
     ("vanster", "hoger", "skjut", "skjut"), icon_kross, kross),
    ("studs", "STUDS", SKY, ("Studsa hogt upp!", "Bruna plattor gar", "sonder, gula studsar"),
     ("vanster", "hoger", "", "skjut"), icon_studs, studs),
    ("2048", "2048", PINK, ("Skjut brickorna at", "ett hall. Lika tal", "slas ihop. Na 2048!"),
     ("upp", "hoger", "vanster", "ner"), icon_2048, g2048),
    ("kurvan", "KURVAN", VIOLET, ("Rita en linje och", "krocka inte! Mot", "datorn eller 2 spel."),
     ("P1 <", "P2 <", "P1 >", "P2 >"), icon_kurvan, kurvan),
)
M_BG = [mix((16, 14, 40), (36, 14, 54), y / (H - 1)) for y in range(H)]


def menu(lcd, keys, sel):
    stars = Stars(36)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.repeat(K0, 12, 5):
            sel = (sel - 1) % len(GAMES)
        if keys.repeat(K1, 12, 5):
            sel = (sel + 1) % len(GAMES)
        if keys.pressed(K2):
            keys.wait_release()
            return sel
        key, name, col, desc, ctrl, icon, _ = GAMES[sel]
        gradient(lcd, M_BG)
        stars.draw(lcd, -0.3, 0.0)
        # Rubrik
        x = 8
        for i, ch in enumerate("PICO SPEL"):
            c = CONFETTI[(i + t // 8) % len(CONFETTI)]
            dy = int(2 * math.sin(t * 0.15 + i * 0.6))
            big(lcd, ch, x + 2, 8 + dy + 2, SHADOW, 3)
            big(lcd, ch, x, 8 + dy, c, 3)
            x += 24
        rtext(lcd, "0/1 valj", W - 6, 8, GRAY)
        rtext(lcd, "2 spela", W - 6, 20, GRAY)
        # Lista
        for i, g in enumerate(GAMES):
            y = 42 + i * 27
            if i == sel:
                lcd.fill_rect(6, y - 3, 132, 24, g[2])
                if len(g[1]) <= 7:
                    big(lcd, g[1], 14, y + 1, BG, 2)
                else:
                    big(lcd, g[1], 14, y + 5, BG, 1)
                    tri(lcd, 126, y + 4, 126, y + 14, 131, y + 9, BG)
            else:
                lcd.fill_rect(6, y - 3, 4, 24, g[2])
                lcd.text(g[1], 16, y + 6, WHITE)
        # Förhandsvisning
        lcd.fill_rect(144, 38, 172, 200, PANEL)
        lcd.rect(144, 38, 172, 200, col)
        icon(lcd, 150, 44, t)
        lcd.rect(149, 43, 162, 74, LINE)
        ctext(lcd, name, 124, col, 2, 230)
        for i, d in enumerate(desc):
            ctext(lcd, d, 146 + i * 11, GRAY, 1, 230)
        best = SCORES.get(key)
        if best:
            ctext(lcd, "Rekord: %d" % best, 182, WHITE, 1, 230)
        # Knapparna, placerade som på kortet
        a, b, c, d = ctrl
        lcd.hline(150, 198, 160, LINE)
        lcd.text("0 " + a, 152, 206, WHITE if a else DIM)
        if b:
            rtext(lcd, b + " 1", 310, 206, WHITE)
        if c:
            lcd.text("3 " + c, 152, 222, WHITE)
        if d:
            rtext(lcd, d + " 2", 310, 222, WHITE)
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
                SCORES["_sel"] = sel              # kom ihåg valt spel
                save_scores()
            key, name, col, desc, ctrl, icon, play = GAMES[sel]
            while True:
                gc.collect()
                res = play(lcd, keys)
                if res is None:
                    break
                if isinstance(res, tuple):          # KURVAN: någon vann
                    again = game_over(lcd, keys, key, res[3], res[2], "%s VANN!" % res[1],
                                      "Dina vunna rundor:")
                else:
                    again = game_over(lcd, keys, key, res, col)
                if not again:
                    break
        except KeyboardInterrupt:
            raise
        except Exception as e:
            show_error(lcd, e)
            keys.wait_release()
            while True:                         # vänta på en knapp
                keys.update()
                if any(keys.now):
                    break
                time.sleep_ms(20)


main()
