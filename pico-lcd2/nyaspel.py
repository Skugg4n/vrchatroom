# NYA SPEL - METEORER, TURBO, BUBBLOR och MINIGOLF i en fil
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Alla fyra spelen får inte plats i minnet samtidigt. Därför packar den
# här filen första gången upp sig själv till små filer på Picon
# (ny_lib.py, ny_meteor.py, ny_turbo.py, ny_bubblor.py, ny_minigolf.py
# och ny_meny.py). Sedan laddas bara det spel du valt.
# Ladda bara upp den här filen. Ändra i den här filen, inte i ny_*.py,
# de skrivs över när versionen ändras.
#
# Spelen startas från korten i Pico Arcade (main2.py). Kör du filen
# direkt med F5 i Thonny får du en egen liten meny.

import json
import machine
import gc

VERSION = "2"
FILES = {
    'ny_lib.py': r'''# picolib - gemensam grund för spelen i Pico Arcade
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Skärm, fyra knappar, text, stjärnhimmel, rekord och gemensamma skärmar
# (titel, paus, game over). Spelen startas från Pico Arcade och går
# tillbaka dit med back().
#
# Knapparnas placering:  KEY0 uppe till vänster   KEY1 uppe till höger
#                        KEY3 nere till vänster   KEY2 nere till höger
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
KEY_PINS = (15, 17, 2, 3)
K0, K1, K2, K3 = 0, 1, 2, 3
SCORE_FILE = "rekord.json"
START_FILE = "starta.txt"


def rgb(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


def lerp(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def mix(c1, c2, t):
    return rgb(*lerp(c1, c2, t))


BLACK = rgb(0, 0, 0)
WHITE = rgb(255, 255, 255)
BG = rgb(6, 6, 22)
DIM = rgb(50, 50, 90)
GRAY = rgb(140, 140, 170)
CYAN = rgb(0, 230, 255)
MAGENTA = rgb(255, 40, 200)
YELLOW = rgb(255, 220, 40)
ORANGE = rgb(255, 140, 40)
GREEN = rgb(80, 230, 90)
RED = rgb(255, 50, 70)
BLUE = rgb(60, 110, 255)
PURPLE = rgb(180, 80, 255)
SHADOW = rgb(40, 0, 70)
GRADIENT = [mix((8, 8, 40), (45, 0, 60), y / (H - 1)) for y in range(H)]
RAINBOW = [mix((0, 230, 255), (255, 40, 200), i / 10) for i in range(11)]
STAR_COLS = (rgb(70, 70, 110), rgb(150, 150, 200), rgb(255, 255, 255))


# ---------------------------------------------------------------
# Skärm
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = bytearray(W * H * 2)
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

    def set_bg(self, fn):
        """Ritar en bakgrund en gång och sparar den."""
        self.bg_fn = fn
        fn(self)
        if self.bg is not None:
            self.bg[:] = self.buffer

    def load_bg(self):
        if self.bg is not None:
            self.buffer[:] = self.bg
        elif self.bg_fn:
            self.bg_fn(self)


# ---------------------------------------------------------------
# Knappar
# ---------------------------------------------------------------
class Keys:
    def __init__(self):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in KEY_PINS]
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
        return self.now[k] and not self.prev[k]

    def released(self, k):
        return self.prev[k] and not self.now[k]

    def repeat(self, k, delay=8, rate=3):
        c = self.cnt[k]
        return c == 1 or (c > delay and (c - delay) % rate == 0)

    def any_pressed(self):
        for i in range(4):
            if self.now[i] and not self.prev[i]:
                return True
        return False

    def menu(self):
        """Alla fyra knapparna nere en kort stund = paus/meny."""
        return self.all_cnt >= 8

    def wait_release(self):
        self.update()
        while any(self.now):
            time.sleep_ms(10)
            self.update()
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
def big_text(fb, s, x, y, c, scale=2):
    if scale == 1:
        fb.text(s, x, y, c)
        return
    fr = fb.fill_rect
    for ch in s:
        for run in _runs(ch):
            fr(x + run[0] * scale, y + run[1] * scale, run[2] * scale, scale, c)
        x += 8 * scale


def ctext(fb, s, y, c, scale=1, cx=W // 2):
    big_text(fb, s, cx - len(s) * 4 * scale, y, c, scale)


def stext(fb, s, y, c, scale=2, cx=W // 2):
    ctext(fb, s, y + scale + 1, SHADOW, scale, cx)
    ctext(fb, s, y, c, scale, cx)


def wave(fb, s, y, scale, cols, t, amp=3):
    x = (W - len(s) * 8 * scale) // 2
    for i, ch in enumerate(s):
        if ch != " ":
            dy = int(amp * math.sin(t * 0.15 + i * 0.7))
            big_text(fb, ch, x + 3, y + dy + 3, SHADOW, scale)
            big_text(fb, ch, x, y + dy, cols[i % len(cols)], scale)
        x += 8 * scale


def draw_gradient(lcd):
    for y in range(H):
        lcd.hline(0, y, W, GRADIENT[y])


_fps = [0, 0]


def frame_wait(t0, ms=33):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < ms:
        time.sleep_ms(ms - used)
    _fps[0] += 1
    if _fps[0] >= 150:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, _fps[1])
        if dt > 0:
            print("FPS: %d" % (150000 // dt))
        _fps[0] = 0
        _fps[1] = now


class Stars:
    def __init__(self, n=50):
        self.s = [[random.randint(0, W - 1), random.randint(0, H - 1), random.randint(1, 3)]
                  for _ in range(n)]

    @native
    def draw(self, fb, dx=-1.0, dy=0.0):
        for s in self.s:
            s[0] += dx * s[2]
            s[1] += dy * s[2]
            if s[0] < 0:
                s[0] += W
            elif s[0] >= W:
                s[0] -= W
            if s[1] < 0:
                s[1] += H
            elif s[1] >= H:
                s[1] -= H
            fb.pixel(int(s[0]), int(s[1]), STAR_COLS[s[2] - 1])


class Popups:
    """Flytande poängtexter, t.ex. "+100"."""

    def __init__(self):
        self.p = []

    def add(self, x, y, txt, col=YELLOW):
        if len(self.p) < 12:
            self.p.append([x, y, txt, col, 30])

    def draw(self, fb, ox=0, oy=0):
        for p in self.p[:]:
            p[1] -= 0.8
            p[4] -= 1
            if p[4] <= 0:
                self.p.remove(p)
            else:
                fb.text(p[2], int(p[0]) - len(p[2]) * 4 + ox, int(p[1]) + oy,
                        p[3] if p[4] > 6 or p[4] % 2 else WHITE)


class Particles:
    def __init__(self, cap=120):
        self.p = []
        self.cap = cap

    def burst(self, x, y, col, n=12, speed=3.0, life=20, grav=0.0):
        for _ in range(n):
            if len(self.p) >= self.cap:
                return
            a = random.uniform(0, 6.283)
            v = random.uniform(0.3, 1.0) * speed
            self.p.append([x, y, math.cos(a) * v, math.sin(a) * v, life + random.randint(0, 8), col, grav])

    @native
    def draw(self, fb, ox=0, oy=0):
        alive = []
        for p in self.p:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[6]
            p[2] *= 0.96
            p[3] *= 0.96
            p[4] -= 1
            if p[4] > 0:
                alive.append(p)
                sz = 2 if p[4] > 8 else 1
                fb.fill_rect(int(p[0]) + ox, int(p[1]) + oy, sz, sz, p[5])
        self.p = alive


class Shake:
    def __init__(self):
        self.a = 0.0

    def hit(self, amount):
        self.a = max(self.a, amount)

    def offset(self):
        if self.a < 0.5:
            self.a = 0.0
            return 0, 0
        a = self.a
        self.a *= 0.85
        return random.randint(-int(a), int(a)), random.randint(-int(a), int(a))


# ---------------------------------------------------------------
# Rekord (delas med Pico Arcade)
# ---------------------------------------------------------------
def load_scores():
    try:
        with open(SCORE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


SCORES = load_scores()


def save_scores():
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(SCORES, f)
    except Exception:
        pass


def submit(key, score, lower_is_better=False):
    """Returnerar (rekord, nytt_rekord?)."""
    best = SCORES.get(key)
    better = best is None or (score < best if lower_is_better else score > best)
    if better and (lower_is_better or score > 0):
        SCORES[key] = score
        save_scores()
        return score, True
    return (best if best is not None else score), False


# ---------------------------------------------------------------
# Start och tillbaka
# ---------------------------------------------------------------
def init():
    try:
        machine.freq(250_000_000)
    except Exception:
        pass
    gc.collect()
    lcd = LCD()
    keys = Keys()
    _fps[1] = time.ticks_ms()
    return lcd, keys


def back():
    """Tillbaka till Pico Arcade (startar om Picon mjukt)."""
    try:
        with open(START_FILE, "w") as f:
            f.write("main2")
    except Exception:
        pass
    machine.soft_reset()


# ---------------------------------------------------------------
# Gemensamma skärmar
# ---------------------------------------------------------------
def legend(fb, y, k0, k1, k3, k2, col=GRAY):
    """Visar vad knapparna gör, placerade som på kortet."""
    fb.text("0 " + k0, 20, y, col)
    fb.text(k1 + " 1", W - 20 - (len(k1) + 2) * 8, y, col)
    fb.text("3 " + k3, 20, y + 12, col)
    fb.text(k2 + " 2", W - 20 - (len(k2) + 2) * 8, y + 12, col)


def title(lcd, keys, name, col, lines, key, controls, anim=None, record_fmt="Rekord: %d"):
    """Titelskärm. True = spela, False = tillbaka till arcaden.
    controls = (KEY0, KEY1, KEY3, KEY2) beskrivningar."""
    stars = Stars(50)
    lcd.set_bg(draw_gradient)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 5:
            if keys.pressed(K2):
                return True
            if keys.pressed(K3):
                return False
        lcd.load_bg()
        stars.draw(lcd)
        if anim:
            anim(lcd, t)
        wave(lcd, name, 18, 4 if len(name) <= 9 else 3, [col, WHITE, col], t)
        for i, ln in enumerate(lines):
            ctext(lcd, ln, 70 + i * 12, WHITE)
        best = SCORES.get(key)
        if best is not None:
            ctext(lcd, record_fmt % best, 70 + len(lines) * 12 + 8, col)
        legend(lcd, 176, *controls)
        if (t // 10) % 2 == 0:
            ctext(lcd, "2: SPELA", 210, YELLOW, 2)
        ctext(lcd, "3: tillbaka", 230, DIM)
        lcd.show()
        t += 1
        frame_wait(t0)


def pause(lcd, keys):
    """True = avsluta spelet."""
    lcd.fill_rect(70, 74, 180, 92, BG)
    lcd.rect(70, 74, 180, 92, YELLOW)
    ctext(lcd, "PAUS", 86, YELLOW, 3)
    ctext(lcd, "2: fortsatt", 122, WHITE)
    ctext(lcd, "3: avsluta", 138, WHITE)
    lcd.show()
    keys.wait_release()
    while True:
        keys.update()
        if keys.pressed(K2):
            keys.wait_release()
            return False
        if keys.pressed(K3):
            return True
        time.sleep_ms(20)


def result(lcd, keys, head, score_txt, key, score, col, lower_is_better=False, extra=""):
    """Slutskärm med rekord. True = spela igen."""
    best, new = submit(key, score, lower_is_better)
    stars = Stars(40)
    lcd.set_bg(draw_gradient)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 12:
            if keys.pressed(K2):
                return True
            if keys.pressed(K3):
                return False
        lcd.load_bg()
        stars.draw(lcd)
        if new:
            for _ in range(36):
                lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3,
                              random.choice(RAINBOW))
        dy = int(4 * math.sin(t * 0.2))
        stext(lcd, head, 34 + dy, col, 3)
        ctext(lcd, score_txt, 84, WHITE, 5)
        if extra:
            ctext(lcd, extra, 134, GRAY)
        if new:
            if (t // 8) % 2 == 0:
                ctext(lcd, "NYTT REKORD!", 156, YELLOW, 2)
        else:
            ctext(lcd, "Rekord: %s" % best, 160, GRAY)
        ctext(lcd, "2: spela igen    3: till arcaden", 214, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)
''',
    'ny_meteor.py': r'''# METEORER - ett Asteroids-spel för Pico Arcade
#
#   KEY0 (uppe vänster)  = sväng vänster
#   KEY1 (uppe höger)    = sväng höger
#   KEY3 (nere vänster)  = gasa
#   KEY2 (nere höger)    = skjut (håll inne för att skjuta hela tiden)
#   alla fyra            = paus
#
# Uppackad från nyaspel.py, ändra i nyaspel.py i stället.

from ny_lib import *

ROT = 0.11
THRUST = 0.16
FRICTION = 0.988
MAX_V = 5.5
BULLET_V = 7.0
BULLET_LIFE = 34
SIZES = (0, 7, 14, 26)               # radie per storlek
POINTS = (0, 100, 50, 20)
ROCK_COLS = (0, rgb(255, 200, 140), rgb(200, 190, 255), rgb(150, 170, 230))
SHIP_COL = rgb(120, 255, 240)
UFO_COL = rgb(255, 90, 200)


def make_rock(x, y, size, speed):
    n = 9 + size
    shape = []
    for i in range(n):
        a = i / n * 6.283
        r = SIZES[size] * random.uniform(0.72, 1.12)
        shape.append((math.cos(a) * r, math.sin(a) * r))
    a = random.uniform(0, 6.283)
    v = random.uniform(0.4, 1.0) * speed * (1.6 - size * 0.25)
    return [x, y, math.cos(a) * v, math.sin(a) * v, size, shape, random.uniform(0, 6.28),
            random.uniform(-0.04, 0.04)]


@native
def draw_poly(fb, pts, x, y, ang, col):
    ca = math.cos(ang)
    sa = math.sin(ang)
    n = len(pts)
    px = x + pts[n - 1][0] * ca - pts[n - 1][1] * sa
    py = y + pts[n - 1][0] * sa + pts[n - 1][1] * ca
    for i in range(n):
        qx = x + pts[i][0] * ca - pts[i][1] * sa
        qy = y + pts[i][0] * sa + pts[i][1] * ca
        fb.line(int(px), int(py), int(qx), int(qy), col)
        px = qx
        py = qy


SHIP = ((11, 0), (-8, -7), (-4, 0), (-8, 7))
FLAME = ((-5, -3), (-13, 0), (-5, 3))


def wrap(o, r):
    if o[0] < -r:
        o[0] += W + 2 * r
    elif o[0] > W + r:
        o[0] -= W + 2 * r
    if o[1] < -r:
        o[1] += H + 2 * r
    elif o[1] > H + r:
        o[1] -= H + 2 * r


def draw_rock(fb, r, ox, oy):
    col = ROCK_COLS[r[4]]
    # Två lager linjer ger en svag glöd
    draw_poly(fb, r[5], r[0] + ox + 1, r[1] + oy + 1, r[6], DIM)
    draw_poly(fb, r[5], r[0] + ox, r[1] + oy, r[6], col)


def draw_ufo(fb, u, ox, oy, t):
    x, y = int(u[0]) + ox, int(u[1]) + oy
    fb.ellipse(x, y, 13, 4, UFO_COL)
    fb.ellipse(x, y - 4, 6, 4, UFO_COL)
    fb.hline(x - 13, y, 26, UFO_COL)
    if (t // 4) % 2:
        fb.pixel(x - 6, y + 2, YELLOW)
        fb.pixel(x + 6, y + 2, YELLOW)


def play(lcd, keys):
    stars = Stars(40)
    parts = Particles(140)
    pops = Popups()
    shake = Shake()
    ship = [W / 2, H / 2, 0.0, 0.0, -1.5708]   # x, y, vx, vy, vinkel
    bullets = []                              # [x, y, vx, vy, liv]
    rocks = []
    ufo = None                                # [x, y, vx, skottklocka]
    ufo_shots = []
    lives, score, wave_n = 3, 0, 0
    next_life = 10000
    inv = 90
    cool = 0
    dead = 0
    banner = 0
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.menu():
            if pause(lcd, keys):
                return None
        # Ny våg när alla stenar är borta
        if not rocks and dead == 0:
            wave_n += 1
            for _ in range(min(3 + wave_n, 9)):
                while True:
                    x, y = random.uniform(0, W), random.uniform(0, H)
                    if (x - ship[0]) ** 2 + (y - ship[1]) ** 2 > 90 * 90:
                        break
                rocks.append(make_rock(x, y, 3, 1.0 + wave_n * 0.08))
            banner = 60
            inv = max(inv, 40)

        thrusting = False
        if dead == 0:
            if keys.held(K0):
                ship[4] -= ROT
            if keys.held(K1):
                ship[4] += ROT
            ca, sa = math.cos(ship[4]), math.sin(ship[4])
            if keys.held(K3):
                thrusting = True
                ship[2] += ca * THRUST
                ship[3] += sa * THRUST
                if t % 2 == 0:
                    parts.p.append([ship[0] - ca * 9, ship[1] - sa * 9,
                                    -ca * 2 + random.uniform(-0.6, 0.6),
                                    -sa * 2 + random.uniform(-0.6, 0.6), 10,
                                    ORANGE if t % 4 else YELLOW, 0.0])
            sp = math.sqrt(ship[2] ** 2 + ship[3] ** 2)
            if sp > MAX_V:
                ship[2] *= MAX_V / sp
                ship[3] *= MAX_V / sp
            ship[2] *= FRICTION
            ship[3] *= FRICTION
            ship[0] += ship[2]
            ship[1] += ship[3]
            wrap(ship, 10)
            if cool > 0:
                cool -= 1
            if (keys.pressed(K2) or (keys.held(K2) and cool == 0)) and len(bullets) < 6:
                bullets.append([ship[0] + ca * 11, ship[1] + sa * 11,
                                ca * BULLET_V + ship[2], sa * BULLET_V + ship[3], BULLET_LIFE])
                cool = 7
        else:
            dead -= 1
            if dead == 0:
                if lives <= 0:
                    return score
                ship = [W / 2, H / 2, 0.0, 0.0, -1.5708]
                inv = 120

        # Skott
        for b in bullets:
            b[0] += b[2]
            b[1] += b[3]
            b[4] -= 1
            wrap(b, 2)
        bullets = [b for b in bullets if b[4] > 0]

        # Stenar
        new_rocks = []
        for r in rocks:
            r[0] += r[2]
            r[1] += r[3]
            r[6] += r[7]
            wrap(r, SIZES[r[4]])
            rad = SIZES[r[4]]
            hit = False
            for b in bullets:
                if (b[0] - r[0]) ** 2 + (b[1] - r[1]) ** 2 < (rad + 2) ** 2:
                    b[4] = 0
                    hit = True
                    break
            if hit:
                score += POINTS[r[4]]
                pops.add(r[0], r[1] - rad, "+%d" % POINTS[r[4]])
                parts.burst(r[0], r[1], ROCK_COLS[r[4]], 6 + r[4] * 5, 2.5 + r[4] * 0.6, 18)
                shake.hit(r[4] * 2.2)
                if r[4] > 1:
                    for _ in range(2):
                        new_rocks.append(make_rock(r[0], r[1], r[4] - 1, 1.2 + wave_n * 0.1))
                continue
            new_rocks.append(r)
            if dead == 0 and inv == 0 and \
                    (r[0] - ship[0]) ** 2 + (r[1] - ship[1]) ** 2 < (rad + 6) ** 2:
                dead = 70
        rocks = new_rocks

        # UFO från våg 3
        if ufo is None and wave_n >= 3 and random.random() < 0.003:
            side = random.choice((-1, 1))
            ufo = [W + 15 if side < 0 else -15, random.uniform(30, H - 30), 1.4 * side, 50]
        if ufo:
            ufo[0] += ufo[2]
            ufo[1] += math.sin(t * 0.05) * 0.8
            ufo[3] -= 1
            if ufo[3] <= 0 and dead == 0:
                ufo[3] = 55
                a = math.atan2(ship[1] - ufo[1], ship[0] - ufo[0]) + random.uniform(-0.3, 0.3)
                ufo_shots.append([ufo[0], ufo[1], math.cos(a) * 3.2, math.sin(a) * 3.2, 80])
            for b in bullets:
                if abs(b[0] - ufo[0]) < 13 and abs(b[1] - ufo[1]) < 7:
                    b[4] = 0
                    score += 500
                    pops.add(ufo[0], ufo[1] - 10, "+500", MAGENTA)
                    parts.burst(ufo[0], ufo[1], UFO_COL, 24, 3.5, 24)
                    shake.hit(6)
                    ufo = None
                    break
            if ufo and (ufo[0] < -30 or ufo[0] > W + 30):
                ufo = None
        for s in ufo_shots:
            s[0] += s[2]
            s[1] += s[3]
            s[4] -= 1
            wrap(s, 2)
            if dead == 0 and inv == 0 and (s[0] - ship[0]) ** 2 + (s[1] - ship[1]) ** 2 < 64:
                s[4] = 0
                dead = 70
        ufo_shots = [s for s in ufo_shots if s[4] > 0]

        if dead == 70:                        # skeppet sprängdes precis
            lives -= 1
            parts.burst(ship[0], ship[1], SHIP_COL, 30, 4, 30)
            parts.burst(ship[0], ship[1], ORANGE, 20, 2.5, 24)
            shake.hit(9)
        if score >= next_life:
            lives += 1
            next_life += 10000
            pops.add(W / 2, 60, "EXTRA LIV!", GREEN)
        if inv > 0:
            inv -= 1

        # --- Rita ---
        ox, oy = shake.offset()
        lcd.fill(BLACK)
        stars.draw(lcd, 0.0, 0.0)
        for r in rocks:
            draw_rock(lcd, r, ox, oy)
        if ufo:
            draw_ufo(lcd, ufo, ox, oy, t)
        for b in bullets:
            lcd.fill_rect(int(b[0]) - 1 + ox, int(b[1]) - 1 + oy, 3, 3, YELLOW)
        for s in ufo_shots:
            lcd.fill_rect(int(s[0]) - 1 + ox, int(s[1]) - 1 + oy, 3, 3, MAGENTA)
        parts.draw(lcd, ox, oy)
        if dead == 0 and (inv == 0 or (t // 3) % 2 == 0):
            draw_poly(lcd, SHIP, ship[0] + ox, ship[1] + oy, ship[4], SHIP_COL)
            if thrusting and t % 2 == 0:
                draw_poly(lcd, FLAME, ship[0] + ox, ship[1] + oy, ship[4], ORANGE)
        pops.draw(lcd, ox, oy)
        big_text(lcd, str(score), 6, 4, WHITE, 2)
        for i in range(lives):
            draw_poly(lcd, SHIP, W - 14 - i * 16, 12, -1.5708, SHIP_COL)
        if banner > 0:
            banner -= 1
            stext(lcd, "VAG %d" % wave_n, 96, CYAN, 3)
        lcd.show()
        t += 1
        frame_wait(t0)


def demo(lcd, t):
    """Stenar som svävar bakom titeln."""
    for i in range(5):
        x = (i * 71 + t * (0.6 + i * 0.15)) % (W + 60) - 30
        y = 60 + (i * 47) % 120
        pts = DEMO_ROCKS[i]
        draw_poly(lcd, pts, x, y, t * 0.01 * (i + 1), ROCK_COLS[1 + i % 3])


random.seed(3)
DEMO_ROCKS = [make_rock(0, 0, 1 + i % 3, 1)[5] for i in range(5)]
random.seed(time.ticks_ms())


def main():
    lcd, keys = init()
    while True:
        if not title(lcd, keys, "METEORER", CYAN,
                     ("Sprang stenarna innan", "de krossar ditt skepp!", "",
                      "Stora stenar spricker i mindre.", "Akta dig for UFO:n."),
                     "meteor", ("svang", "svang", "gasa", "skjut"), demo):
            back()
        while True:
            gc.collect()
            score = play(lcd, keys)
            if score is None:
                break
            if not result(lcd, keys, "GAME OVER", str(score), "meteor", score, CYAN):
                back()


main()
''',
    'ny_turbo.py': r'''# TURBO - racingspel i 3D för Pico Arcade
#
#   KEY0 (uppe vänster)  = styr vänster
#   KEY1 (uppe höger)    = styr höger
#   KEY2 (nere höger)    = gasa
#   KEY3 (nere vänster)  = bromsa
#   alla fyra            = paus
#
# Kör så långt du kan innan tiden tar slut. Varje kontrollpunkt ger mer tid.
# Uppackad från nyaspel.py, ändra i nyaspel.py i stället.

from ny_lib import *
from array import array

SEG_L = 200                  # längd på en vägbit
ROAD_W = 2000                # halva vägens bredd
RUMBLE = 3                   # vägbitar per färgrand
DRAW = 70                    # så många bitar framåt ritas
CAM_H = 1000.0
CAM_D = 0.84                 # 1/tan(fov/2), fov ca 100 grader
PLAYER_Z = CAM_H * CAM_D
MAX_SPEED = 140.0            # enheter per bild
ACCEL = MAX_SPEED / 80
BRAKE = -MAX_SPEED / 25
DECEL = -MAX_SPEED / 160
OFF_DECEL = -MAX_SPEED / 45
OFF_LIMIT = MAX_SPEED / 4
CENTRIFUGAL = 0.32
CHECK_EVERY = 260            # vägbitar mellan kontrollpunkter
HX, HY = W // 2, H // 2

FOG = (150, 175, 220)
NFOG = 8


def fogc(c, f):
    return mix(c, FOG, f)


# Färger per dimnivå: (gräs, kant, väg, linje) för ljus och mörk rand
PAL = []
for lv in range(NFOG):
    f = (lv / (NFOG - 1)) ** 1.6 * 0.85
    PAL.append(((fogc((40, 170, 50), f), fogc((255, 255, 255), f), fogc((110, 110, 118), f), fogc((255, 255, 255), f)),
                (fogc((30, 145, 40), f), fogc((220, 40, 40), f), fogc((100, 100, 108), f), 0)))
SKY = [mix((40, 110, 230), FOG, y / HY) for y in range(HY + 20)]


# ---------------------------------------------------------------
# Banan
# ---------------------------------------------------------------
def ease_in(a, b, p):
    return a + (b - a) * p * p


def ease_io(a, b, p):
    return a + (b - a) * ((-math.cos(p * math.pi) / 2) + 0.5)


def build_track():
    random.seed(2026)
    curves = []
    ys = []

    def add(enter, hold, leave, curve, height):
        start_y = ys[-1] if ys else 0.0
        end_y = start_y + height * SEG_L
        total = enter + hold + leave
        n = 0
        for i in range(enter):
            curves.append(ease_in(0, curve, i / enter))
            ys.append(ease_io(start_y, end_y, n / total))
            n += 1
        for i in range(hold):
            curves.append(curve)
            ys.append(ease_io(start_y, end_y, n / total))
            n += 1
        for i in range(leave):
            curves.append(ease_io(curve, 0, i / leave))
            ys.append(ease_io(start_y, end_y, n / total))
            n += 1

    add(10, 40, 10, 0, 0)
    pieces = 0
    while len(curves) < 1500:
        kind = random.randint(0, 5)
        L = random.choice((15, 25, 40))
        c = random.choice((2, 3, 4, 6)) * random.choice((-1, 1))
        hgt = random.choice((-40, -20, 0, 0, 20, 40))
        if kind == 0:
            add(L, L, L, 0, hgt)
        elif kind <= 2:
            add(L, L, L, c, hgt)
        elif kind == 3:                                   # S-kurva
            add(L, L, L, c, hgt // 2)
            add(L, L, L, -c, -hgt // 2)
        elif kind == 4:                                   # backar
            add(L // 2, L // 2, L // 2, 0, 30)
            add(L // 2, L // 2, L // 2, 0, -30)
        else:
            add(L, L * 2, L, c // 2, 0)
        pieces += 1
    add(20, 20, 20, 0, -(ys[-1] / SEG_L))                 # tillbaka till samma höjd
    n = len(curves)
    sprites = {}
    for i in range(20, n, 1):
        if i % 6 == 0:
            side = random.choice((-1, 1))
            sprites[i] = [(random.choice((0, 0, 1, 2)), side * random.uniform(1.35, 2.6))]
            if random.random() < 0.5:
                sprites[i].append((0, -side * random.uniform(1.35, 2.4)))
        if i % CHECK_EVERY == 0:
            sprites[i] = [(3, -1.25), (3, 1.25)]
    return array('f', curves), array('f', ys), sprites


# ---------------------------------------------------------------
# Ritning
# ---------------------------------------------------------------
MTN = [int(30 + 18 * math.sin(i * 0.02) + 10 * math.sin(i * 0.057 + 2) + 6 * math.sin(i * 0.13)) for i in range(640)]
HILLC = [int(14 + 8 * math.sin(i * 0.05 + 1) + 4 * math.sin(i * 0.17)) for i in range(640)]


def sky_bg(lcd):
    for y in range(len(SKY)):
        lcd.hline(0, y, W, SKY[y])
    lcd.ellipse(240, 40, 18, 18, rgb(255, 245, 190), True)


@native
def draw_back(fb, off):
    o = int(off) % 640
    c1 = rgb(120, 130, 200)
    c2 = rgb(70, 140, 90)
    for x in range(0, W, 2):
        h = MTN[(x + o) % 640]
        fb.fill_rect(x, HY - h, 2, h + 20, c1)
        h2 = HILLC[(x + o * 2) % 640]
        fb.fill_rect(x, HY - h2 + 6, 2, h2 + 20, c2)


@native
def draw_road(fb, curves, ys, n_seg, position, player_x, player_y, proj, base):
    """Ritar vägen och sparar varje bits position för sprites och bilar."""
    base_off = position - base * SEG_L
    base_pct = base_off / SEG_L
    camx = player_x * ROAD_W
    camy = player_y + CAM_H
    x = 0.0
    dx = -curves[base] * base_pct
    maxy = H
    for n in range(DRAW):
        i = (base + n) % n_seg
        z1 = n * SEG_L - base_off            # avstånd från kameran
        z2 = z1 + SEG_L
        j = (i + 1) % n_seg
        proj[n * 4 + 3] = maxy
        if z1 <= 1.0:
            x += dx
            dx += curves[i]
            proj[n * 4] = -1.0
            continue
        s1 = CAM_D / z1
        s2 = CAM_D / z2
        X1 = HX + s1 * (x - camx) * HX
        Y1 = HY - s1 * (ys[i] - camy) * HY
        W1 = s1 * ROAD_W * HX
        X2 = HX + s2 * (x + dx - camx) * HX
        Y2 = HY - s2 * (ys[j] - camy) * HY
        W2 = s2 * ROAD_W * HX
        proj[n * 4] = s1
        proj[n * 4 + 1] = X1
        proj[n * 4 + 2] = Y1
        x += dx
        dx += curves[i]
        if Y2 >= Y1 or Y2 >= maxy:
            continue
        lv = n * NFOG // DRAW
        cols = PAL[lv][(i // RUMBLE) % 2]
        grass = cols[0]
        rumble = cols[1]
        road = cols[2]
        lane = cols[3]
        ya = int(Y2)
        if ya < 0:
            ya = 0
        yb = int(Y1)
        if yb > maxy:
            yb = int(maxy)
        dy = Y1 - Y2
        for y in range(ya, yb):
            p = (y - Y2) / dy
            cx = X2 + (X1 - X2) * p
            w = W2 + (W1 - W2) * p
            rw = w / 6
            fb.hline(0, y, W, grass)
            fb.hline(int(cx - w - rw), y, int(2 * (w + rw)), rumble)
            fb.hline(int(cx - w), y, int(2 * w), road)
            if lane:
                lw = w / 32 + 1
                fb.hline(int(cx - w / 3 - lw / 2), y, int(lw), lane)
                fb.hline(int(cx + w / 3 - lw / 2), y, int(lw), lane)
        if Y2 < maxy:
            maxy = Y2


def draw_sprite(fb, kind, x, y, s, t):
    """x, y = mitten nertill. s = skala (pixlar per 'enhet')."""
    if kind == 0:                                # palm
        h = int(s * 2600)
        w = max(1, int(s * 220))
        fb.fill_rect(int(x - w / 2), y - h, w, h, rgb(120, 80, 40))
        r = int(s * 900)
        if r >= 2:
            fb.ellipse(int(x), y - h, r, max(1, r // 2), rgb(30, 130, 50), True)
            fb.ellipse(int(x - r * 0.6), y - h + r // 3, r // 2 + 1, max(1, r // 4), rgb(40, 160, 60), True)
            fb.ellipse(int(x + r * 0.6), y - h + r // 3, r // 2 + 1, max(1, r // 4), rgb(40, 160, 60), True)
    elif kind == 1:                              # buske
        r = int(s * 700)
        if r >= 1:
            fb.ellipse(int(x), y - r // 2, r, max(1, r // 2), rgb(50, 120, 40), True)
    elif kind == 2:                              # skylt
        h = int(s * 1500)
        w = int(s * 1400)
        fb.fill_rect(int(x - s * 60), y - h, max(1, int(s * 120)), h, GRAY)
        fb.fill_rect(int(x - w / 2), y - h - int(w * 0.5), w, int(w * 0.5) + 1, YELLOW)
        if w > 16:
            fb.fill_rect(int(x - w / 4), y - h - int(w * 0.35), w // 2, max(1, int(w * 0.12)), BLACK)
    elif kind == 3:                              # kontrollpunkt-stolpe
        h = int(s * 3000)
        w = max(1, int(s * 200))
        fb.fill_rect(int(x - w / 2), y - h, w, h, WHITE if (t // 4) % 2 else YELLOW)


def draw_car(fb, x, y, s, col, braking=False):
    """Bil bakifrån. s = skala."""
    w = int(s * 1200)
    if w < 3:
        return
    h = int(w * 0.55)
    x = int(x)
    fb.fill_rect(x - w // 2, y - h, w, h, col)
    fb.fill_rect(x - w // 2 + w // 6, y - h - h // 2, w - w // 3, h // 2 + 1, col)
    fb.fill_rect(x - w // 2 + w // 5, y - h - h // 3, w - 2 * (w // 5), max(1, h // 4), rgb(40, 50, 70))
    lc = rgb(255, 60, 60) if braking else rgb(170, 20, 20)
    fb.fill_rect(x - w // 2 + 1, y - h + h // 4, max(1, w // 6), max(1, h // 5), lc)
    fb.fill_rect(x + w // 2 - 1 - max(1, w // 6), y - h + h // 4, max(1, w // 6), max(1, h // 5), lc)
    fb.fill_rect(x - w // 2, y - max(1, h // 4), max(1, w // 5), max(1, h // 4), BLACK)
    fb.fill_rect(x + w // 2 - max(1, w // 5), y - max(1, h // 4), max(1, w // 5), max(1, h // 4), BLACK)


def draw_player(fb, steer, bump, braking):
    x = HX
    y = 226 + bump
    col = rgb(230, 30, 40)
    dark = rgb(150, 15, 25)
    # Skugga och däck
    fb.fill_rect(x - 38, y - 4, 76, 6, rgb(20, 40, 20))
    fb.fill_rect(x - 36, y - 16, 12, 16, BLACK)
    fb.fill_rect(x + 24, y - 16, 12, 16, BLACK)
    # Kaross, lutar lite när man svänger
    sh = steer * 3
    fb.fill_rect(x - 34, y - 24, 68, 16, col)
    fb.fill_rect(x - 30 + sh, y - 38, 60, 15, col)
    fb.fill_rect(x - 24 + sh, y - 36, 48, 9, rgb(40, 50, 80))
    fb.fill_rect(x - 22 + sh, y - 35, 14, 3, rgb(120, 140, 180))
    fb.fill_rect(x - 34, y - 12, 68, 4, dark)
    lc = rgb(255, 80, 80) if braking else rgb(180, 30, 30)
    fb.fill_rect(x - 32, y - 21, 12, 5, lc)
    fb.fill_rect(x + 20, y - 21, 12, 5, lc)
    fb.fill_rect(x - 8, y - 20, 16, 6, rgb(240, 240, 200))       # nummerplåt
    fb.fill_rect(x - 36 + sh, y - 42, 72, 4, dark)               # spoiler


# ---------------------------------------------------------------
# Spelet
# ---------------------------------------------------------------
CAR_COLS = (rgb(40, 110, 255), rgb(255, 200, 30), rgb(240, 240, 240), rgb(60, 200, 90), rgb(255, 120, 30))


def play(lcd, keys, track):
    curves, ys, sprites = track
    n_seg = len(curves)
    track_len = n_seg * SEG_L
    proj = array('f', [0.0] * (DRAW * 4))
    position = 0.0
    speed = 0.0
    player_x = 0.0
    sky_off = 0.0
    time_left = 45.0 * 30                   # i bilder
    dist = 0.0
    next_check = CHECK_EVERY
    banner, banner_txt = 0, ""
    overtakes = 0
    shake = Shake()
    pops = Popups()
    cars = []
    for k in range(14):
        cars.append([random.uniform(10, n_seg) * SEG_L, random.uniform(-0.75, 0.75),
                     random.uniform(MAX_SPEED * 0.3, MAX_SPEED * 0.6), CAR_COLS[k % len(CAR_COLS)], False])
    countdown = 90
    t = 0
    lcd.set_bg(sky_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.menu():
            if pause(lcd, keys):
                return None
            lcd.set_bg(sky_bg)
        base = int(position // SEG_L) % n_seg
        player_seg = int((position + PLAYER_Z) // SEG_L) % n_seg
        pct = ((position + PLAYER_Z) % SEG_L) / SEG_L
        player_y = ys[player_seg] + (ys[(player_seg + 1) % n_seg] - ys[player_seg]) * pct
        spd_pct = speed / MAX_SPEED
        steer = 0
        braking = False
        if countdown > 0:
            countdown -= 1
        else:
            time_left -= 1
            dxs = 0.065 * spd_pct + 0.01 * (speed > 1)
            if keys.held(K0):
                player_x -= dxs
                steer = -1
            if keys.held(K1):
                player_x += dxs
                steer = 1
            player_x -= dxs * spd_pct * curves[player_seg] * CENTRIFUGAL
            if keys.held(K2):
                speed += ACCEL
            elif keys.held(K3):
                speed += BRAKE
                braking = True
            else:
                speed += DECEL
            if keys.held(K3):
                braking = True
            off = player_x < -1 or player_x > 1
            if off and speed > OFF_LIMIT:
                speed += OFF_DECEL
                shake.hit(1.5)
            speed = max(0.0, min(MAX_SPEED, speed))
            player_x = max(-2.5, min(2.5, player_x))
        position = (position + speed) % track_len
        dist += speed
        sky_off += curves[base] * spd_pct * 2

        # Trafik
        for c in cars:
            c[0] = (c[0] + c[2]) % track_len
            rel = (c[0] - position) % track_len
            if not c[4] and rel < PLAYER_Z - 50 and rel > PLAYER_Z - 400:
                c[4] = True                          # vi körde om
                overtakes += 1
                pops.add(HX, 160, "OMKORNING +100", CYAN)
            if rel > PLAYER_Z + SEG_L * 3:
                c[4] = False
            if abs(rel - PLAYER_Z) < SEG_L * 0.7 and abs(c[1] - player_x) < 0.55 and speed > c[2]:
                speed = c[2] * 0.6
                shake.hit(7)
                pops.add(HX, 140, "KRASCH!", RED)

        # Kontrollpunkt
        seg_abs = int(dist // SEG_L)
        if seg_abs >= next_check:
            next_check += CHECK_EVERY
            time_left += 25 * 30
            banner, banner_txt = 60, "KONTROLLPUNKT +25"
        if time_left <= 0:
            score = int(dist / 100) + overtakes * 100
            return score

        # --- Rita ---
        ox, oy = shake.offset()
        lcd.load_bg()
        draw_back(lcd, sky_off * 10)
        draw_road(lcd, curves, ys, n_seg, position, player_x, player_y, proj, base)
        # Sprites och bilar bakifrån och fram
        car_at = {}
        for c in cars:
            rel = (c[0] - position) % track_len
            k = int(rel // SEG_L)
            if 1 <= k < DRAW:
                car_at.setdefault(k, []).append(c)
        for n in range(DRAW - 1, 0, -1):
            s = proj[n * 4]
            if s <= 0:
                continue
            X, Y, clip = proj[n * 4 + 1], proj[n * 4 + 2], proj[n * 4 + 3]
            if Y > clip + 2:
                continue
            sc = s * HX
            i = (base + n) % n_seg
            sp = sprites.get(i)
            if sp:
                for kind, offs in sp:
                    draw_sprite(lcd, kind, X + sc * offs * ROAD_W, int(Y), sc, t)
            cl = car_at.get(n)
            if cl:
                for c in cl:
                    draw_car(lcd, X + sc * c[1] * ROAD_W, int(Y), sc, c[3])
        bump = (t % 2) * 2 if (player_x < -1 or player_x > 1) and speed > 5 else 0
        draw_player(lcd, steer, bump + oy, braking)

        # Instrument
        secs = int(time_left // 30)
        tc = RED if secs < 10 and (t // 6) % 2 else WHITE
        lcd.fill_rect(0, 0, W, 22, rgb(10, 10, 30))
        lcd.text("TID", 6, 7, GRAY)
        big_text(lcd, "%02d" % max(0, secs), 34, 3, tc, 2)
        lcd.text("%d m" % int(dist / 100), 90, 7, WHITE)
        kmh = int(spd_pct * 260)
        big_text(lcd, "%3d" % kmh, 228, 3, YELLOW, 2)
        lcd.text("km/h", 280, 9, GRAY)
        lcd.fill_rect(160, 8, 56, 6, DIM)
        lcd.fill_rect(160, 8, int(56 * spd_pct), 6, ORANGE if spd_pct < 0.9 else RED)
        prog = 1 - (next_check - dist / SEG_L) / CHECK_EVERY
        lcd.hline(6, 24, W - 12, DIM)
        lcd.fill_rect(6 + int((W - 12) * max(0, min(1, prog))) - 2, 23, 4, 3, YELLOW)
        pops.draw(lcd)
        if countdown > 0:
            stext(lcd, str(countdown // 30 + 1), 80, YELLOW, 5)
        elif t < 110:
            stext(lcd, "GO!", 80, GREEN, 5)
        elif banner > 0:
            banner -= 1
            stext(lcd, banner_txt, 70, YELLOW, 2)
        lcd.show()
        t += 1
        frame_wait(t0)


def demo(lcd, t):
    # Liten väg i perspektiv nertill på titelskärmen
    for i in range(48):
        y = 192 + i
        if y >= H:
            break
        z = 60.0 / (i + 1)
        w = int(160 / z) + 6
        cx = HX + int(math.sin(t * 0.03 + z * 0.3) * 20 / z * 3)
        s = int(z * 1.5 + t * 0.4) & 1
        lcd.hline(0, y, W, rgb(40, 170, 50) if s else rgb(30, 145, 40))
        lcd.hline(cx - w, y, 2 * w, rgb(110, 110, 118))


def main():
    lcd, keys = init()
    track = build_track()
    random.seed(time.ticks_ms())
    while True:
        if not title(lcd, keys, "TURBO", ORANGE,
                     ("Kor sa langt du kan", "innan tiden tar slut!", "",
                      "Kontrollpunkter ger +25 s.", "Omkorningar ger extrapoang."),
                     "turbo", ("vanster", "hoger", "broms", "gasa"), demo):
            back()
        while True:
            gc.collect()
            score = play(lcd, keys, track)
            if score is None:
                break
            if not result(lcd, keys, "TIDEN SLUT!", str(score), "turbo", score, ORANGE):
                back()


main()
''',
    'ny_bubblor.py': r'''# BUBBLOR - bubbelskjutare för Pico Arcade
#
#   KEY0 (uppe vänster)  = sikta åt vänster (håll inne)
#   KEY1 (uppe höger)    = sikta åt höger (håll inne)
#   KEY2 (nere höger)    = skjut
#   KEY3 (nere vänster)  = byt till nästa bubbla
#   alla fyra            = paus
#
# Få tre eller fler i samma färg att sitta ihop så spricker de. Bubblor
# som inte längre hänger fast i taket ramlar ner och ger extra poäng.
# Uppackad från nyaspel.py, ändra i nyaspel.py i stället.

from ny_lib import *

R = 10
D = 20
COLS = 9
ROWS = 13
RH = 17
X0 = 70
FIELD_W = COLS * D
SHOOT_X, SHOOT_Y = X0 + FIELD_W // 2, 224
LOSE_Y = 204
SPEED = 7.5

BCOL = ((255, 70, 80), (255, 210, 50), (70, 220, 100), (60, 140, 255), (190, 90, 255), (40, 230, 230))
B_MAIN = [rgb(*c) for c in BCOL]
B_DARK = [mix(c, (0, 0, 0), 0.45) for c in BCOL]
B_LIGHT = [mix(c, (255, 255, 255), 0.55) for c in BCOL]
FIELD_BG = rgb(14, 12, 34)


def draw_bubble(fb, x, y, ci, r=R):
    fb.ellipse(x, y, r, r, B_DARK[ci], True)
    fb.ellipse(x, y, r - 2, r - 2, B_MAIN[ci], True)
    if r >= 6:
        fb.ellipse(x - r // 3, y - r // 3, r // 3, r // 4 + 1, B_LIGHT[ci], True)
        fb.pixel(x - r // 3 - 1, y - r // 3 - 1, WHITE)


def ncols(row):
    return COLS if row % 2 == 0 else COLS - 1


def cell_xy(row, col, y0):
    return X0 + R + col * D + (R if row % 2 else 0), y0 + R + row * RH


def neighbors(row, col):
    if row % 2 == 0:
        cand = ((row, col - 1), (row, col + 1), (row - 1, col - 1), (row - 1, col),
                (row + 1, col - 1), (row + 1, col))
    else:
        cand = ((row, col - 1), (row, col + 1), (row - 1, col), (row - 1, col + 1),
                (row + 1, col), (row + 1, col + 1))
    return [(r, c) for r, c in cand if 0 <= r < ROWS and 0 <= c < ncols(r)]


def field_bg(lcd):
    draw_gradient(lcd)
    for i in range(30):                                    # svaga prickar
        lcd.pixel((i * 97) % W, (i * 53) % H, DIM)
    lcd.fill_rect(X0 - 4, 0, FIELD_W + 8, H, rgb(60, 50, 120))
    lcd.fill_rect(X0, 0, FIELD_W, H, FIELD_BG)
    for y in range(LOSE_Y, LOSE_Y + 1):
        for x in range(X0, X0 + FIELD_W, 6):
            lcd.hline(x, y, 3, rgb(120, 40, 60))
    lcd.text("POANG", 8, 10, GRAY)
    lcd.text("NIVA", 8, 60, GRAY)
    lcd.text("NASTA", W - 60, 10, GRAY)
    lcd.text("TAKET", W - 60, 90, GRAY)


class Game:
    def __init__(self, level, score):
        self.level = level
        self.score = score
        self.grid = [bytearray(COLS) for _ in range(ROWS)]
        self.n_colors = min(3 + level // 2, 6)
        rows = min(4 + level, 8)
        for r in range(rows):
            for c in range(ncols(r)):
                self.grid[r][c] = random.randint(1, self.n_colors)
        self.drop = 0                       # hur många rader taket har sänkts
        self.shots = 0
        self.shots_per_drop = max(5, 9 - level // 2)
        self.cur = self.pick()
        self.nxt = self.pick()

    def y0(self):
        return 6 + self.drop * RH

    def present(self):
        s = []
        for row in self.grid:
            for v in row:
                if v and v not in s:
                    s.append(v)
        return s

    def pick(self):
        p = self.present() if hasattr(self, "grid") else []
        return (random.choice(p) if p else random.randint(1, self.n_colors)) - 1

    def empty(self):
        for row in self.grid:
            for v in row:
                if v:
                    return False
        return True

    def hits(self, x, y):
        """Krockar en bubbla på (x, y) med något?"""
        y0 = self.y0()
        if y - R <= y0:
            return True
        row = int((y - y0 - R) / RH + 0.5)
        for r in range(row - 1, row + 2):
            if 0 <= r < ROWS:
                for c in range(ncols(r)):
                    if self.grid[r][c]:
                        cx, cy = cell_xy(r, c, y0)
                        if (cx - x) ** 2 + (cy - y) ** 2 < (D - 3) ** 2:
                            return True
        return False

    def snap(self, x, y):
        """Hitta närmaste tomma ruta för en bubbla som har stannat."""
        y0 = self.y0()
        best, bd = None, 1e9
        row = int((y - y0 - R) / RH + 0.5)
        for r in range(max(0, row - 1), min(ROWS, row + 2)):
            for c in range(ncols(r)):
                if not self.grid[r][c]:
                    cx, cy = cell_xy(r, c, y0)
                    d = (cx - x) ** 2 + (cy - y) ** 2
                    if d < bd:
                        best, bd = (r, c), d
        return best

    def flood(self, start, same_color):
        r0, c0 = start
        col = self.grid[r0][c0]
        seen = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for n in neighbors(r, c):
                if n not in seen and self.grid[n[0]][n[1]] and \
                        (not same_color or self.grid[n[0]][n[1]] == col):
                    seen.add(n)
                    stack.append(n)
        return seen

    def floating(self):
        attached = set()
        for c in range(ncols(0)):
            if self.grid[0][c] and (0, c) not in attached:
                attached.update(self.flood((0, c), False))
        out = []
        for r in range(ROWS):
            for c in range(ncols(r)):
                if self.grid[r][c] and (r, c) not in attached:
                    out.append((r, c))
        return out

    def lost(self):
        y0 = self.y0()
        for r in range(ROWS):
            for c in range(ncols(r)):
                if self.grid[r][c] and cell_xy(r, c, y0)[1] + R > LOSE_Y:
                    return True
        return False


def trace(g, ang):
    """Siktlinje: punkter längs bubblans väg (med studs mot väggarna)."""
    x, y = float(SHOOT_X), float(SHOOT_Y)
    vx, vy = math.sin(ang) * 6, -math.cos(ang) * 6
    pts = []
    for i in range(70):
        x += vx
        y += vy
        if x < X0 + R:
            x = 2 * (X0 + R) - x
            vx = -vx
        elif x > X0 + FIELD_W - R:
            x = 2 * (X0 + FIELD_W - R) - x
            vx = -vx
        if g.hits(x, y):
            break
        if i % 2 == 0:
            pts.append((int(x), int(y)))
    return pts


def play(lcd, keys):
    level, score = 1, 0
    g = Game(level, score)
    ang = 0.0
    turn = 0.0
    shot = None                      # [x, y, vx, vy, färg]
    falling = []                     # [x, y, vy, färg]
    parts = Particles(120)
    pops = Popups()
    shake = Shake()
    banner = 50
    t = 0
    lcd.set_bg(field_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.menu():
            if pause(lcd, keys):
                return None
            lcd.set_bg(field_bg)
        # Sikta (snabbare ju längre man håller)
        if keys.held(K0) or keys.held(K1):
            turn = min(0.06, turn + 0.006)
            ang += -turn if keys.held(K0) else turn
        else:
            turn = 0.012
        ang = max(-1.35, min(1.35, ang))
        if keys.pressed(K3) and shot is None:
            g.cur, g.nxt = g.nxt, g.cur
        if keys.pressed(K2) and shot is None and banner == 0:
            shot = [float(SHOOT_X), float(SHOOT_Y), math.sin(ang) * SPEED, -math.cos(ang) * SPEED, g.cur]
            g.cur = g.nxt
            g.nxt = g.pick()

        if shot:
            for _ in range(2):                       # två delsteg per bild
                shot[0] += shot[2] / 2
                shot[1] += shot[3] / 2
                if shot[0] < X0 + R:
                    shot[0] = 2 * (X0 + R) - shot[0]
                    shot[2] = -shot[2]
                elif shot[0] > X0 + FIELD_W - R:
                    shot[0] = 2 * (X0 + FIELD_W - R) - shot[0]
                    shot[2] = -shot[2]
                if g.hits(shot[0], shot[1]):
                    cell = g.snap(shot[0], shot[1])
                    ci = shot[4]
                    shot = None
                    if cell is None:
                        break
                    g.grid[cell[0]][cell[1]] = ci + 1
                    group = g.flood(cell, True)
                    if len(group) >= 3:
                        y0 = g.y0()
                        for r, c in group:
                            x, y = cell_xy(r, c, y0)
                            parts.burst(x, y, B_MAIN[ci], 6, 2.5, 14)
                            g.grid[r][c] = 0
                        gain = len(group) * 10
                        drops = g.floating()
                        for r, c in drops:
                            x, y = cell_xy(r, c, y0)
                            falling.append([x, y, random.uniform(-2.5, -0.5), g.grid[r][c] - 1,
                                            random.uniform(-1.2, 1.2)])
                            g.grid[r][c] = 0
                        gain += len(drops) * 30 * (1 + len(drops) // 4)
                        g.score += gain
                        cx, cy = cell_xy(cell[0], cell[1], y0)
                        pops.add(cx, cy - 8, "+%d" % gain, YELLOW if not drops else CYAN)
                        shake.hit(2 + len(drops) * 0.6)
                    else:
                        g.shots += 1
                        if g.shots >= g.shots_per_drop:
                            g.shots = 0
                            g.drop += 1
                            shake.hit(5)
                    break
            if g.empty():
                bonus = 500 + g.level * 200
                g.score += bonus
                level_banner(lcd, keys, g.level, bonus)
                g = Game(g.level + 1, g.score)
                falling = []
                banner = 40
                lcd.set_bg(field_bg)
            elif shot is None and g.lost():
                return g.score

        for f in falling:
            f[2] += 0.45
            f[1] += f[2]
            f[0] += f[4]
        falling = [f for f in falling if f[1] < H + 12]

        # --- Rita ---
        ox, oy = shake.offset()
        lcd.load_bg()
        y0 = g.y0()
        if g.drop:
            lcd.fill_rect(X0, 0, FIELD_W, y0, rgb(60, 50, 120))
            for i in range(g.drop):
                lcd.hline(X0, 6 + i * RH + RH - 1, FIELD_W, rgb(90, 80, 160))
        for r in range(ROWS):
            row = g.grid[r]
            for c in range(ncols(r)):
                v = row[c]
                if v:
                    x, y = cell_xy(r, c, y0)
                    draw_bubble(lcd, x + ox, y + oy, v - 1)
        # Siktlinje
        if shot is None:
            for i, (x, y) in enumerate(trace(g, ang)):
                if (i + t // 3) % 2 == 0:
                    lcd.fill_rect(x - 1, y - 1, 2, 2, B_LIGHT[g.cur])
        # Kanon
        ca, sa = math.sin(ang), -math.cos(ang)
        for k in (-1, 0, 1):
            lcd.line(SHOOT_X + k, SHOOT_Y, int(SHOOT_X + ca * 26) + k, int(SHOOT_Y + sa * 26), GRAY)
        lcd.ellipse(SHOOT_X, SHOOT_Y + 8, 18, 10, rgb(60, 50, 120), True)
        if shot is None:
            draw_bubble(lcd, SHOOT_X, SHOOT_Y, g.cur)
        else:
            draw_bubble(lcd, int(shot[0]), int(shot[1]), shot[4])
        for f in falling:
            draw_bubble(lcd, int(f[0]), int(f[1]), f[3])
        parts.draw(lcd, ox, oy)
        pops.draw(lcd, ox, oy)
        # Sidopaneler
        big_text(lcd, str(g.score), 8, 24, WHITE, 2 if g.score < 10000 else 1)
        big_text(lcd, str(g.level), 8, 74, YELLOW, 3)
        draw_bubble(lcd, W - 34, 44, g.nxt, 12)
        lcd.text("3 byt", W - 56, 64, DIM)
        for i in range(g.shots_per_drop):
            c = RED if i < g.shots else DIM
            lcd.fill_rect(W - 60 + (i % 5) * 10, 104 + (i // 5) * 10, 7, 7, c)
        if banner > 0:
            banner -= 1
            stext(lcd, "NIVA %d" % g.level, 100, WHITE, 3)
        lcd.show()
        t += 1
        frame_wait(t0)


def level_banner(lcd, keys, level, bonus):
    for t in range(60):
        t0 = time.ticks_ms()
        lcd.fill_rect(X0, 80, FIELD_W, 70, BG)
        lcd.rect(X0, 80, FIELD_W, 70, YELLOW)
        stext(lcd, "RENSAT!", 92, GREEN, 3, cx=X0 + FIELD_W // 2)
        ctext(lcd, "Bonus +%d" % bonus, 128, YELLOW, 1, cx=X0 + FIELD_W // 2)
        lcd.show()
        frame_wait(t0)


def demo(lcd, t):
    for i in range(14):
        x = (i * 47 + int(t * (0.5 + (i % 3) * 0.3))) % (W + 40) - 20
        y = 60 + int(40 * math.sin(t * 0.03 + i)) + (i * 31) % 90
        draw_bubble(lcd, x, y, i % 6, 7 + i % 4)


def main():
    lcd, keys = init()
    while True:
        if not title(lcd, keys, "BUBBLOR", MAGENTA,
                     ("Fa tre i samma farg att", "sitta ihop sa spricker de!", "",
                      "Losa bubblor ramlar = extrapoang.", "Taket sanks efter nagra skott."),
                     "bubblor", ("sikta", "sikta", "byt", "skjut"), demo):
            back()
        while True:
            gc.collect()
            score = play(lcd, keys)
            if score is None:
                break
            if not result(lcd, keys, "GAME OVER", str(score), "bubblor", score, MAGENTA):
                back()


main()
''',
    'ny_minigolf.py': r'''# MINIGOLF - 9 hål för Pico Arcade
#
#   KEY0 (uppe vänster)  = sikta åt vänster (håll inne)
#   KEY1 (uppe höger)    = sikta åt höger (håll inne)
#   KEY3 (nere vänster)  = håll inne för att sikta långsamt och noga
#   KEY2 (nere höger)    = håll inne för att ladda, släpp för att slå
#   alla fyra            = paus
#
# Sand bromsar, vatten ger ett straffslag och pilarna visar sluttningar.
# Försök klara alla hål på så få slag som möjligt.
# Uppackad från nyaspel.py, ändra i nyaspel.py i stället.

from ny_lib import *

TS = 4                         # rutstorlek i pixlar
GW, GH = W // TS, H // TS
WALL, GRASS, SAND, WATER, SL_N, SL_E, SL_S, SL_W = range(8)
SLOPE_DIR = {SL_N: (0, -1), SL_E: (1, 0), SL_S: (0, 1), SL_W: (-1, 0)}
BALL_R = 3
CUP_R = 5
BLADE = 20                     # väderkvarnens vinglängd
TOP = 16                       # överst finns poängraden

# Varje hål: namn, par, utslag, hål, ytor [(typ, x, y, b, h)], väderkvarnar [(x, y)]
HOLES = (
    ("Rakt fram", 2, (60, 120), (262, 120),
     [(GRASS, 40, 100, 240, 40)], []),
    ("Kroken", 2, (60, 172), (222, 58),
     [(GRASS, 40, 152, 200, 40), (GRASS, 200, 40, 40, 152)], []),
    ("Sandfallan", 3, (50, 120), (272, 120),
     [(GRASS, 28, 60, 264, 120), (SAND, 128, 72, 64, 96), (WALL, 152, 104, 16, 32)], []),
    ("Bron", 3, (50, 68), (264, 68),
     [(GRASS, 28, 40, 264, 164), (WATER, 112, 40, 64, 124), (SAND, 216, 120, 48, 40)], []),
    ("Backen", 2, (60, 120), (262, 120),
     [(GRASS, 40, 92, 240, 56), (SL_W, 120, 92, 84, 56)], []),
    ("Vaderkvarnen", 3, (60, 120), (264, 120),
     [(GRASS, 40, 88, 240, 64)], [(164, 120)]),
    ("Sicksack", 3, (50, 58), (270, 186),
     [(GRASS, 28, 40, 224, 36), (GRASS, 216, 40, 36, 100), (GRASS, 68, 104, 184, 36),
      (GRASS, 68, 104, 36, 100), (GRASS, 68, 168, 224, 36)], []),
    ("Muren", 2, (80, 72), (240, 72),
     [(GRASS, 40, 40, 240, 168), (WALL, 152, 40, 16, 124), (SL_S, 176, 164, 64, 40)], []),
    ("Finalen", 4, (52, 56), (268, 196),
     [(GRASS, 24, 36, 272, 184), (WATER, 116, 84, 76, 56), (SAND, 56, 148, 64, 44),
      (SL_N, 204, 148, 56, 44), (WALL, 24, 120, 60, 12)], [(244, 96)]),
)

C_GRASS = (rgb(60, 175, 70), rgb(52, 160, 62))
C_SAND = (rgb(230, 205, 140), rgb(215, 188, 120))
C_WATER = (rgb(40, 110, 210), rgb(60, 140, 230))
C_SLOPE = (rgb(70, 160, 110), rgb(62, 148, 100))
C_WOOD = rgb(140, 90, 50)
C_WOOD_L = rgb(185, 130, 75)
C_OUT = rgb(18, 40, 30)
C_OUT2 = rgb(22, 48, 36)


def build(hole):
    grid = bytearray(GW * GH)
    for typ, x, y, w, h in hole[4]:
        for gy in range(y // TS, (y + h) // TS):
            for gx in range(x // TS, (x + w) // TS):
                if 0 <= gx < GW and 0 <= gy < GH:
                    grid[gy * GW + gx] = typ
    return grid


def tile(grid, x, y):
    gx, gy = int(x) // TS, int(y) // TS
    if gx < 0 or gy < 0 or gx >= GW or gy >= GH:
        return WALL
    return grid[gy * GW + gx]


def course_bg(grid, hole):
    def bg(lcd):
        for gy in range(GH):
            for gx in range(GW):
                v = grid[gy * GW + gx]
                x, y = gx * TS, gy * TS
                if v == WALL:
                    near = False
                    for oy in (-1, 0, 1):
                        for ox in (-1, 0, 1):
                            nx, ny = gx + ox, gy + oy
                            if 0 <= nx < GW and 0 <= ny < GH and grid[ny * GW + nx] != WALL:
                                near = True
                    if near:
                        lcd.fill_rect(x, y, TS, TS, C_WOOD)
                        lcd.pixel(x + 1, y + 1, C_WOOD_L)
                    else:
                        lcd.fill_rect(x, y, TS, TS, C_OUT if (gx + gy) % 2 else C_OUT2)
                elif v == GRASS:
                    lcd.fill_rect(x, y, TS, TS, C_GRASS[(gx // 3) % 2])
                elif v == SAND:
                    lcd.fill_rect(x, y, TS, TS, C_SAND[(gx * 7 + gy * 3) % 2])
                    if (gx * 5 + gy * 11) % 7 == 0:
                        lcd.pixel(x + 1, y + 2, rgb(190, 160, 100))
                elif v == WATER:
                    lcd.fill_rect(x, y, TS, TS, C_WATER[0])
                    if (gx + gy * 2) % 5 == 0:
                        lcd.hline(x, y + 2, 3, C_WATER[1])
                else:
                    lcd.fill_rect(x, y, TS, TS, C_SLOPE[(gx // 3) % 2])
        # Pilar på sluttningarna
        for gy in range(1, GH, 4):
            for gx in range(1, GW, 4):
                v = grid[gy * GW + gx]
                if v in SLOPE_DIR:
                    dx, dy = SLOPE_DIR[v]
                    cx, cy = gx * TS + 2, gy * TS + 2
                    c = rgb(170, 230, 180)
                    lcd.line(cx - dx * 4, cy - dy * 4, cx + dx * 4, cy + dy * 4, c)
                    lcd.line(cx + dx * 4, cy + dy * 4, cx + dx * 1 - dy * 3, cy + dy * 1 + dx * 3, c)
                    lcd.line(cx + dx * 4, cy + dy * 4, cx + dx * 1 + dy * 3, cy + dy * 1 - dx * 3, c)
        # Hålet och utslagsplatsen
        hx, hy = hole[3]
        lcd.ellipse(hx, hy, CUP_R + 1, CUP_R + 1, rgb(30, 90, 40), True)
        lcd.ellipse(hx, hy, CUP_R, CUP_R, rgb(10, 20, 10), True)
        tx, ty = hole[2]
        lcd.fill_rect(tx - 6, ty - 6, 12, 12, rgb(80, 195, 90))
        lcd.fill_rect(0, 0, W, TOP, rgb(10, 20, 16))
    return bg


def blade_hit(ball, cx, cy, ang):
    """Väderkvarnens vingar: returnerar normal (nx, ny) om bollen träffar."""
    for k in range(4):
        a = ang + k * 1.5708
        ex, ey = cx + math.cos(a) * BLADE, cy + math.sin(a) * BLADE
        # närmaste punkt på vingen
        vx, vy = ex - cx, ey - cy
        px, py = ball[0] - cx, ball[1] - cy
        # Mitten är en tunnel som bollen kan rulla igenom, bara vingarna stoppar
        tt = (px * vx + py * vy) / (vx * vx + vy * vy)
        if tt < 0.4:
            continue
        tt = min(1.0, tt)
        qx, qy = cx + vx * tt, cy + vy * tt
        dx, dy = ball[0] - qx, ball[1] - qy
        d = math.sqrt(dx * dx + dy * dy)
        if d < BALL_R + 2:
            if d < 0.01:
                return (1.0, 0.0), 1.0
            return (dx / d, dy / d), BALL_R + 2 - d
    return None, 0


def draw_mill(fb, cx, cy, ang):
    fb.ellipse(cx, cy + 3, 9, 4, rgb(30, 60, 30), True)
    for k in range(4):
        a = ang + k * 1.5708
        ex, ey = int(cx + math.cos(a) * BLADE), int(cy + math.sin(a) * BLADE)
        for o in (-1, 0, 1):
            fb.line(cx + o, cy, ex + o, ey, WHITE if k % 2 else RED)
    fb.ellipse(cx, cy, 3, 3, rgb(120, 80, 50), True)
    fb.pixel(cx, cy, YELLOW)


def label_for(strokes, par):
    if strokes == 1:
        return "HOLE IN ONE!", YELLOW
    d = strokes - par
    return {-3: ("ALBATROSS!", MAGENTA), -2: ("EAGLE!", MAGENTA), -1: ("BIRDIE!", CYAN),
            0: ("PAR", GREEN), 1: ("BOGEY", ORANGE), 2: ("DUBBELBOGEY", RED)}.get(
        d, ("+%d" % d, RED) if d > 0 else ("SUPER!", MAGENTA))


def play_hole(lcd, keys, n, hole, card):
    name, par, tee, cup, _, mills = hole
    grid = build(hole)
    lcd.set_bg(course_bg(grid, hole))
    ball = [float(tee[0]), float(tee[1]), 0.0, 0.0]
    last = (ball[0], ball[1])
    aim = math.atan2(cup[1] - tee[1], cup[0] - tee[0])
    strokes = 0
    power = 0.0
    pdir = 1
    charging = False
    turn = 0.0
    mill_ang = 0.0
    parts = Particles(60)
    pops = Popups()
    banner = 70
    sink = 0
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.menu():
            if pause(lcd, keys):
                return None
            lcd.set_bg(course_bg(grid, hole))
        moving = abs(ball[2]) > 0.02 or abs(ball[3]) > 0.02
        mill_ang += 0.045
        if not moving and sink == 0 and banner < 40:
            fine = keys.held(K3)
            if keys.held(K0) or keys.held(K1):
                turn = 0.006 if fine else min(0.07, turn + 0.005)
                aim += -turn if keys.held(K0) else turn
            else:
                turn = 0.01
            if keys.held(K2):
                charging = True
                power += 0.022 * pdir
                if power >= 1:
                    power, pdir = 1.0, -1
                elif power <= 0:
                    power, pdir = 0.0, 1
            elif charging:
                charging = False
                sp = 0.4 + power * 7.6
                ball[2], ball[3] = math.cos(aim) * sp, math.sin(aim) * sp
                last = (ball[0], ball[1])
                strokes += 1
                power, pdir = 0.0, 1
        # Fysik i fyra delsteg
        if moving and sink == 0:
            for _ in range(4):
                nx = ball[0] + ball[2] / 4
                if tile(grid, nx + (BALL_R if ball[2] > 0 else -BALL_R), ball[1]) == WALL:
                    ball[2] = -ball[2] * 0.78
                    parts.burst(ball[0], ball[1], C_WOOD_L, 3, 1.2, 8)
                else:
                    ball[0] = nx
                ny = ball[1] + ball[3] / 4
                if tile(grid, ball[0], ny + (BALL_R if ball[3] > 0 else -BALL_R)) == WALL:
                    ball[3] = -ball[3] * 0.78
                    parts.burst(ball[0], ball[1], C_WOOD_L, 3, 1.2, 8)
                else:
                    ball[1] = ny
                for mx, my in mills:
                    nrm, depth = blade_hit(ball, mx, my, mill_ang)
                    if nrm:
                        ball[0] += nrm[0] * depth
                        ball[1] += nrm[1] * depth
                        dot = ball[2] * nrm[0] + ball[3] * nrm[1]
                        if dot < 0:
                            ball[2] -= 1.8 * dot * nrm[0]
                            ball[3] -= 1.8 * dot * nrm[1]
                        ball[2] += -nrm[1] * 0.4
                        ball[3] += nrm[0] * 0.4
            g = tile(grid, ball[0], ball[1])
            fr = 0.93 if g == SAND else 0.982
            ball[2] *= fr
            ball[3] *= fr
            if g in SLOPE_DIR:
                dx, dy = SLOPE_DIR[g]
                ball[2] += dx * 0.09
                ball[3] += dy * 0.09
            sp = math.sqrt(ball[2] ** 2 + ball[3] ** 2)
            if sp < 0.06 and g not in SLOPE_DIR:
                ball[2] = ball[3] = 0.0
            if g == WATER:
                parts.burst(ball[0], ball[1], WHITE, 14, 2, 18)
                pops.add(ball[0], ball[1] - 8, "PLASK! +1", CYAN)
                strokes += 1
                ball[0], ball[1] = last
                ball[2] = ball[3] = 0.0
            # Hålet
            dx, dy = ball[0] - cup[0], ball[1] - cup[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < CUP_R:
                if sp < 4.2:
                    sink = 1
                    ball[2] = ball[3] = 0.0
                else:                                   # för fort, studsar ur
                    ball[2] *= 0.7
                    ball[3] *= 0.7
            elif dist < CUP_R + 6 and sp < 2.5:         # hålet drar lite i bollen
                ball[2] -= dx / dist * 0.08
                ball[3] -= dy / dist * 0.08
        if sink:
            sink += 1
            ball[0] += (cup[0] - ball[0]) * 0.3
            ball[1] += (cup[1] - ball[1]) * 0.3
            if sink == 3:
                parts.burst(cup[0], cup[1], YELLOW, 24, 3, 26)
                parts.burst(cup[0], cup[1], WHITE, 16, 2, 20)
            if sink > 70:
                return strokes
        if strokes >= 8 and not moving and sink == 0:
            pops.add(W / 2, 100, "MAX 8 SLAG", RED)
            card[n] = 8
            for _ in range(30):
                t1 = time.ticks_ms()
                lcd.load_bg()
                pops.draw(lcd)
                lcd.show()
                frame_wait(t1)
            return 8

        # --- Rita ---
        lcd.load_bg()
        for mx, my in mills:
            draw_mill(lcd, mx, my, mill_ang)
        # Flagga
        fx, fy = cup
        lcd.vline(fx, fy - 24, 24, WHITE)
        wav = int(2 * math.sin(t * 0.2))
        lcd.fill_rect(fx + 1, fy - 24 + wav // 2, 12, 7, RED)
        # Sikte och kraft
        if not moving and sink == 0:
            L = 18 + power * 40
            for i in range(1, 9):
                d = L * i / 8
                if (i + t // 3) % 2 == 0:
                    lcd.fill_rect(int(ball[0] + math.cos(aim) * d) - 1,
                                  int(ball[1] + math.sin(aim) * d) - 1, 2, 2, WHITE)
            if charging:
                bw = 100
                lcd.fill_rect(W // 2 - bw // 2 - 2, H - 12, bw + 4, 8, BLACK)
                c = mix((80, 230, 90), (255, 60, 60), power)
                lcd.fill_rect(W // 2 - bw // 2, H - 10, int(bw * power), 4, c)
        if sink == 0 or sink < 8:
            lcd.ellipse(int(ball[0]) + 1, int(ball[1]) + 2, BALL_R, BALL_R - 1, rgb(20, 60, 25), True)
            lcd.ellipse(int(ball[0]), int(ball[1]), BALL_R, BALL_R, WHITE, True)
            lcd.pixel(int(ball[0]) - 1, int(ball[1]) - 1, rgb(220, 220, 220))
        parts.draw(lcd)
        pops.draw(lcd)
        total = sum(card[:n])
        tpar = sum(h[1] for h in HOLES[:n])
        lcd.text("HAL %d/9" % (n + 1), 4, 4, WHITE)
        lcd.text("PAR %d" % par, 84, 4, GRAY)
        lcd.text("SLAG %d" % strokes, 148, 4, YELLOW)
        diff = total - tpar
        lcd.text("TOTALT %s" % (("+%d" % diff) if diff > 0 else ("%d" % diff) if diff else "E"), 228, 4, CYAN)
        if banner > 0:
            banner -= 1
            lcd.fill_rect(40, 92, 240, 50, BG)
            lcd.rect(40, 92, 240, 50, YELLOW)
            ctext(lcd, "HAL %d - %s" % (n + 1, name), 102, WHITE, 1)
            ctext(lcd, "PAR %d" % par, 118, YELLOW, 2)
        if sink > 8:
            txt, col = label_for(strokes, par)
            stext(lcd, txt, 96, col, 3 if len(txt) < 11 else 2)
        lcd.show()
        t += 1
        frame_wait(t0)


def scorecard(lcd, card):
    lcd.fill(BG)
    stext(lcd, "SCOREKORT", 10, YELLOW, 3)
    for i, h in enumerate(HOLES):
        y = 50 + i * 16
        lcd.text("%d %s" % (i + 1, h[0]), 40, y, WHITE)
        lcd.text("par %d" % h[1], 190, y, GRAY)
        s = card[i]
        c = CYAN if s < h[1] else (GREEN if s == h[1] else ORANGE)
        lcd.text(str(s), 260, y, c)
    lcd.show()


def demo(lcd, t):
    # En boll som rullar mot ett hål nertill
    y = 160
    lcd.fill_rect(30, y - 14, 260, 28, C_GRASS[0])
    lcd.rect(28, y - 16, 264, 32, C_WOOD)
    lcd.ellipse(268, y, CUP_R, CUP_R, rgb(10, 20, 10), True)
    lcd.vline(268, y - 22, 22, WHITE)
    lcd.fill_rect(269, y - 22, 10, 6, RED)
    p = (t % 120) / 120
    bx = int(40 + (268 - 40) * (1 - (1 - p) ** 2))
    if p < 0.95:
        lcd.ellipse(bx, y, BALL_R, BALL_R, WHITE, True)


def main():
    lcd, keys = init()
    while True:
        if not title(lcd, keys, "MINIGOLF", GREEN,
                     ("9 hal med sand, vatten,", "backar och vaderkvarnar.", "",
                      "Hall 2 for att ladda slaget,", "slapp for att sla."),
                     "golf", ("sikta", "sikta", "noga", "sla"), demo, "Basta runda: %d slag"):
            back()
        while True:
            gc.collect()
            card = [0] * len(HOLES)
            quit_ = False
            for n, hole in enumerate(HOLES):
                s = play_hole(lcd, keys, n, hole, card)
                if s is None:
                    quit_ = True
                    break
                card[n] = s
            if quit_:
                break
            total = sum(card)
            par = sum(h[1] for h in HOLES)
            scorecard(lcd, card)
            time.sleep_ms(2500)
            diff = total - par
            extra = "Par %d  (%s)" % (par, ("+%d" % diff) if diff > 0 else ("%d" % diff) if diff else "E")
            if not result(lcd, keys, "RUNDAN KLAR", "%d slag" % total, "golf", total, GREEN,
                          lower_is_better=True, extra=extra):
                back()


main()
''',
    'ny_meny.py': r'''# Liten meny för de nya spelen (när nyaspel.py körs direkt).
# Uppackad från nyaspel.py, ändra i nyaspel.py i stället.
from ny_lib import *

GAME_LIST = (("meteor", "METEORER", CYAN), ("turbo", "TURBO", ORANGE),
             ("bubblor", "BUBBLOR", MAGENTA), ("minigolf", "MINIGOLF", GREEN))


def start(name):
    try:
        with open(START_FILE, "w") as f:
            f.write("ny_" + name)
    except Exception:
        pass
    machine.soft_reset()


def main():
    lcd, keys = init()
    sel = 0
    t = 0
    stars = Stars(50)
    lcd.set_bg(draw_gradient)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K0):
            sel = (sel - 1) % len(GAME_LIST)
        if keys.pressed(K1):
            sel = (sel + 1) % len(GAME_LIST)
        if keys.pressed(K2):
            start(GAME_LIST[sel][0])
        if keys.pressed(K3):
            back()
        lcd.load_bg()
        stars.draw(lcd)
        wave(lcd, "NYA SPEL", 20, 4, RAINBOW, t)
        for i, g in enumerate(GAME_LIST):
            y = 80 + i * 32
            if i == sel:
                lcd.fill_rect(60, y - 6, 200, 26, g[2])
                ctext(lcd, g[1], y, BG, 2)
            else:
                ctext(lcd, g[1], y, WHITE, 2)
        ctext(lcd, "0/1 valj   2 spela   3 arcaden", 220, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


main()
''',
}


def unpack():
    """Skriver ut spelfilerna om de saknas eller är av en äldre version."""
    try:
        with open("ny_version.txt") as f:
            if f.read().strip() == VERSION:
                return
    except OSError:
        pass
    print("Packar upp nya spel...")
    for name, src in FILES.items():
        with open(name, "w") as f:
            f.write(src)
        print("  ", name)
    with open("ny_version.txt", "w") as f:
        f.write(VERSION)


def chosen():
    """Vilket spel valdes i arcaden? None = visa menyn."""
    try:
        with open("rekord.json") as f:
            scores = json.load(f)
    except Exception:
        return None
    name = scores.pop("_spel", None)
    if name is not None:
        try:
            with open("rekord.json", "w") as f:
                json.dump(scores, f)
        except Exception:
            pass
    return name


unpack()
_game = chosen()
FILES = None
gc.collect()
with open("starta.txt", "w") as f:
    f.write("ny_" + _game if _game else "ny_meny")
machine.soft_reset()                 # startar main.py, som laddar spelet
