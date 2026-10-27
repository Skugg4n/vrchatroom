# HOPPA!
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Plattformsspel med 10 banor i 4 världar: Äng, Öken, Natt och Slott.
# Gubben springer av sig själv, du hoppar. Hitta de 3 stora mynten på
# varje bana. Dina framsteg sparas.
#
# Styrning (bara KEY0 och KEY1 behövs):
#   tryck 0 eller 1   = hoppa (håll inne = högre, tryck igen i luften = dubbelhopp)
#   håll 0+1          = paus / meny
#   I banväljaren: 0/1 = bläddra, 0+1 = starta banan
#
# Kör med F5 i Thonny. Vill du att spelet startar av sig själv, lägg en
# main.py på Picon med raden: import hoppa
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö.

import machine
from machine import Pin, SPI, PWM
import framebuf
import time
import random
import math
import json
import gc

try:
    import micropython
    native = micropython.native
except (ImportError, AttributeError):
    def native(f):
        return f

W, H = 320, 240


import builtins


def shared_fb():
    """Skärmbilden som startmenyn (main.py) har skapat, annars en egen."""
    fb = getattr(builtins, "PICO_FB", None)
    return fb if fb is not None else bytearray(W * H * 2)


def leave(next_prog=None):
    """Avsluta utan omstart. Startmenyn tar bort koden ur minnet och
    startar next_prog (eller visar menyn)."""
    builtins.PICO_NEXT = next_prog
    raise SystemExit
FRAME_MS = 33
SAVE_FILE = "hoppa.json"
LONG = 40
N_LEVELS = 10


