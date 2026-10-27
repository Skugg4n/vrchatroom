# picolib - gemensam grund för spelen i Pico Arcade
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