def rgb(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def lerp(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


WHITE = rgb(255, 255, 255)
BLACK = rgb(0, 0, 0)
GRAY = rgb(140, 140, 170)
DIM = rgb(60, 60, 90)
BG = rgb(10, 10, 26)
YELLOW = rgb(255, 215, 40)
GOLD_D = rgb(200, 140, 20)
ORANGE = rgb(255, 140, 40)
CYAN = rgb(0, 230, 255)
RED = rgb(230, 50, 60)
GREEN = rgb(80, 220, 100)
SHADOW = rgb(30, 0, 50)
SKIN = rgb(255, 200, 150)
SHIRT = rgb(220, 40, 50)
PANTS = rgb(40, 80, 200)


# ---------------------------------------------------------------
# Skärm och knappar
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = shared_fb()
        super().__init__(self.buffer, W, H, framebuf.RGB565)
        try:
            self.bg = bytearray(W * H * 2)
        except MemoryError:
            self.bg = None
        self.bg_fn = None
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=75_000_000, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.bl.duty_u16(65535)
        self._init()

    def cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def _init(self):
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

    def show(self):
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)

    def set_bg(self, fn):
        self.bg_fn = fn
        fn(self)
        if self.bg is not None:
            self.bg[:] = self.buffer

    def load_bg(self):
        if self.bg is not None:
            self.buffer[:] = self.bg
        elif self.bg_fn:
            self.bg_fn(self)


class Keys:
    """Två knappar: tryck (räknas när man släpper), båda samtidigt, håll båda."""

    def __init__(self):
        self.pins = (Pin(15, Pin.IN, Pin.PULL_UP), Pin(17, Pin.IN, Pin.PULL_UP))
        self.now = [False, False]
        self.prev = [False, False]
        self.cnt = [0, 0]
        self.both = 0
        self.chorded = False
        self.chord_tap = False
        self.tapped = [False, False]

    def update(self):
        self.prev = self.now
        self.now = [p.value() == 0 for p in self.pins]
        old = self.cnt[:]
        for i in (0, 1):
            self.cnt[i] = self.cnt[i] + 1 if self.now[i] else 0
        both = self.now[0] and self.now[1]
        self.chord_tap = self.both > 0 and not both and self.both < LONG
        if both:
            self.chorded = True
        for i in (0, 1):
            self.tapped[i] = self.prev[i] and not self.now[i] and not self.chorded and old[i] <= 8
        self.both = self.both + 1 if both else 0
        if not self.now[0] and not self.now[1]:
            self.chorded = False

    def pressed(self, k):
        return self.now[k] and not self.prev[k]

    def long(self):
        return self.both >= LONG

    def wait_release(self):
        self.update()
        while self.now[0] or self.now[1]:
            time.sleep_ms(10)
            self.update()
        self.update()


# --- Text ------------------------------------------------------
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


def big_text(fb, s, x, y, c, scale=2):
    if scale == 1:
        fb.text(s, x, y, c)
        return
    for ch in s:
        for a, b, w in _runs(ch):
            fb.fill_rect(x + a * scale, y + b * scale, w * scale, scale, c)
        x += 8 * scale


def ctext(fb, s, y, c, scale=1, cx=W // 2):
    big_text(fb, s, cx - len(s) * 4 * scale, y, c, scale)


def stext(fb, s, y, c, scale):
    ctext(fb, s, y + 3, SHADOW, scale)
    ctext(fb, s, y, c, scale)


def frame_wait(t0):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < FRAME_MS:
        time.sleep_ms(FRAME_MS - used)


def load_save():
    try:
        with open(SAVE_FILE) as f:
            s = json.load(f)
            if len(s.get("coins", [])) == N_LEVELS:
                return s
    except Exception:
        pass
    return {"open": 1, "coins": [0] * N_LEVELS}


def store(save):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(save, f)
    except Exception:
        pass


# ---------------------------------------------------------------
# Världar (färger)
# ---------------------------------------------------------------
# namn, himmel topp, himmel botten, kullar, jord, gräs, tegel
THEMES = (
    ("ANGEN", (80, 160, 255), (200, 235, 255), (110, 190, 120), (150, 95, 55), (80, 200, 70), (210, 110, 50)),
    ("OKNEN", (255, 140, 80), (255, 225, 160), (225, 170, 100), (205, 150, 85), (240, 205, 120), (190, 120, 70)),
    ("NATTEN", (8, 10, 40), (50, 35, 90), (35, 35, 80), (70, 60, 95), (120, 110, 220), (110, 90, 150)),
    ("SLOTTET", (40, 10, 25), (130, 45, 45), (70, 25, 35), (95, 95, 110), (160, 160, 180), (120, 70, 70)),
)


def theme_of(level):
    return THEMES[min(3, (level - 1) // 3)]


T = 16                      # rutstorlek i pixlar
ROWS = 15
EMPTY, GROUND, BRICK, SPIKE, COIN, BIG, FLAG, CHECK, SPRING = range(9)
SOLID = (GROUND, BRICK)


# ---------------------------------------------------------------
# Banbygge: banan sätts ihop av bitar. Samma bana blir likadan varje
# gång eftersom slumpen startas med banans nummer.
# ---------------------------------------------------------------
def build(level):
    random.seed(level * 7919 + 13)
    cols = []                          # varje kolumn = bytearray(ROWS)
    h = 3                              # markens höjd i rutor
    diff = level

    def col(ground_h, extra=None):
        c = bytearray(ROWS)
        for r in range(ROWS - ground_h, ROWS):
            c[r] = GROUND
        if extra:
            for r, v in extra:
                c[r] = v
        cols.append(c)

    def top(hh):
        return ROWS - hh - 1           # raden ovanför marken

    for _ in range(8):
        col(h)
    n_seg = 10 + diff * 2
    check_at = n_seg // 2
    # Tre stora mynt, ett i varje tredjedel av banan
    third = n_seg // 3
    big_at = [random.randint(1, third - 1), random.randint(third, 2 * third - 1),
              random.randint(2 * third, n_seg - 2)]
    big_at = [i + 1 if i == check_at else i for i in big_at]
    for i in range(n_seg):
        big = i in big_at
        kind = random.randint(0, min(7, 2 + diff))
        if i == check_at:
            col(h, [(top(h), CHECK)])
            for _ in range(3):
                col(h)
            continue
        if kind == 0:                                  # platt med mynt
            n = random.randint(4, 7)
            for k in range(n):
                col(h, [(top(h) - 1, COIN)] if 1 <= k < n - 1 else None)
        elif kind == 1:                                # steg upp eller ner
            h = max(2, min(7, h + random.choice((-2, -1, 1, 2))))
            for _ in range(random.randint(3, 5)):
                col(h)
        elif kind == 2:                                # glapp
            w = random.randint(2, min(4, 2 + diff // 3))
            for k in range(w):
                col(0, [(top(h) - 3, COIN)] if k == w // 2 else None)
            for _ in range(3):
                col(h)
        elif kind == 3:                                # taggar
            n = random.randint(1, min(3, 1 + diff // 3))
            col(h)
            for _ in range(n):
                col(h, [(top(h), SPIKE)])
            for _ in range(3):
                col(h)
        elif kind == 4:                                # flytande tegel över glapp
            w = random.randint(4, 6)
            py = top(h) - 2
            for k in range(w):
                ex = [(py, BRICK)] if 1 <= k < w - 1 else None
                if ex and k == w // 2:
                    ex.append((py - 1, COIN))
                col(0 if 0 < k < w - 1 else h, ex)
            for _ in range(2):
                col(h)
        elif kind == 5:                                # pelare
            for _ in range(random.randint(2, 3)):
                ph = min(9, h + random.randint(1, 2))
                col(ph)
                col(ph)
                for _ in range(random.randint(2, 3)):
                    col(0)
            col(h)
            col(h)
        elif kind == 6:                                # studsmatta och hög mur
            col(h)
            col(h, [(top(h), SPRING)])
            col(h)
            wall = min(11, h + random.randint(4, 5))
            for _ in range(2):
                col(wall)
            h = max(2, wall - random.randint(2, 4))
            for _ in range(3):
                col(h)
        else:                                          # lång taggrad
            for k in range(5):
                ex = [(top(h), SPIKE)] if 1 <= k <= 3 else None
                col(h, ex)
            for _ in range(2):
                col(h)
        if big:                                        # stort mynt på en svår plats
            c = cols[-2 - random.randint(0, 2)]
            r = 0
            while r < ROWS and c[r] == EMPTY:
                r += 1
            c[max(1, r - 4)] = BIG
    for _ in range(4):
        col(h)
    col(h, [(top(h), FLAG)])
    for _ in range(12):
        col(h)
    return cols


# ---------------------------------------------------------------
# Ritning
# ---------------------------------------------------------------
def make_bg(theme):
    sky0, sky1 = theme[1], theme[2]
    sky = [rgb(*lerp(sky0, sky1, y / H)) for y in range(H)]

    def bg(lcd):
        for y in range(H):
            lcd.hline(0, y, W, sky[y])
        if theme[0] == "NATTEN":
            for i in range(50):
                lcd.pixel((i * 73 + 7) % W, (i * 41 + 3) % 150, WHITE)
            lcd.ellipse(260, 40, 16, 16, rgb(250, 245, 210), True)
        elif theme[0] == "SLOTTET":
            lcd.ellipse(250, 50, 22, 22, rgb(255, 120, 80), True)
        else:
            lcd.ellipse(260, 44, 20, 20, rgb(255, 245, 170), True)
    return bg


HILL_H = [int(40 + 22 * math.sin(i * 0.031) + 12 * math.sin(i * 0.083 + 1)) for i in range(640)]


@native
def draw_hills(fb, off, col):
    o = int(off) % 640
    for x in range(0, W, 2):
        h = HILL_H[(x + o) % 640]
        fb.fill_rect(x, 200 - h, 2, h + 40, col)


@native
def draw_tiles(fb, cols, camx, colors, t):
    ground, grass, brick, brick_d, ground_d = colors
    c0 = int(camx) // T
    off = int(camx) % T
    n = len(cols)
    for i in range(W // T + 2):
        ci = c0 + i
        if ci < 0 or ci >= n:
            continue
        x = i * T - off
        col = cols[ci]
        for r in range(ROWS):
            v = col[r]
            if v == 0:
                continue
            y = r * T
            if v == GROUND:
                fb.fill_rect(x, y, T, T, ground)
                if r == 0 or col[r - 1] != GROUND:
                    fb.fill_rect(x, y, T, 5, grass)
                    fb.fill_rect(x + 3, y + 5, 2, 2, grass)
                    fb.fill_rect(x + 10, y + 5, 2, 3, grass)
                else:
                    fb.fill_rect(x + 4 + (ci * 5 + r * 3) % 7, y + 6, 2, 2, ground_d)
            elif v == BRICK:
                fb.fill_rect(x, y, T, T, brick)
                fb.hline(x, y + 7, T, brick_d)
                fb.hline(x, y + 15, T, brick_d)
                fb.vline(x + 7, y, 8, brick_d)
                fb.vline(x + 2, y + 8, 8, brick_d)
                fb.vline(x + 12, y + 8, 8, brick_d)
            elif v == SPIKE:                           # två vassa taggar
                for k in range(14):
                    w = k * 7 // 14 + 1
                    c = WHITE if k < 3 else (GRAY if k < 11 else DIM)
                    fb.hline(x + 4 - w // 2, y + 2 + k, w, c)
                    fb.hline(x + 12 - w // 2, y + 2 + k, w, c)
                fb.hline(x, y + 15, T, DIM)
            elif v == COIN:
                w = int(5 * abs(math.sin(t * 0.15 + ci)))
                fb.ellipse(x + 8, y + 8, w + 1, 6, YELLOW, True)
                fb.ellipse(x + 8, y + 8, max(0, w - 1), 3, GOLD_D, True)
            elif v == BIG:
                fb.ellipse(x + 8, y + 8, 9, 9, GOLD_D, True)
                fb.ellipse(x + 8, y + 8, 7, 7, YELLOW, True)
                fb.fill_rect(x + 7, y + 3, 2, 10, GOLD_D)
            elif v == FLAG:
                fb.fill_rect(x + 6, y - 5 * T, 3, 6 * T, WHITE)
                wav = int(2 * math.sin(t * 0.2))
                fb.fill_rect(x + 9, y - 5 * T + 2 + wav, 16, 11, GREEN)
                fb.ellipse(x + 7, y - 5 * T, 4, 4, YELLOW, True)
            elif v == CHECK:
                fb.fill_rect(x + 6, y - T, 2, 2 * T, GRAY)
                fb.fill_rect(x + 8, y - T, 10, 7, CYAN)
            elif v == SPRING:
                fb.fill_rect(x + 2, y + 10, 12, 6, GRAY)
                fb.fill_rect(x + 1, y + 6, 14, 4, RED)


def draw_hero(fb, x, y, t, on_ground, vy):
    # x, y = övre vänstra hörnet av en 12x18 kropp
    fb.fill_rect(x + 2, y, 9, 4, SHIRT)                   # keps
    fb.fill_rect(x + 8, y + 3, 5, 2, SHIRT)
    fb.fill_rect(x + 2, y + 4, 8, 5, SKIN)                # ansikte
    fb.fill_rect(x + 7, y + 5, 2, 2, BLACK)               # öga
    fb.fill_rect(x + 1, y + 9, 10, 5, SHIRT)              # tröja
    fb.fill_rect(x + 1, y + 13, 10, 2, PANTS)
    if not on_ground:
        fb.fill_rect(x + 10, y + 8 if vy < 0 else y + 11, 3, 3, SKIN)   # arm upp
        fb.fill_rect(x + 1, y + 15, 4, 3, PANTS)
        fb.fill_rect(x + 7, y + 14, 4, 3, PANTS)
    else:
        step = (t // 3) % 4
        fb.fill_rect(x + 4, y + 10, 3, 3, SKIN)
        a = (0, 2, 4, 2)[step]
        fb.fill_rect(x + 1 + a, y + 15, 4, 3, PANTS)
        fb.fill_rect(x + 7 - a, y + 15, 4, 3, PANTS)


# ---------------------------------------------------------------
# En bana
# ---------------------------------------------------------------
HW, HH = 12, 18


def tile_at(cols, px, py):
    ci = int(px) // T
    r = int(py) // T
    if ci < 0 or ci >= len(cols) or r < 0 or r >= ROWS:
        return EMPTY
    return cols[ci][r]


def play(lcd, keys, level):
    """Returnerar ('klar', stora mynt) eller ('meny', 0)."""
    th = theme_of(level)
    cols = build(level)
    total_big = sum(1 for c in cols for v in c if v == BIG)
    colors = (rgb(*th[4]), rgb(*th[5]), rgb(*th[6]),
              rgb(*lerp(th[6], (0, 0, 0), 0.4)), rgb(*lerp(th[4], (0, 0, 0), 0.3)))
    hill = rgb(*th[3])
    speed = 2.3 + level * 0.07
    gravity, hold_g, jump_v, djump_v = 0.55, 0.32, -7.2, -6.4
    lcd.set_bg(make_bg(th))

    def spawn_y(x):
        c = cols[int(x) // T]
        r = 0
        while r < ROWS and c[r] not in SOLID:
            r += 1
        return r * T - HH

    start_x = 2 * T
    px = float(start_x)
    py = float(spawn_y(px))
    vy = 0.0
    on_ground = True
    jumps = 0
    coins = 0
    bigs = 0
    taken = []                        # (kolumn, rad, typ) som plockats sedan senaste kontrollpunkt
    check_x = start_x
    deaths = 0
    parts = []
    dead_t = 0
    banner = 50
    t = 0
    flag_x = 0
    for i, c in enumerate(cols):
        for v in c:
            if v == FLAG:
                flag_x = i * T
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.long():
            if pause(lcd, keys):
                return "meny", 0
            lcd.set_bg(make_bg(th))
            keys.wait_release()

        if dead_t > 0:
            dead_t -= 1
            if dead_t == 0:
                px = float(check_x)
                py = float(spawn_y(px))
                vy = 0.0
                jumps = 0
        else:
            jump_press = keys.pressed(0) or keys.pressed(1)
            jump_held = keys.now[0] or keys.now[1]
            if jump_press and not keys.chorded:
                if on_ground:
                    vy = jump_v
                    jumps = 1
                elif jumps < 2:
                    vy = djump_v
                    jumps = 2
                    for _ in range(6):
                        parts.append([px + 6, py + HH, random.uniform(-2, 2), random.uniform(0, 2), 10, WHITE])
            # Fart framåt, stopp mot väggar
            nx = px + speed
            if tile_at(cols, nx + HW, py + 2) in SOLID or tile_at(cols, nx + HW, py + HH - 2) in SOLID:
                nx = (int(nx + HW) // T) * T - HW - 0.01
            px = nx
            # Tyngdkraft (lägre medan man håller in hoppet och är på väg upp)
            vy += hold_g if (jump_held and vy < 0) else gravity
            if vy > 9:
                vy = 9
            ny = py + vy
            on_ground = False
            if vy >= 0:
                if tile_at(cols, px + 2, ny + HH) in SOLID or tile_at(cols, px + HW - 2, ny + HH) in SOLID:
                    ny = (int(ny + HH) // T) * T - HH
                    vy = 0.0
                    on_ground = True
                    jumps = 0
            else:
                if tile_at(cols, px + 2, ny) in SOLID or tile_at(cols, px + HW - 2, ny) in SOLID:
                    ny = (int(ny) // T + 1) * T
                    vy = 0.0
            py = ny
            # Saker man rör vid
            died = py > H + 20
            for sx, sy in ((px + 3, py + 3), (px + HW - 3, py + 3), (px + 3, py + HH - 2),
                           (px + HW - 3, py + HH - 2), (px + HW // 2, py + HH // 2)):
                ci, r = int(sx) // T, int(sy) // T
                if 0 <= ci < len(cols) and 0 <= r < ROWS:
                    v = cols[ci][r]
                    if v == SPIKE and (sy % T) > 6:
                        died = True
                    elif v == COIN:
                        cols[ci][r] = EMPTY
                        coins += 1
                        taken.append((ci, r, COIN))
                    elif v == BIG:
                        cols[ci][r] = EMPTY
                        bigs += 1
                        taken.append((ci, r, BIG))
                        for _ in range(14):
                            parts.append([sx, sy, random.uniform(-3, 3), random.uniform(-4, 1), 18, YELLOW])
                    elif v == CHECK and ci * T > check_x:
                        check_x = ci * T
                        taken = []
                        banner = -40                  # visa "kontrollpunkt"
                    elif v == SPRING and vy >= 0:
                        vy = -11.5
                        jumps = 1
            if px >= flag_x:
                return "klar", bigs
            if died:
                deaths += 1
                dead_t = 30
                for _ in range(20):
                    parts.append([px + 6, py + 9, random.uniform(-4, 4), random.uniform(-6, 1), 25, SHIRT])
                # Lägg tillbaka det som plockats sedan kontrollpunkten
                for ci, r, v in taken:
                    cols[ci][r] = v
                    if v == COIN:
                        coins -= 1
                    else:
                        bigs -= 1
                taken = []

        # --- Rita ---
        camx = max(0.0, px - 90)
        lcd.load_bg()
        draw_hills(lcd, camx * 0.3, hill)
        draw_tiles(lcd, cols, camx, colors, t)
        for p in parts[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.3
            p[4] -= 1
            if p[4] <= 0:
                parts.remove(p)
            else:
                lcd.fill_rect(int(p[0] - camx), int(p[1]), 3, 3, p[5])
        if dead_t == 0:
            draw_hero(lcd, int(px - camx), int(py), t, on_ground, vy)
        # Överst: bana, mynt, stora mynt och hur långt man kommit
        lcd.fill_rect(0, 0, W, 14, BLACK)
        lcd.text("%d-%d" % ((level - 1) // 3 + 1, (level - 1) % 3 + 1), 4, 3, WHITE)
        lcd.ellipse(54, 7, 4, 4, YELLOW, True)
        lcd.text("%d" % coins, 62, 3, WHITE)
        for i in range(total_big):
            lcd.ellipse(110 + i * 14, 7, 5, 5, YELLOW if i < bigs else DIM, i < bigs)
        lcd.text("X%d" % deaths, 160, 3, GRAY)
        lcd.hline(200, 7, 110, DIM)
        prog = min(1.0, px / max(1, flag_x))
        lcd.fill_rect(200 + int(110 * prog) - 2, 4, 5, 7, CYAN)
        if banner > 0:
            banner -= 1
            stext(lcd, "%s %d" % (th[0], (level - 1) % 3 + 1), 70, WHITE, 3)
            ctext(lcd, "Tryck 0 eller 1 for att hoppa", 110, WHITE)
        elif banner < 0:
            banner += 1
            ctext(lcd, "KONTROLLPUNKT!", 60, CYAN, 2)
        lcd.show()
        t += 1
        frame_wait(t0)


def pause(lcd, keys):
    keys.wait_release()
    sel = 0
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.tapped[0] or keys.tapped[1]:
            sel = 1 - sel
        if keys.chord_tap:
            return sel == 1
        lcd.fill_rect(70, 70, 180, 100, BLACK)
        lcd.rect(70, 70, 180, 100, YELLOW)
        ctext(lcd, "PAUS", 80, YELLOW, 3)
        for i, s in enumerate(("FORTSATT", "TILL BANORNA")):
            if i == sel:
                lcd.fill_rect(90, 114 + i * 20, 140, 16, YELLOW)
            ctext(lcd, s, 118 + i * 20, BG if i == sel else WHITE)
        lcd.text("0/1 valj  0+1 ok", 96, 158, GRAY)
        lcd.show()
        frame_wait(t0)


def level_done(lcd, keys, level, bigs, save):
    best = save["coins"][level - 1]
    if bigs > best:
        save["coins"][level - 1] = bigs
    if level < N_LEVELS and save["open"] < level + 1:
        save["open"] = level + 1
    store(save)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 20 and (keys.chord_tap or keys.tapped[0] or keys.tapped[1]):
            return
        lcd.fill(BG)
        for _ in range(30):
            lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3,
                          random.choice((YELLOW, CYAN, GREEN, RED)))
        stext(lcd, "BANAN KLAR!", 40 + int(4 * math.sin(t * 0.2)), GREEN, 3)
        for i in range(3):
            x = W // 2 - 50 + i * 50
            got = i < bigs
            pop = got and t > 10 + i * 8
            r = 18 if pop else 16
            lcd.ellipse(x, 120, r, r, GOLD_D if got else DIM, True)
            lcd.ellipse(x, 120, r - 4, r - 4, YELLOW if got else BG, True)
        ctext(lcd, "Stora mynt: %d av 3" % bigs, 160, WHITE, 2)
        if level == N_LEVELS:
            ctext(lcd, "Du klarade alla banor!", 190, YELLOW)
        if (t // 10) % 2 == 0:
            ctext(lcd, "Tryck for att fortsatta", 220, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def select(lcd, keys, save, sel):
    """Banväljaren. Returnerar vald bana."""
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.tapped[0]:
            sel = (sel - 2) % N_LEVELS + 1
        if keys.tapped[1]:
            sel = sel % N_LEVELS + 1
        if keys.chord_tap and sel <= save["open"]:
            return sel
        if keys.long():
            leave()                              # tillbaka till startmenyn
        th = theme_of(sel)
        top = rgb(*lerp(th[1], (0, 0, 0), 0.5))
        lcd.fill(top)
        stext(lcd, "HOPPA!", 12 + int(3 * math.sin(t * 0.12)), YELLOW, 4)
        total = sum(save["coins"])
        ctext(lcd, "Stora mynt: %d av %d" % (total, N_LEVELS * 3), 50, WHITE)
        for i in range(N_LEVELS):
            n = i + 1
            x = 22 + (i % 5) * 58
            y = 72 + (i // 5) * 70
            open_ = n <= save["open"]
            tcol = rgb(*theme_of(n)[5]) if open_ else DIM
            if n == sel:
                lcd.fill_rect(x - 4, y - 4, 56, 62, WHITE)
            lcd.fill_rect(x, y, 48, 54, tcol)
            lcd.fill_rect(x + 2, y + 2, 44, 50, BG)
            if open_:
                ctext(lcd, str(n), y + 8, WHITE, 2, cx=x + 24)
                for k in range(3):
                    got = k < save["coins"][i]
                    lcd.ellipse(x + 10 + k * 14, y + 40, 5, 5, YELLOW if got else DIM, True)
            else:
                lcd.fill_rect(x + 16, y + 22, 16, 13, GRAY)       # hänglås
                lcd.rect(x + 19, y + 14, 10, 10, GRAY)
        ctext(lcd, "%s - bana %d" % (theme_of(sel)[0], sel), 214, WHITE)
        ctext(lcd, "0/1 valj  0+1 spela  hall 0+1 meny" if sel <= save["open"]
              else "Last! Klara banan innan", 228, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def main():
    try:
        machine.freq(250_000_000)
    except Exception:
        pass
    gc.collect()
    lcd = LCD()
    keys = Keys()
    save = load_save()
    sel = save["open"]
    while True:
        sel = select(lcd, keys, save, sel)
        while True:
            gc.collect()
            res, bigs = play(lcd, keys, sel)
            if res == "meny":
                break
            level_done(lcd, keys, sel, bigs, save)
            if sel < N_LEVELS:
                sel += 1
            break


main()
