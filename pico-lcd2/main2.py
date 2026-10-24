# Pico Arcade
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Liggande spel: Pong, Snake, Breakout, Flappy, Tetris, Dino och Simon.
# Stående spel: Runner, Space och Stack. Plus ett knapptest.
# Håll in alla fyra knapparna samtidigt för att gå ur ett spel.
# Spara som main2.py på Picon. För att den ska starta automatiskt,
# lägg en main.py på Picon med raden: import main2
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö, därför skrivs
# texten på skärmen utan dem.

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
    native = micropython.native      # snabbare maskinkod för tunga loopar
except (ImportError, AttributeError):
    def native(f):
        return f

W, H = 320, 240
VW, VH = 240, 320        # stående läge

# Klockfrekvens. 250 MHz går bra på de flesta Pico 2. Sätt till None
# om Picon beter sig konstigt, då körs den i vanliga 150 MHz.
OVERCLOCK_HZ = 250_000_000
SPI_HZ = 75_000_000

# ---------------------------------------------------------------
# Knappar. Siffran = knappens nummer på kortet (KEY0..KEY3).
#   KEY0 = GP15, KEY1 = GP17, KEY2 = GP2, KEY3 = GP3
# ---------------------------------------------------------------
# De översta knapparna (KEY0 och KEY1) används till det man gör mest:
# styra, flytta och bläddra.
KEY_PINS = (15, 17, 2, 3)
K_X = 0   # vänster / föregående / upp
K_Y = 1   # höger / nästa / ner
K_A = 2   # välj / starta / hoppa / vrid
K_B = 3   # tillbaka / paus

PONG_SOLO = (0, 1)        # 1 spelare: upp, ner
PONG_P1 = (0, 2)          # 2 spelare, spelare 1: upp, ner
PONG_P2 = (1, 3)          # 2 spelare, spelare 2: upp, ner
SNAKE_LEFT, SNAKE_RIGHT = 0, 1

# 2-KNAPPSLÄGE: bara KEY0 och KEY1 används (om KEY2/KEY3 är trasiga).
#   0 / 1             = vänster / höger, föregående / nästa
#   0 + 1 samtidigt   = välj, starta, vrid
#   håll 0 + 1 länge  = gå ur spelet
# Sätt till False när alla fyra knapparna fungerar igen.
TWO_KEYS = True
LONG_FRAMES = 40          # håll 0+1 så här länge (40 = ca 1,3 s) för att gå ur

EXIT_FRAMES = 8           # så länge alla fyra måste hållas (8 = ca 0,25 s)
FRAME_MS = 33             # ca 30 bilder per sekund
SCORE_FILE = "rekord.json"


SEL_TXT = "0+1" if TWO_KEYS else str(K_A)          # välj
EXIT_TXT = "hall 0+1" if TWO_KEYS else "alla 4"     # gå ur


def rgb(r, g, b):
    """RGB888 -> RGB565 med bytebyte (skärmen vill ha big endian)."""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


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


# ---------------------------------------------------------------
# Skärmdrivrutin
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = bytearray(W * H * 2)
        super().__init__(self.buffer, W, H, framebuf.RGB565)
        # Samma minne sett som en stående skärm (240x320)
        self.pfb = framebuf.FrameBuffer(self.buffer, VW, VH, framebuf.RGB565)
        # Extra buffert för bakgrunder: ritas en gång och kopieras sedan
        # in varje bild, vilket går mycket fortare än att rita om dem.
        try:
            self.bg = bytearray(W * H * 2)
        except MemoryError:
            self.bg = None
        self.bg_fn = None
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=SPI_HZ, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.backlight(100)
        self._init_display()

    def backlight(self, percent):
        percent = max(0, min(100, percent))
        self.bl.duty_u16(int(percent * 655.35))

    def cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def _init_display(self):
        self.rst(1)
        time.sleep_ms(5)
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(120)
        self.cmd(0x3A, [0x05])                      # 16 bitar/pixel
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
        self.cmd(0x21)                              # inverterade färger (krävs)
        self.cmd(0x11)                              # vakna
        time.sleep_ms(120)
        self.cmd(0x29)                              # skärm på
        self.landscape()

    def _window(self, w, h):
        self.cmd(0x2A, [0x00, 0x00, (w - 1) >> 8, (w - 1) & 0xFF])
        self.cmd(0x2B, [0x00, 0x00, (h - 1) >> 8, (h - 1) & 0xFF])

    def landscape(self):
        self.cmd(0x36, [0x70])
        self._window(W, H)

    def portrait(self):
        self.cmd(0x36, [0x00])
        self._window(VW, VH)

    def show(self):
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)

    def set_bg(self, fn):
        """Ritar bakgrunden med fn och sparar den."""
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
# Knappar med "nyss nedtryckt"-detektering
# ---------------------------------------------------------------
class Keys:
    def __init__(self):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in KEY_PINS]
        self.now = [False] * 4
        self.prev = [False] * 4
        self.cnt = [0] * 4
        self.all_cnt = 0
        # För 2-knappsläget
        self.both_cnt = 0
        self.chorded = False      # har båda varit nere under det här trycket?
        self.chord_edge = False   # båda gick ner just nu
        self.chord_tap = False    # kort tryck på båda, just släppt
        self.tapped = [False, False]

    def update(self):
        self.prev = self.now
        self.now = [p.value() == 0 for p in self.pins]
        old = self.cnt[:]
        for i in range(4):
            self.cnt[i] = self.cnt[i] + 1 if self.now[i] else 0
        self.all_cnt = self.all_cnt + 1 if all(self.now) else 0
        both = self.now[0] and self.now[1]
        was_both = self.both_cnt > 0
        self.chord_edge = both and not was_both
        self.chord_tap = was_both and not both and self.both_cnt < LONG_FRAMES
        if both:
            self.chorded = True
        for i in (0, 1):
            # Ett "tryck" räknas när knappen släpps, om den andra inte
            # också var nere och den inte hölls inne länge (upprepning).
            self.tapped[i] = self.prev[i] and not self.now[i] \
                and not self.chorded and old[i] <= 8
        self.both_cnt = self.both_cnt + 1 if both else 0
        if not self.now[0] and not self.now[1]:
            self.chorded = False

    # --- Handlingar som fungerar i både 4- och 2-knappsläget ---
    def sel(self):
        """Välj / ok / starta."""
        return self.chord_tap if TWO_KEYS else self.pressed(K_A)

    def back(self):
        """Tillbaka / paus (finns inte i 2-knappsläget)."""
        return False if TWO_KEYS else self.pressed(K_B)

    def prev_(self):
        return self.tapped[0] if TWO_KEYS else self.pressed(K_X)

    def next_(self):
        return self.tapped[1] if TWO_KEYS else self.pressed(K_Y)

    def step(self, k, delay=8, rate=2):
        """Flytta ett steg, upprepas om knappen hålls inne."""
        if not TWO_KEYS:
            return self.repeat(k, delay, rate)
        c = self.cnt[k]
        return self.tapped[k] or (c > delay and not self.chorded
                                   and (c - delay) % rate == 0)

    def rotate(self):
        return self.chord_edge if TWO_KEYS else self.pressed(K_A)

    def held(self, k):
        return self.now[k]

    def pressed(self, k):
        return self.now[k] and not self.prev[k]

    def repeat(self, k, delay=7, rate=2):
        """Som pressed, men upprepas om knappen hålls in."""
        c = self.cnt[k]
        return c == 1 or (c > delay and (c - delay) % rate == 0)

    def any_held(self):
        return any(self.now)

    def exit_requested(self):
        """Alla fyra knapparna (eller 0+1 länge) = gå ur spelet."""
        if TWO_KEYS:
            return self.both_cnt >= LONG_FRAMES
        return self.all_cnt >= EXIT_FRAMES

    def wait_release(self):
        self.update()
        while self.any_held():
            time.sleep_ms(10)
            self.update()
        self.update()


# ---------------------------------------------------------------
# Rekord som sparas på Picon
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


def submit_score(game, score):
    """Returnerar (rekord, nytt_rekord?)."""
    best = SCORES.get(game, 0)
    if score > best:
        SCORES[game] = score
        save_scores()
        return score, True
    return best, False


def record_info(game, score):
    best, new = submit_score(game, score)
    return ("NYTT REKORD!" if new else "Rekord: %d" % best), new


# ---------------------------------------------------------------
# Grafikhjälp
# ---------------------------------------------------------------
_glyph = bytearray(8)
_gfb = framebuf.FrameBuffer(_glyph, 8, 8, framebuf.MONO_HLSB)
_RUNS = {}


def _runs(ch):
    """Bokstavens pixlar som horisontella streck (sparas i en cache)."""
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
    """Skriver text i valfri storlek (det inbyggda typsnittet är 8x8)."""
    if scale == 1:
        fb.text(s, x, y, c)
        return
    fr = fb.fill_rect
    for ch in s:
        for run in _runs(ch):
            fr(x + run[0] * scale, y + run[1] * scale, run[2] * scale, scale, c)
        x += 8 * scale


def text_w(s, scale=1):
    return len(s) * 8 * scale


def center_text(fb, s, y, c, scale=1, cx=W // 2):
    big_text(fb, s, cx - text_w(s, scale) // 2, y, c, scale)


def shadow_text(fb, s, y, c, scale, cx=W // 2):
    center_text(fb, s, y + 3, SHADOW, scale, cx)
    center_text(fb, s, y, c, scale, cx)


def wave_text(fb, s, y, scale, cols, t, amp=3):
    """Text där varje bokstav gungar och har egen färg."""
    x = (W - text_w(s, scale)) // 2
    step = 8 * scale
    for i, ch in enumerate(s):
        if ch != " ":
            dy = int(amp * math.sin(t * 0.15 + i * 0.7))
            big_text(fb, ch, x + 3, y + dy + 3, SHADOW, scale)
            big_text(fb, ch, x, y + dy, cols[i % len(cols)], scale)
        x += step


def lerp_col(c1, c2, t):
    return rgb(int(c1[0] + (c2[0] - c1[0]) * t),
               int(c1[1] + (c2[1] - c1[1]) * t),
               int(c1[2] + (c2[2] - c1[2]) * t))


def clip_rect(fb, x, y, w, h, c, x0, x1):
    """fill_rect som bara ritar mellan x0 och x1 (för förhandsvisningar)."""
    a = max(x, x0)
    b = min(x + w, x1)
    if b > a:
        fb.fill_rect(a, y, b - a, h, c)


def tri(t, period):
    """Triangelvåg 0..1..0, bra för studsande animationer."""
    p = (t % period) / period
    return p * 2 if p < 0.5 else 2 - p * 2


GRADIENT = [lerp_col((8, 8, 40), (45, 0, 60), y / (H - 1)) for y in range(H)]
STAR_COLS = (rgb(70, 70, 110), rgb(150, 150, 200), rgb(255, 255, 255))
RAINBOW = [lerp_col((0, 230, 255), (255, 40, 200), i / 10) for i in range(11)]


def draw_gradient(fb):
    for y in range(H):
        fb.hline(0, y, W, GRADIENT[y])


_fps = [0, 0]


def frame_wait(t0):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < FRAME_MS:
        time.sleep_ms(FRAME_MS - used)
    # Skriv ut bilder per sekund i Thonny var 5:e sekund ungefär
    _fps[0] += 1
    if _fps[0] >= 150:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, _fps[1])
        if dt > 0:
            print("FPS: %d" % (150000 // dt))
        _fps[0] = 0
        _fps[1] = now


class Stars:
    def __init__(self, n=50, w=W, h=H):
        self.w, self.h = w, h
        self.s = [[random.randint(0, w - 1), random.randint(0, h - 1),
                   random.randint(1, 3)] for _ in range(n)]

    @native
    def draw(self, fb, speed=1.0):
        for s in self.s:
            s[0] -= s[2] * speed
            if s[0] < 0:
                s[0] += self.w
                s[1] = random.randint(0, self.h - 1)
            x = int(s[0])
            if s[2] == 3 or speed > 2:
                fb.hline(x, s[1], 2 + int(speed * s[2] / 2), STAR_COLS[s[2] - 1])
            else:
                fb.pixel(x, s[1], STAR_COLS[s[2] - 1])


# ---------------------------------------------------------------
# Gemensamma skärmar
# ---------------------------------------------------------------
def pause_screen(lcd, keys):
    """Returnerar True om man vill tillbaka till menyn."""
    lcd.fill_rect(70, 74, 180, 92, BG)
    lcd.rect(70, 74, 180, 92, YELLOW)
    center_text(lcd, "PAUS", 86, YELLOW, 3)
    center_text(lcd, "%d: fortsatt" % K_A, 120, WHITE)
    center_text(lcd, "%d: till menyn" % K_B, 134, WHITE)
    center_text(lcd, "(alla 4: meny)", 150, GRAY)
    lcd.show()
    while True:
        keys.update()
        if keys.exit_requested():
            return True
        if keys.pressed(K_A):
            keys.wait_release()
            return False
        if keys.pressed(K_B):
            return True
        time.sleep_ms(20)


def result_screen(lcd, keys, title, big, col, info="", party=False):
    """Visas när ett spel är slut. Returnerar True = spela igen."""
    stars = Stars(40)
    lcd.set_bg(draw_gradient)
    keys.wait_release()
    t = 0
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 10:
            if (keys.tapped[0] if TWO_KEYS else keys.pressed(K_A)):
                return True
            if (keys.tapped[1] if TWO_KEYS else keys.pressed(K_B)) \
                    or keys.exit_requested():
                return False
        lcd.load_bg()
        stars.draw(lcd)
        if party:
            for _ in range(40):
                lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3),
                              3, 3, random.choice(RAINBOW))
        dy = int(4 * math.sin(t * 0.2))
        shadow_text(lcd, title, 40 + dy, col, 3)
        center_text(lcd, big, 92, WHITE, 5)
        if info:
            if party:
                if (t // 8) % 2 == 0:
                    center_text(lcd, info, 156, YELLOW, 2)
            else:
                center_text(lcd, info, 160, GRAY)
        if TWO_KEYS:
            center_text(lcd, "0: spela igen    1: meny", 212, GRAY)
        else:
            center_text(lcd, "%d: spela igen    %d: meny" % (K_A, K_B), 212, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def choose(lcd, keys, title, options, accent):
    """Liten meny. Returnerar valt index eller None (B = tillbaka)."""
    stars = Stars(40)
    lcd.set_bg(draw_gradient)
    sel = 0
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.prev_():
            sel = (sel - 1) % len(options)
        if keys.next_():
            sel = (sel + 1) % len(options)
        if keys.sel():
            return sel
        if keys.back() or keys.exit_requested():
            return None
        lcd.load_bg()
        stars.draw(lcd)
        wave_text(lcd, title, 30, 4, RAINBOW, t)
        pulse = (math.sin(t * 0.2) + 1) / 2
        for i, item in enumerate(options):
            y = 100 + i * 36
            if i == sel:
                lcd.fill_rect(60, y - 6, 200, 28, accent)
                lcd.fill_rect(60, y - 6, 4 + int(pulse * 6), 28, WHITE)
                center_text(lcd, item, y, BG, 2)
            else:
                center_text(lcd, item, y, WHITE, 2)
        if TWO_KEYS:
            center_text(lcd, "0/1: valj  0+1: ok  hall: tillbaka", 222, GRAY)
        else:
            center_text(lcd, "%d/%d: valj  %d: ok  %d: tillbaka"
                        % (K_X, K_Y, K_A, K_B), 222, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: PONG
# ---------------------------------------------------------------
PW, PH = 6, 44
PONG_BS = 6
PONG_WIN = 7
TRAIL_COLS = [lerp_col((6, 6, 22), (255, 255, 255), i / 5) for i in range(1, 5)]


def game_pong(lcd, keys):
    mode = choose(lcd, keys, "PONG", ("VS DATORN", "2 SPELARE"), CYAN)
    if mode is None:
        return
    while play_pong(lcd, keys, mode == 1):
        pass


def play_pong(lcd, keys, two_players):
    BS = PONG_BS
    lx, rx = 12, W - 12 - PW
    ly = ry = (H - PH) / 2
    s1 = s2 = 0
    bx = by = vx = vy = 0.0
    speed = 4.0
    trail = []
    countdown = 45
    serve_dir = random.choice((-1, 1))
    cpu_err = 0
    cpu_speed = 3.6
    ldir, rdir = 1, -1

    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if not two_players and keys.pressed(K_B) and pause_screen(lcd, keys):
            return False

        if two_players and TWO_KEYS:
            # En knapp per spelare: paddeln åker hela tiden, tryck = vänd
            if keys.pressed(0):
                ldir = -ldir
            if keys.pressed(1):
                rdir = -rdir
            ly += 5 * ldir
            ry += 5 * rdir
            if ly <= 0 or ly >= H - PH:
                ldir = -ldir
            if ry <= 0 or ry >= H - PH:
                rdir = -rdir
        elif two_players:
            if keys.held(PONG_P1[0]):
                ly -= 6
            if keys.held(PONG_P1[1]):
                ly += 6
            if keys.held(PONG_P2[0]):
                ry -= 6
            if keys.held(PONG_P2[1]):
                ry += 6
        else:
            if keys.held(PONG_SOLO[0]):
                ly -= 6
            if keys.held(PONG_SOLO[1]):
                ly += 6
            if vx > 0:
                target = by + BS / 2 - PH / 2 + cpu_err
            else:
                target = (H - PH) / 2
            ry += max(-cpu_speed, min(cpu_speed, target - ry))
        ly = max(0, min(H - PH, ly))
        ry = max(0, min(H - PH, ry))

        if countdown > 0:
            countdown -= 1
            bx, by = W / 2 - BS / 2, H / 2 - BS / 2
            trail = []
            if countdown == 0:
                speed = 4.0
                ang = random.uniform(-0.5, 0.5)
                vx = speed * math.cos(ang) * serve_dir
                vy = speed * math.sin(ang)
        else:
            trail.append((int(bx), int(by)))
            if len(trail) > 4:
                trail.pop(0)
            bx += vx
            by += vy
            if by < 0:
                by = 0
                vy = -vy
            elif by > H - BS:
                by = H - BS
                vy = -vy

            if vx < 0 and bx <= lx + PW and bx + BS >= lx \
                    and by + BS >= ly and by <= ly + PH:
                bx = lx + PW
                rel = ((by + BS / 2) - (ly + PH / 2)) / (PH / 2)
                ang = max(-1.0, min(1.0, rel))
                speed = min(speed * 1.07, 9.0)
                vx = speed * math.cos(ang)
                vy = speed * math.sin(ang)
                cpu_err = random.randint(-18, 18)
            elif vx > 0 and bx + BS >= rx and bx <= rx + PW \
                    and by + BS >= ry and by <= ry + PH:
                bx = rx - BS
                rel = ((by + BS / 2) - (ry + PH / 2)) / (PH / 2)
                ang = max(-1.0, min(1.0, rel))
                speed = min(speed * 1.07, 9.0)
                vx = -speed * math.cos(ang)
                vy = speed * math.sin(ang)

            if bx < -BS:
                s2 += 1
                serve_dir = -1
                countdown = 40
            elif bx > W:
                s1 += 1
                serve_dir = 1
                countdown = 40
            if s1 >= PONG_WIN or s2 >= PONG_WIN:
                if two_players:
                    text = "SPELARE %d VANN" % (1 if s1 > s2 else 2)
                else:
                    text = "DU VANN!" if s1 > s2 else "DATORN VANN"
                info = ""
                if not two_players and s1 > s2:
                    best, new = submit_score("pong", s1 - s2)
                    info = "STORSTA VINST!" if new else "Storsta vinst: +%d" % best
                return result_screen(lcd, keys, text, "%d - %d" % (s1, s2),
                                     CYAN if s1 > s2 else MAGENTA, info,
                                     party=(s1 > s2 or two_players))

        lcd.fill(BG)
        for y in range(4, H, 16):
            lcd.fill_rect(W // 2 - 1, y, 2, 8, DIM)
        center_text(lcd, str(s1), 10, DIM, 5, cx=W // 2 - 50)
        center_text(lcd, str(s2), 10, DIM, 5, cx=W // 2 + 50)
        lcd.fill_rect(lx, int(ly), PW, PH, CYAN)
        lcd.vline(lx + 1, int(ly) + 2, PH - 4, WHITE)
        lcd.fill_rect(rx, int(ry), PW, PH, MAGENTA)
        lcd.vline(rx + PW - 2, int(ry) + 2, PH - 4, WHITE)
        if countdown > 0:
            if (countdown // 6) % 2 == 0:
                lcd.fill_rect(int(bx), int(by), BS, BS, YELLOW)
        else:
            for i, (tx, ty) in enumerate(trail):
                lcd.fill_rect(tx + 1, ty + 1, BS - 2, BS - 2, TRAIL_COLS[i])
            lcd.fill_rect(int(bx), int(by), BS, BS, WHITE)
        if two_players and TWO_KEYS:
            lcd.text("0: vand", lx + 12, H - 12, DIM)
            lcd.text("1: vand", rx - 62, H - 12, DIM)
        elif two_players:
            lcd.text("%d/%d" % PONG_P1, lx + 12, H - 12, DIM)
            lcd.text("%d/%d" % PONG_P2, rx - 34, H - 12, DIM)
        else:
            lcd.text("DU", lx + 12, H - 12, DIM)
            lcd.text("CPU", rx - 30, H - 12, DIM)
        lcd.show()
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: SNAKE
# ---------------------------------------------------------------
CELL = 10
GW, GH = 32, 22
S_TOP = 20
DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))     # höger, ner, vänster, upp
EYES = (((6, 2), (6, 6)), ((2, 6), (6, 6)), ((2, 2), (2, 6)), ((2, 2), (6, 2)))
SNAKE_COLS = [lerp_col((150, 255, 90), (0, 110, 70), i / 24) for i in range(25)]
S_FIELD = rgb(8, 20, 14)
S_DOT = rgb(20, 45, 30)


def game_snake(lcd, keys):
    while play_snake(lcd, keys):
        pass


def new_food(snake):
    while True:
        p = (random.randint(0, GW - 1), random.randint(0, GH - 1))
        if p not in snake:
            return p


def snake_bg(lcd):
    lcd.fill(BG)
    lcd.fill_rect(0, S_TOP, W, H - S_TOP, S_FIELD)
    for gy in range(0, GH, 2):
        for gx in range(0, GW, 2):
            lcd.pixel(gx * CELL + 5, S_TOP + gy * CELL + 5, S_DOT)
    lcd.text("SNAKE", 6, 6, GREEN)


@native
def draw_snake_field(lcd, snake, d, food, t, score, color_override=None):
    lcd.load_bg()
    # Äpple som pulserar
    fx, fy = food[0] * CELL + 5, S_TOP + food[1] * CELL + 5
    r = 4 if (t // 6) % 2 else 3
    lcd.ellipse(fx, fy + 1, r, r, RED, True)
    lcd.pixel(fx - 1, fy - 1, WHITE)
    lcd.fill_rect(fx, fy - 5, 2, 3, GREEN)
    # Ormen
    n = len(snake)
    for i in range(n - 1, -1, -1):
        sx, sy = snake[i]
        col = color_override if color_override is not None \
            else SNAKE_COLS[min(i, 24)]
        lcd.fill_rect(sx * CELL + 1, S_TOP + sy * CELL + 1, 8, 8, col)
        if i + 1 < n:      # fyll glappet mot nästa bit så ormen blir hel
            nx, ny = snake[i + 1]
            if nx == sx:
                lcd.fill_rect(sx * CELL + 2, S_TOP + min(sy, ny) * CELL + 9, 6, 2, col)
            elif ny == sy:
                lcd.fill_rect(min(sx, nx) * CELL + 9, S_TOP + sy * CELL + 2, 2, 6, col)
    hx, hy = snake[0]
    for e in EYES[d]:
        lcd.fill_rect(hx * CELL + e[0], S_TOP + hy * CELL + e[1], 2, 2, BG)
    lcd.text("POANG %d" % score, 110, 6, WHITE)
    lcd.text("REKORD %d" % SCORES.get("snake", 0), 218, 6, GRAY)


def play_snake(lcd, keys):
    snake = [(8, 11), (7, 11), (6, 11), (5, 11)]
    d = 0
    turns = []
    food = new_food(snake)
    score = 0
    tick = 0
    step = 5
    t = 0
    lcd.set_bg(snake_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if keys.pressed(K_B) and pause_screen(lcd, keys):
            return False
        if len(turns) < 2:
            if keys.pressed(SNAKE_LEFT):
                turns.append(-1)
            if keys.pressed(SNAKE_RIGHT):
                turns.append(1)

        tick += 1
        if tick >= step:
            tick = 0
            if turns:
                d = (d + turns.pop(0)) % 4
            dx, dy = DIRS[d]
            hx, hy = snake[0][0] + dx, snake[0][1] + dy
            if hx < 0 or hx >= GW or hy < 0 or hy >= GH or (hx, hy) in snake[:-1]:
                for k in range(8):          # död: blinka ormen
                    draw_snake_field(lcd, snake, d, food, t, score,
                                     WHITE if k % 2 == 0 else RED)
                    lcd.show()
                    time.sleep_ms(90)
                info, new = record_info("snake", score)
                return result_screen(lcd, keys, "GAME OVER", str(score),
                                     GREEN, info, party=new)
            snake.insert(0, (hx, hy))
            if (hx, hy) == food:
                score += 1
                food = new_food(snake)
                step = max(3, 5 - score // 6)
            else:
                snake.pop()

        draw_snake_field(lcd, snake, d, food, t, score)
        if t < 60 and (t // 10) % 2 == 0:
            center_text(lcd, "%d: vanster   %d: hoger" % (SNAKE_LEFT, SNAKE_RIGHT),
                        200, WHITE)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: BREAKOUT
# ---------------------------------------------------------------
BR_COLS, BR_ROWS = 10, 6
BR_TOP = 30
BR_ROW_COLS = ((255, 60, 90), (255, 140, 40), (255, 220, 40),
               (80, 230, 90), (40, 180, 255), (170, 90, 255))
BR_FILL = [rgb(*c) for c in BR_ROW_COLS]
BR_LIGHT = [lerp_col(c, (255, 255, 255), 0.5) for c in BR_ROW_COLS]
BR_DARK = [lerp_col(c, (0, 0, 0), 0.4) for c in BR_ROW_COLS]
PAD_W, PAD_H, PAD_Y = 50, 6, H - 18
BR_BS = 5


def game_breakout(lcd, keys):
    while play_breakout(lcd, keys):
        pass


def new_bricks(level):
    b = bytearray(BR_COLS * BR_ROWS)
    for i in range(len(b)):
        b[i] = 1 if level == 1 or random.random() > 0.15 else 0
    return b


@native
def draw_bricks(lcd, bricks):
    for row in range(BR_ROWS):
        y = BR_TOP + row * 12
        for col in range(BR_COLS):
            if bricks[row * BR_COLS + col]:
                x = col * 32 + 1
                lcd.fill_rect(x, y, 30, 10, BR_FILL[row])
                lcd.hline(x, y, 30, BR_LIGHT[row])
                lcd.hline(x, y + 9, 30, BR_DARK[row])


def play_breakout(lcd, keys):
    BS = BR_BS
    level, lives, score = 1, 3, 0
    bricks = new_bricks(level)
    px = (W - PAD_W) / 2
    attached = True
    bx = by = vx = vy = 0.0
    speed = 4.0
    parts = []
    banner = 45
    wait = 0
    t = 0

    def hit_bricks(x, y):
        nonlocal score
        hit = False
        for cx, cy in ((x, y), (x + BS - 1, y), (x, y + BS - 1), (x + BS - 1, y + BS - 1)):
            row = (int(cy) - BR_TOP) // 12
            col = int(cx) // 32
            if 0 <= row < BR_ROWS and 0 <= col < BR_COLS and bricks[row * BR_COLS + col]:
                bricks[row * BR_COLS + col] = 0
                score += (BR_ROWS - row) * 10
                hit = True
                for _ in range(6):
                    if len(parts) < 60:
                        parts.append([col * 32 + 15, BR_TOP + row * 12 + 5,
                                      random.uniform(-3, 3), random.uniform(-3, 1),
                                      12, BR_FILL[row]])
        return hit

    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if keys.pressed(K_B) and pause_screen(lcd, keys):
            return False
        if keys.held(K_X):
            px -= 7
        if keys.held(K_Y):
            px += 7
        px = max(0, min(W - PAD_W, px))

        if attached:
            bx, by = px + PAD_W / 2 - BS / 2, PAD_Y - BS
        else:
            wait = 0
        if attached:
            wait += 1
            if (keys.rotate() or (TWO_KEYS and wait > 45)) and banner == 0:
                attached = False
                ang = random.uniform(-0.4, 0.4)
                vx = speed * math.sin(ang)
                vy = -speed * math.cos(ang)
        else:
            bx += vx
            if bx < 0:
                bx = 0
                vx = -vx
            elif bx > W - BS:
                bx = W - BS
                vx = -vx
            if hit_bricks(bx, by):
                bx -= vx
                vx = -vx
            by += vy
            if by < 20:
                by = 20
                vy = -vy
            if hit_bricks(bx, by):
                by -= vy
                vy = -vy
            if vy > 0 and PAD_Y - BS <= by <= PAD_Y + PAD_H \
                    and bx + BS >= px and bx <= px + PAD_W:
                by = PAD_Y - BS
                rel = ((bx + BS / 2) - (px + PAD_W / 2)) / (PAD_W / 2)
                ang = max(-1.0, min(1.0, rel)) * 1.05
                vx = speed * math.sin(ang)
                vy = -speed * math.cos(ang)
            if by > H:
                lives -= 1
                attached = True
                if lives == 0:
                    info, new = record_info("breakout", score)
                    return result_screen(lcd, keys, "GAME OVER", str(score),
                                         ORANGE, info, party=new)
            if not any(bricks):
                level += 1
                bricks = new_bricks(level)
                speed = min(4.0 + (level - 1) * 0.6, 7.0)
                attached = True
                banner = 45

        if banner > 0:
            banner -= 1

        lcd.fill(BG)
        lcd.hline(0, 19, W, DIM)
        draw_bricks(lcd, bricks)
        for p in parts[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.3
            p[4] -= 1
            if p[4] <= 0:
                parts.remove(p)
            else:
                lcd.fill_rect(int(p[0]), int(p[1]), 2, 2, p[5])
        ipx = int(px)
        lcd.fill_rect(ipx, PAD_Y, PAD_W, PAD_H, CYAN)
        lcd.hline(ipx + 2, PAD_Y + 1, PAD_W - 4, WHITE)
        lcd.fill_rect(int(bx), int(by), BS, BS, WHITE)
        lcd.text("POANG %d" % score, 6, 6, WHITE)
        lcd.text("NIVA %d" % level, 136, 6, ORANGE)
        for i in range(lives):
            lcd.ellipse(W - 12 - i * 14, 9, 4, 4, RED, True)
        if banner > 0:
            center_text(lcd, "NIVA %d" % level, 120, YELLOW, 3)
        elif attached and (t // 10) % 2 == 0:
            center_text(lcd, "%s: skjut  %d/%d: styr" % (SEL_TXT, K_X, K_Y), 150, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: FLAPPY
# ---------------------------------------------------------------
GROUND_Y = H - 22
BIRD_X = 70
PIPE_W = 36
GAP = 78
SPACING = 150
GRAVITY = 0.45
FLAP = -5.6
SKY = [lerp_col((70, 160, 255), (200, 235, 255), y / GROUND_Y) for y in range(GROUND_Y)]
PIPE_COL = rgb(60, 190, 70)
PIPE_LIGHT = rgb(150, 240, 120)
PIPE_DARK = rgb(20, 110, 40)
GROUND_COL = rgb(200, 160, 90)
GROUND_DARK = rgb(160, 120, 60)
GRASS = rgb(90, 200, 60)
CLOUD = rgb(245, 250, 255)


def game_flappy(lcd, keys):
    while play_flappy(lcd, keys):
        pass


def draw_bird(fb, cx, cy, flap_up):
    fb.ellipse(cx, cy, 9, 7, YELLOW, True)
    fb.ellipse(cx - 1, cy + 3, 6, 3, rgb(255, 245, 170), True)
    fb.ellipse(cx - 4, cy + (-3 if flap_up else 2), 5, 3, rgb(255, 170, 30), True)
    fb.ellipse(cx + 4, cy - 3, 3, 3, WHITE, True)
    fb.fill_rect(cx + 5, cy - 3, 2, 2, BLACK)
    fb.fill_rect(cx + 7, cy, 6, 3, ORANGE)


def draw_pipe(fb, x, gap_y, x0=0, x1=W, top=0, bottom=GROUND_Y, gap=GAP, pw=PIPE_W):
    t_end = gap_y - gap // 2
    b_start = gap_y + gap // 2
    for (y, h) in ((top, t_end - top), (b_start, bottom - b_start)):
        if h <= 0:
            continue
        clip_rect(fb, x, y, pw, h, PIPE_COL, x0, x1)
        clip_rect(fb, x + 4, y, 4, h, PIPE_LIGHT, x0, x1)
        clip_rect(fb, x + pw - 5, y, 3, h, PIPE_DARK, x0, x1)
    cap = 8 if pw > 20 else 4
    clip_rect(fb, x - 3, t_end - cap, pw + 6, cap, PIPE_DARK, x0, x1)
    clip_rect(fb, x - 2, t_end - cap + 1, pw + 4, cap - 2, PIPE_COL, x0, x1)
    clip_rect(fb, x - 3, b_start, pw + 6, cap, PIPE_DARK, x0, x1)
    clip_rect(fb, x - 2, b_start + 1, pw + 4, cap - 2, PIPE_COL, x0, x1)


def flappy_bg(lcd):
    for y in range(GROUND_Y):
        lcd.hline(0, y, W, SKY[y])
    lcd.fill_rect(0, GROUND_Y, W, H - GROUND_Y, GROUND_COL)
    lcd.fill_rect(0, GROUND_Y, W, 4, GRASS)


def play_flappy(lcd, keys):
    by = H / 2
    vy = 0.0
    started = False
    score = 0
    pipes = [[W + 40 + i * SPACING, random.randint(60, GROUND_Y - 60), False]
             for i in range(3)]
    clouds = [[random.randint(0, W), random.randint(10, 90), random.randint(14, 24)]
              for _ in range(4)]
    ground = 0.0
    t = 0
    lcd.set_bg(flappy_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if keys.pressed(K_B) and pause_screen(lcd, keys):
            return False
        flap = keys.pressed(K_A) or keys.pressed(K_X) or keys.pressed(K_Y)
        speed = min(2.6 + score * 0.05, 4.2)
        dead = False

        if not started:
            by = H / 2 + 6 * math.sin(t * 0.15)
            if flap:
                started = True
                vy = FLAP
        else:
            vy = min(vy + GRAVITY, 7.0)
            if flap:
                vy = FLAP
            by += vy
            for p in pipes:
                p[0] -= speed
                if p[0] < -PIPE_W - 6:
                    p[0] += 3 * SPACING
                    p[1] = random.randint(60, GROUND_Y - 60)
                    p[2] = False
                if not p[2] and p[0] + PIPE_W < BIRD_X - 9:
                    p[2] = True
                    score += 1
                if p[0] - 3 < BIRD_X + 8 and p[0] + PIPE_W + 3 > BIRD_X - 8:
                    if by - 6 < p[1] - GAP // 2 or by + 6 > p[1] + GAP // 2:
                        dead = True
            if by + 7 >= GROUND_Y or by < -10:
                dead = True

        ground = (ground + speed) % 16

        lcd.load_bg()
        for c in clouds:
            c[0] -= 0.4
            if c[0] < -60:
                c[0] = W + 20
                c[1] = random.randint(10, 90)
            cx = int(c[0])
            lcd.ellipse(cx, c[1], c[2], c[2] // 2, CLOUD, True)
            lcd.ellipse(cx + c[2], c[1] + 3, c[2] - 4, c[2] // 3, CLOUD, True)
            lcd.ellipse(cx - c[2] + 4, c[1] + 4, c[2] - 6, c[2] // 3, CLOUD, True)
        for p in pipes:
            if p[0] < W:
                draw_pipe(lcd, int(p[0]), p[1])
        for x in range(-int(ground), W, 16):
            lcd.fill_rect(x, GROUND_Y + 8, 8, 3, GROUND_DARK)
        draw_bird(lcd, BIRD_X, int(by), (t // 4) % 2 == 0 or vy < 0)

        if started:
            shadow_text(lcd, str(score), 14, WHITE, 4)
        else:
            shadow_text(lcd, "FLAPPY", 30, YELLOW, 4)
            if (t // 10) % 2 == 0:
                center_text(lcd, "Tryck %d for att flyga" % K_X, 160, BG)
        lcd.show()

        if dead:
            lcd.fill(WHITE)
            lcd.show()
            info, new = record_info("flappy", score)
            time.sleep_ms(450)
            return result_screen(lcd, keys, "GAME OVER", str(score),
                                 YELLOW, info, party=new)
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: TETRIS
# ---------------------------------------------------------------
T_CELL = 11
T_W, T_H = 10, 20
T_X, T_Y = 105, 10
SHAPES = (
    ((-1, 0), (0, 0), (1, 0), (2, 0)),      # I
    ((0, 0), (1, 0), (0, 1), (1, 1)),       # O
    ((-1, 0), (0, 0), (1, 0), (0, -1)),     # T
    ((-1, 0), (0, 0), (0, -1), (1, -1)),    # S
    ((-1, -1), (0, -1), (0, 0), (1, 0)),    # Z
    ((-1, -1), (-1, 0), (0, 0), (1, 0)),    # J
    ((1, -1), (-1, 0), (0, 0), (1, 0)),     # L
)
T_RAW = ((0, 230, 255), (255, 220, 40), (180, 80, 255), (80, 230, 90),
         (255, 50, 70), (60, 110, 255), (255, 140, 40))
T_FILL = [rgb(*c) for c in T_RAW]
T_LIGHT = [lerp_col(c, (255, 255, 255), 0.5) for c in T_RAW]
T_DARK = [lerp_col(c, (0, 0, 0), 0.45) for c in T_RAW]
T_LINE_PTS = (0, 40, 100, 300, 1200)
T_BOARD_BG = rgb(12, 12, 32)
TETRIS_HOLD = 8           # 2-knappsläget: håll så här länge (bilder) = fall snabbare


def game_tetris(lcd, keys):
    while play_tetris(lcd, keys):
        pass


def shuffled(n):
    a = list(range(n))
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a


def t_cell(fb, x, y, ci):
    fb.fill_rect(x, y, 10, 10, T_FILL[ci])
    fb.hline(x, y, 10, T_LIGHT[ci])
    fb.vline(x, y, 10, T_LIGHT[ci])
    fb.hline(x, y + 9, 10, T_DARK[ci])
    fb.vline(x + 9, y, 10, T_DARK[ci])


def tetris_bg(lcd):
    draw_gradient(lcd)
    lcd.fill_rect(T_X - 3, T_Y - 3, T_W * T_CELL + 5, T_H * T_CELL + 5, CYAN)
    lcd.fill_rect(T_X - 1, T_Y - 1, T_W * T_CELL + 1, T_H * T_CELL + 1, T_BOARD_BG)
    for y in range(T_H):
        for x in range(T_W):
            lcd.pixel(T_X + x * T_CELL + 5, T_Y + y * T_CELL + 5, DIM)
    big_text(lcd, "TETRIS", 236, 10, CYAN, 1)
    lcd.text("NASTA", 236, 30, GRAY)
    lcd.rect(232, 42, 76, 52, DIM)
    lcd.text("POANG", 10, 30, GRAY)
    lcd.text("RADER", 10, 80, GRAY)
    lcd.text("NIVA", 10, 130, GRAY)
    lcd.text("%d/%d flytta" % (K_X, K_Y), 4, 190, DIM)
    lcd.text("%s vrid" % SEL_TXT, 4, 202, DIM)
    if TWO_KEYS:
        lcd.text("hall 0/1 snabbare", 4, 214, DIM)
    else:
        lcd.text("%d snabbare" % K_B, 4, 214, DIM)


@native
def draw_board(lcd, board):
    for y in range(T_H):
        row = board[y]
        for x in range(T_W):
            v = row[x]
            if v:
                t_cell(lcd, T_X + x * T_CELL, T_Y + y * T_CELL, v - 1)


def play_tetris(lcd, keys):
    board = [bytearray(T_W) for _ in range(T_H)]
    bag = []

    def next_piece():
        if not bag:
            bag.extend(shuffled(7))
        return bag.pop()

    def fits(cells, px, py):
        for cx, cy in cells:
            x = px + cx
            y = py + cy
            if x < 0 or x >= T_W or y >= T_H:
                return False
            if y >= 0 and board[y][x]:
                return False
        return True

    cur = next_piece()
    nxt = next_piece()
    cells = SHAPES[cur]
    px, py = 4, 1
    score = lines = 0
    level = 1
    fall = 0
    lcd.set_bg(tetris_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if TWO_KEYS:
            # Kort tryck = ett steg åt sidan, håll inne = fall snabbare
            if keys.tapped[0] and fits(cells, px - 1, py):
                px -= 1
            if keys.tapped[1] and fits(cells, px + 1, py):
                px += 1
            soft = (keys.cnt[0] > TETRIS_HOLD or keys.cnt[1] > TETRIS_HOLD) \
                and not keys.chorded
        else:
            if keys.step(K_X, 7) and fits(cells, px - 1, py):
                px -= 1
            if keys.step(K_Y, 7) and fits(cells, px + 1, py):
                px += 1
            soft = keys.held(K_B)
        if keys.rotate() and cur != 1:
            r = tuple((-cy, cx) for cx, cy in cells)
            for dx in (0, -1, 1, -2, 2):
                if fits(r, px + dx, py):
                    cells = r
                    px += dx
                    break
        fall += 1
        if fall >= (2 if soft else max(2, 22 - level * 2)):
            fall = 0
            if fits(cells, px, py + 1):
                py += 1
                if soft:
                    score += 1
            else:
                # Lås fast biten
                for cx, cy in cells:
                    if py + cy >= 0:
                        board[py + cy][px + cx] = cur + 1
                full = [y for y in range(T_H) if all(board[y])]
                if full:
                    for k in range(6):       # blinka raderna
                        lcd.load_bg()
                        draw_board(lcd, board)
                        if k % 2 == 0:
                            for y in full:
                                lcd.fill_rect(T_X, T_Y + y * T_CELL, T_W * T_CELL - 1, 10, WHITE)
                        lcd.show()
                        time.sleep_ms(50)
                    for y in full:
                        del board[y]
                        board.insert(0, bytearray(T_W))
                    score += T_LINE_PTS[len(full)] * level
                    lines += len(full)
                    level = lines // 10 + 1
                cur = nxt
                nxt = next_piece()
                cells = SHAPES[cur]
                px, py = 4, 1
                if not fits(cells, px, py):
                    info, new = record_info("tetris", score)
                    return result_screen(lcd, keys, "GAME OVER", str(score),
                                         CYAN, info, party=new)

        # --- Rita ---
        lcd.load_bg()
        draw_board(lcd, board)
        gy = py
        while fits(cells, px, gy + 1):
            gy += 1
        ci = cur
        for cx, cy in cells:                 # skuggbit som visar var den landar
            if gy + cy >= 0:
                lcd.rect(T_X + (px + cx) * T_CELL, T_Y + (gy + cy) * T_CELL,
                         10, 10, T_DARK[ci])
        for cx, cy in cells:
            if py + cy >= 0:
                t_cell(lcd, T_X + (px + cx) * T_CELL, T_Y + (py + cy) * T_CELL, ci)
        for cx, cy in SHAPES[nxt]:
            t_cell(lcd, 260 + cx * T_CELL, 66 + cy * T_CELL, nxt)
        big_text(lcd, str(score), 10, 44, WHITE, 2)
        big_text(lcd, str(lines), 10, 94, WHITE, 2)
        big_text(lcd, str(level), 10, 144, YELLOW, 2)
        lcd.show()
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: DINO
# ---------------------------------------------------------------
D_GROUND = 196
D_X = 40
DINO_COL = rgb(170, 230, 170)
CACTUS_COL = rgb(60, 170, 80)
CACTUS_DARK = rgb(30, 110, 50)
NIGHT = [lerp_col((5, 5, 30), (40, 20, 70), y / D_GROUND) for y in range(D_GROUND)]


def game_dino(lcd, keys):
    while play_dino(lcd, keys):
        pass


def dino_bg(lcd):
    for y in range(D_GROUND):
        lcd.hline(0, y, W, NIGHT[y])
    lcd.fill_rect(0, D_GROUND, W, H - D_GROUND, rgb(25, 20, 40))
    lcd.hline(0, D_GROUND, W, GRAY)
    lcd.ellipse(270, 40, 16, 16, rgb(250, 245, 210), True)
    lcd.ellipse(262, 36, 14, 14, NIGHT[36], True)
    for i in range(40):
        lcd.pixel((i * 73 + 11) % W, (i * 37 + 5) % (D_GROUND - 40), STAR_COLS[i % 3])


def draw_dino(fb, x, y, t, in_air):
    c = DINO_COL
    fb.fill_rect(x + 10, y, 12, 8, c)            # huvud
    fb.fill_rect(x + 13, y + 2, 2, 2, BG)        # öga
    fb.fill_rect(x + 18, y + 6, 4, 1, BG)        # mun
    fb.fill_rect(x + 2, y + 8, 14, 10, c)        # kropp
    fb.fill_rect(x + 10, y + 8, 6, 3, c)
    fb.fill_rect(x, y + 8, 3, 6, c)              # svans
    fb.fill_rect(x + 16, y + 11, 3, 2, c)        # arm
    if in_air:
        fb.fill_rect(x + 4, y + 18, 3, 6, c)
        fb.fill_rect(x + 11, y + 18, 3, 6, c)
    elif (t // 3) % 2:
        fb.fill_rect(x + 4, y + 18, 3, 6, c)
        fb.fill_rect(x + 11, y + 18, 3, 3, c)
    else:
        fb.fill_rect(x + 4, y + 18, 3, 3, c)
        fb.fill_rect(x + 11, y + 18, 3, 6, c)


def draw_obstacle(fb, o, t):
    x, w, h, kind = int(o[0]), o[1], o[2], o[3]
    if kind == 0:                                 # kaktus
        top = D_GROUND - h
        for sx in range(x, x + w, 9):
            fb.fill_rect(sx + 1, top, 6, h, CACTUS_COL)
            fb.vline(sx + 2, top + 1, h - 2, CACTUS_DARK)
            fb.fill_rect(sx - 2, top + h // 3, 3, 3, CACTUS_COL)
            fb.fill_rect(sx - 2, top + h // 3 - 6, 3, 6, CACTUS_COL)
            fb.fill_rect(sx + 7, top + h // 2, 3, 3, CACTUS_COL)
            fb.fill_rect(sx + 7, top + h // 2 - 5, 3, 5, CACTUS_COL)
    else:                                         # fågel
        y = o[4]
        fb.fill_rect(x + 4, y + 4, 14, 5, MAGENTA)
        fb.fill_rect(x, y + 5, 5, 3, ORANGE)
        if (t // 5) % 2:
            fb.fill_rect(x + 7, y - 4, 6, 8, MAGENTA)
        else:
            fb.fill_rect(x + 7, y + 8, 6, 6, MAGENTA)


def play_dino(lcd, keys):
    dy = 0.0          # höjd över marken
    vy = 0.0
    started = False
    dist = 0.0
    speed = 5.0
    obs = []
    next_gap = 200
    pebbles = [[random.randint(0, W), random.randint(D_GROUND + 4, H - 4)]
               for _ in range(14)]
    t = 0
    lcd.set_bg(dino_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        if keys.pressed(K_B) and pause_screen(lcd, keys):
            return False
        jump_down = keys.held(K_A) or keys.held(K_X) or keys.held(K_Y)
        jump_press = keys.pressed(K_A) or keys.pressed(K_X) or keys.pressed(K_Y)
        if not started:
            if jump_press:
                started = True
        else:
            if jump_press and dy == 0:
                vy = 8.5
            if not jump_down and vy > 3:     # kort tryck = lägre hopp
                vy = 3
            if dy > 0 or vy > 0:
                dy += vy
                vy -= 0.6
                if dy <= 0:
                    dy = 0
                    vy = 0
            speed = min(5.0 + dist / 1500, 11.0)
            dist += speed
            for o in obs:
                o[0] -= speed
            if obs and obs[0][0] < -40:
                obs.pop(0)
            if not obs or obs[-1][0] < W - next_gap:
                score_now = int(dist / 10)
                if score_now > 300 and random.random() < 0.3:
                    obs.append([W + 10, 18, 14, 1, D_GROUND - random.choice((22, 30))])
                else:
                    n = random.randint(1, 3)
                    obs.append([W + 10, n * 9, random.randint(20, 34), 0, 0])
                next_gap = random.randint(150, 260) + int(speed * 10)
            # Krock
            dtop = D_GROUND - 24 - int(dy)
            for o in obs:
                ox = o[0]
                if o[3] == 0:
                    otop, obot = D_GROUND - o[2], D_GROUND
                else:
                    otop, obot = o[4] - 4, o[4] + 12
                if ox + 3 < D_X + 18 and ox + o[1] - 3 > D_X + 4 \
                        and otop + 3 < dtop + 22 and obot > dtop + 4:
                    lcd.load_bg()
                    for o2 in obs:
                        draw_obstacle(lcd, o2, t)
                    draw_dino(lcd, D_X, dtop, t, True)
                    center_text(lcd, "AJ!", 90, RED, 4)
                    lcd.show()
                    time.sleep_ms(600)
                    score = int(dist / 10)
                    info, new = record_info("dino", score)
                    return result_screen(lcd, keys, "GAME OVER", str(score),
                                         GREEN, info, party=new)
            for p in pebbles:
                p[0] -= speed
                if p[0] < 0:
                    p[0] += W
                    p[1] = random.randint(D_GROUND + 4, H - 4)

        lcd.load_bg()
        for p in pebbles:
            lcd.fill_rect(int(p[0]), p[1], 2, 1, GRAY)
        for o in obs:
            draw_obstacle(lcd, o, t)
        draw_dino(lcd, D_X, D_GROUND - 24 - int(dy), t, dy > 0 or not started)
        if started:
            s = "%05d" % int(dist / 10)
            big_text(lcd, s, W - text_w(s, 2) - 8, 8, WHITE, 2)
            lcd.text("REKORD %d" % SCORES.get("dino", 0), 8, 12, GRAY)
        else:
            shadow_text(lcd, "DINO", 60, GREEN, 5)
            if (t // 10) % 2 == 0:
                center_text(lcd, "Tryck %d for att hoppa" % K_X, 130, WHITE)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Spel: SIMON (minnesspel med alla fyra knapparna)
# ---------------------------------------------------------------
# Rutornas plats på skärmen, en per knapp (KEY0..KEY3)
SIMON_POS = ((30, 46), (170, 46), (170, 136), (30, 136))
SIMON_RAW = ((80, 230, 90), (255, 50, 70), (255, 220, 40), (60, 140, 255))
SIMON_ON = [rgb(*c) for c in SIMON_RAW]
SIMON_OFF = [lerp_col(c, (0, 0, 0), 0.7) for c in SIMON_RAW]


def game_simon(lcd, keys):
    while play_simon(lcd, keys):
        pass


SIMON_PADS = 2 if TWO_KEYS else 4


def draw_simon(lcd, lit, msg, rnd, msg_col=WHITE):
    lcd.load_bg()
    for k in range(SIMON_PADS):
        if TWO_KEYS:                      # två stora rutor bredvid varandra
            x, y, w, h = 24 + k * 146, 46, 126, 170
        else:
            x, y = SIMON_POS[k]
            w, h = 120, 80
        on = k == lit
        if on:
            lcd.fill_rect(x - 4, y - 4, w + 8, h + 8, WHITE)
        lcd.fill_rect(x, y, w, h, SIMON_ON[k] if on else SIMON_OFF[k])
        center_text(lcd, str(k), y + h // 2 - 12, BG if on else SIMON_ON[k], 3, cx=x + w // 2)
    center_text(lcd, msg, 16, msg_col, 2)
    lcd.text("RUNDA %d" % rnd, 4, 228, GRAY)
    lcd.text("REKORD %d" % SCORES.get("simon", 0), 220, 228, GRAY)
    lcd.show()


def play_simon(lcd, keys):
    seq = []
    lcd.set_bg(draw_gradient)
    keys.wait_release()

    def wait_frames(n, lit, msg, rnd, col=WHITE):
        """Visar en bild i n bilder. Returnerar True om man vill gå ur."""
        for _ in range(n):
            t0 = time.ticks_ms()
            keys.update()
            if keys.exit_requested():
                return True
            draw_simon(lcd, lit, msg, rnd, col)
            frame_wait(t0)
        return False

    while True:
        seq.append(random.randint(0, SIMON_PADS - 1))
        rnd = len(seq)
        if wait_frames(20, -1, "TITTA...", rnd, GRAY):
            return False
        on = max(6, 16 - rnd)
        for k in seq:
            if wait_frames(on, k, "TITTA...", rnd, GRAY):
                return False
            if wait_frames(5, -1, "TITTA...", rnd, GRAY):
                return False
        keys.wait_release()
        idx = 0
        lit, lit_t = -1, 0
        while idx < len(seq):
            t0 = time.ticks_ms()
            keys.update()
            if keys.exit_requested():
                return False
            for k in range(SIMON_PADS):
                if keys.pressed(k):
                    lit, lit_t = k, 6
                    if k == seq[idx]:
                        idx += 1
                    else:
                        if wait_frames(25, seq[idx], "FEL!", rnd, RED):
                            return False
                        score = rnd - 1
                        info, new = record_info("simon", score)
                        return result_screen(lcd, keys, "GAME OVER", str(score),
                                             MAGENTA, info, party=new)
                    break
            if lit_t > 0:
                lit_t -= 1
            else:
                lit = -1
            draw_simon(lcd, lit, "DIN TUR! %d/%d" % (idx, len(seq)), rnd, YELLOW)
            frame_wait(t0)
        if wait_frames(6, lit, "BRA!", rnd, GREEN):
            return False
        if wait_frames(14, -1, "BRA!", rnd, GREEN):
            return False


# ---------------------------------------------------------------
# Knapptest (håll alla fyra knapparna i 1 sekund för att gå ur)
# ---------------------------------------------------------------
ROLES = {K_A: "valj/hoppa/vrid", K_B: "paus/tillbaka",
         K_X: "vanster/foreg.", K_Y: "hoger/nasta"}


def game_keytest(lcd, keys):
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if (keys.both_cnt if TWO_KEYS else keys.all_cnt) > 30:
            return
        lcd.fill(BG)
        center_text(lcd, "KNAPPTEST", 14, YELLOW, 3)
        center_text(lcd, "Tryck pa knapparna", 48, GRAY)
        for i in range(4):
            y = 70 + i * 34
            on = keys.held(i)
            lcd.fill_rect(20, y, 280, 28, CYAN if on else rgb(20, 20, 50))
            col = BG if on else WHITE
            big_text(lcd, "KEY%d" % i, 30, y + 6, col, 2)
            lcd.text("GP%d" % KEY_PINS[i], 106, y + 10, col)
            lcd.text(ROLES.get(i, ""), 150, y + 10, col)
        center_text(lcd, "Hall %s i 1 sek: tillbaka" % ("0+1" if TWO_KEYS else "alla 4"), 222, GRAY)
        lcd.show()
        frame_wait(t0)


# ---------------------------------------------------------------
# Förhandsvisningar för startsidan (ritas i en ruta 180x78)
# ---------------------------------------------------------------
PV_W, PV_H = 180, 78


def pv_pong(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    for yy in range(y + 3, y + PV_H, 10):
        fb.fill_rect(x + 89, yy, 2, 5, DIM)
    bx = x + 12 + int(tri(t, 70) * 152)
    by = y + 3 + int(tri(t, 44) * 68)
    ly = max(y, min(y + PV_H - 20, by - 8))
    ry = max(y, min(y + PV_H - 20, by - 10 + int(8 * math.sin(t * 0.1))))
    fb.fill_rect(x + 5, ly, 4, 20, CYAN)
    fb.fill_rect(x + PV_W - 9, ry, 4, 20, MAGENTA)
    fb.fill_rect(bx, by, 5, 5, WHITE)


def pv_snake(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, S_FIELD)
    for i in range(14):
        p = (t * 3 - i * 7) % 230 - 25
        if 0 <= p <= PV_W - 7:
            sy = y + 36 + int(22 * math.sin((t * 3 - i * 7) * 0.035))
            fb.fill_rect(x + int(p), sy, 7, 7, SNAKE_COLS[min(i * 2, 24)])
    ax = x + 140
    r = 4 if (t // 6) % 2 else 3
    fb.ellipse(ax, y + 20, r, r, RED, True)
    fb.fill_rect(ax, y + 14, 2, 3, GREEN)


def pv_breakout(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    for row in range(4):
        for col in range(8):
            if (row * 8 + col + t // 20) % 7 != 0:
                fb.fill_rect(x + 3 + col * 22, y + 4 + row * 8, 20, 6, BR_FILL[row])
    bx = x + 6 + int(tri(t, 60) * 166)
    by = y + 38 + int(tri(t, 34) * 30)
    px = max(x, min(x + PV_W - 36, bx - 16))
    fb.fill_rect(px, y + PV_H - 6, 36, 4, CYAN)
    fb.fill_rect(bx, by, 4, 4, WHITE)


def pv_flappy(fb, x, y, t):
    for yy in range(PV_H):
        fb.hline(x, y + yy, PV_W, SKY[yy * 2])
    for i in range(2):
        px = x + (i * 100 - t * 2) % 200 - 20
        gy = y + 30 + (12 if i else -6)
        draw_pipe(fb, px, gy, x, x + PV_W, y, y + PV_H - 8, 34, 20)
    fb.fill_rect(x, y + PV_H - 8, PV_W, 8, GROUND_COL)
    fb.fill_rect(x, y + PV_H - 8, PV_W, 2, GRASS)
    draw_bird(fb, x + 50, y + 30 + int(8 * math.sin(t * 0.18)), (t // 4) % 2 == 0)


PV_STACK = ((0, 6, 3), (1, 6, 3), (2, 6, 5), (3, 6, 1), (4, 6, 1), (6, 6, 2),
            (7, 6, 4), (8, 6, 4), (9, 6, 6), (0, 5, 3), (1, 5, 5), (6, 5, 2),
            (7, 5, 2), (8, 5, 6), (9, 5, 6), (0, 4, 0), (9, 4, 6))


def pv_tetris(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, T_BOARD_BG)
    ox = x + 35
    for cx, cy, ci in PV_STACK:
        t_cell(fb, ox + cx * 11, y + cy * 11 + 1, ci)
    fy = (t // 4) % 6
    for cx, cy in SHAPES[2]:
        if fy + cy >= 0:
            t_cell(fb, ox + (4 + cx) * 11, y + (fy + cy) * 11 + 1, 2)


def pv_dino(fb, x, y, t):
    for yy in range(PV_H):
        fb.hline(x, y + yy, PV_W, NIGHT[yy * 2])
    gy = y + PV_H - 8
    fb.fill_rect(x, gy, PV_W, 8, rgb(25, 20, 40))
    fb.hline(x, gy, PV_W, GRAY)
    cx = x + PV_W - (t * 4) % (PV_W + 30)
    if x <= cx <= x + PV_W - 8:
        fb.fill_rect(cx, gy - 22, 6, 22, CACTUS_COL)
        fb.fill_rect(cx - 3, gy - 14, 3, 3, CACTUS_COL)
        fb.fill_rect(cx + 6, gy - 10, 3, 3, CACTUS_COL)
    # hoppa när kaktusen närmar sig
    dist = cx - (x + 30)
    h = 0
    if -10 < dist < 40:
        p = (dist + 10) / 50
        h = int(30 * math.sin(p * math.pi))
    draw_dino(fb, x + 30, gy - 24 - h, t, h > 0)


def pv_simon(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    lit = (t // 10) % 4
    order = (0, 3, 1, 2)
    for k in range(4):
        sx, sy = SIMON_POS[k]
        bx = x + 30 + (64 if sx > 100 else 0)
        by = y + 4 + (37 if sy > 100 else 0)
        on = order[lit] == k
        fb.fill_rect(bx, by, 56, 32, SIMON_ON[k] if on else SIMON_OFF[k])


def pv_keys(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    lit = (t // 12) % 4
    for i in range(4):
        bx = x + 10 + i * 42
        on = i == lit
        fb.fill_rect(bx, y + 22, 34, 34, MAGENTA if on else rgb(30, 30, 60))
        fb.rect(bx, y + 22, 34, 34, WHITE if on else DIM)
        center_text(fb, str(i), y + 31, BG if on else GRAY, 2, cx=bx + 17)


# ---------------------------------------------------------------
# STÅENDE LÄGE (240x320). Skärmen vrids och man ställer in vilken
# knapp som är vänster och höger första gången.
# ---------------------------------------------------------------
GRAD_V = [lerp_col((8, 8, 40), (45, 0, 60), y / (VH - 1)) for y in range(VH)]


def draw_gradient_v(lcd):
    fb = lcd.pfb
    for y in range(VH):
        fb.hline(0, y, VW, GRAD_V[y])


def vtext(fb, s, y, c, scale=1):
    center_text(fb, s, y, c, scale, VW // 2)


def vshadow(fb, s, y, c, scale):
    shadow_text(fb, s, y, c, scale, VW // 2)


def v_calibrate(lcd, keys):
    """Frågar efter vänster- och högerknapp. False = gick ur."""
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    lcd.set_bg(draw_gradient_v)
    got = []
    t = 0
    keys.wait_release()
    while len(got) < 2:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return False
        for k in range(4):
            if keys.pressed(k) and k not in got:
                got.append(k)
                break
        lcd.load_bg()
        stars.draw(fb)
        vshadow(fb, "STAENDE", 18, CYAN, 3)
        vtext(fb, "Hall skarmen sa att", 60, WHITE)
        vtext(fb, "pilen pekar uppat", 72, WHITE)
        bob = int(4 * math.sin(t * 0.2))
        for i in range(18):
            fb.hline(120 - i, 96 + i + bob, 2 * i + 1, YELLOW)
        fb.fill_rect(111, 114 + bob, 19, 40, YELLOW)
        vtext(fb, "Tryck pa knappen", 190, WHITE)
        side = "VANSTER" if not got else "HOGER"
        vtext(fb, "som sitter till", 202, WHITE)
        vshadow(fb, side, 222, YELLOW, 3)
        if (t // 8) % 2 == 0:
            if not got:
                big_text(fb, "<", 8, 264, YELLOW, 4)
            else:
                big_text(fb, ">", VW - 40, 264, YELLOW, 4)
        if got:
            vtext(fb, "Vanster = KEY%d" % got[0], 300, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)
    SCORES["_vl"], SCORES["_vr"] = got[0], got[1]
    save_scores()
    return True


def v_start(lcd, keys, title, col, lines, key, L, R):
    """Startskärm. Returnerar 'go', 'exit' eller 'calib'."""
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    lcd.set_bg(draw_gradient_v)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return "exit"
        if TWO_KEYS:
            if keys.tapped[0] or keys.tapped[1]:
                return "go"
        elif keys.pressed(L) or keys.pressed(R):
            return "go"
        for k in range(4):
            if k != L and k != R and keys.pressed(k):
                return "calib"
        lcd.load_bg()
        stars.draw(fb)
        dy = int(4 * math.sin(t * 0.15))
        vshadow(fb, title, 40 + dy, col, 4)
        for i, line in enumerate(lines):
            vtext(fb, line, 110 + i * 14, WHITE)
        vtext(fb, "Rekord: %d" % SCORES.get(key, 0), 200, col)
        if (t // 10) % 2 == 0:
            vtext(fb, "Tryck %d eller %d" % (L, R), 240, YELLOW, 2)
        vtext(fb, "%d = vanster   %d = hoger" % (L, R), 270, GRAY)
        if not TWO_KEYS:
            vtext(fb, "Annan knapp: stall in", 290, DIM)
        vtext(fb, "%s: tillbaka" % ("Hall 0+1" if TWO_KEYS else "Alla 4"), 304, DIM)
        lcd.show()
        t += 1
        frame_wait(t0)


def v_result(lcd, keys, key, score, col, L, R):
    """Slutskärm. True = spela igen."""
    info, new = record_info(key, score)
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    lcd.set_bg(draw_gradient_v)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 10:
            if TWO_KEYS:
                again = L < 2 and keys.tapped[L]
                leave = R < 2 and keys.tapped[R]
            else:
                again, leave = keys.pressed(L), keys.pressed(R)
            if again:
                return True
            if leave or keys.exit_requested():
                return False
        lcd.load_bg()
        stars.draw(fb)
        if new:
            for _ in range(40):
                fb.fill_rect(random.randint(0, VW - 3), random.randint(0, VH - 3),
                             3, 3, random.choice(RAINBOW))
        dy = int(4 * math.sin(t * 0.2))
        vshadow(fb, "GAME", 40 + dy, col, 4)
        vshadow(fb, "OVER", 80 + dy, col, 4)
        vtext(fb, str(score), 140, WHITE, 5)
        if new:
            if (t // 8) % 2 == 0:
                vtext(fb, info, 200, YELLOW, 2)
        else:
            vtext(fb, info, 204, GRAY)
        vtext(fb, "%d: spela igen" % L, 260, WHITE)
        vtext(fb, "%d: till menyn" % R, 276, WHITE)
        lcd.show()
        t += 1
        frame_wait(t0)


def v_game(lcd, keys, title, col, lines, key, play):
    """Kör ett stående spel från start till slut."""
    lcd.portrait()
    try:
        if "_vl" not in SCORES and not v_calibrate(lcd, keys):
            return
        while True:
            L, R = SCORES["_vl"], SCORES["_vr"]
            r = v_start(lcd, keys, title, col, lines, key, L, R)
            if r == "exit":
                return
            if r == "calib":
                if not v_calibrate(lcd, keys):
                    return
                continue
            while True:
                score = play(lcd, keys, L, R)
                if score is None:
                    return
                if not v_result(lcd, keys, key, score, col, L, R):
                    return
    finally:
        lcd.landscape()


# ---------------------------------------------------------------
# Stående spel: RUNNER (springa längs en väg i 3 filer)
# ---------------------------------------------------------------
HZ = 96                     # horisonten
FOC = 224.0                 # y = HZ + FOC / z  (z = avstånd)
LANE_DX = 74.0
RUN_PZ = 1.25               # spelarens avstånd
RUN_PY = int(HZ + FOC / RUN_PZ)
RUN_Z = [FOC / (y - HZ) for y in range(HZ + 1, VH)]
RUN_HW = [int(110 / z) for z in RUN_Z]
RUN_DIV = [int(LANE_DX / 2 / z) for z in RUN_Z]
RUN_LW = [max(1, int(3 / z)) for z in RUN_Z]
ROAD_A, ROAD_B = rgb(70, 62, 60), rgb(82, 74, 70)
GRASS_A, GRASS_B = rgb(30, 100, 50), rgb(40, 120, 60)
RUMBLE_A, RUMBLE_B = rgb(230, 60, 60), WHITE
SUNSET = [lerp_col((40, 20, 90), (255, 150, 90), y / HZ) for y in range(HZ + 1)]
SKIN = rgb(255, 200, 150)


def runner_bg(lcd):
    fb = lcd.pfb
    for y in range(HZ + 1):
        fb.hline(0, y, VW, SUNSET[y])
    fb.ellipse(120, HZ - 4, 26, 26, rgb(255, 230, 120), True)
    mcol = rgb(70, 40, 90)
    for x in range(VW):
        h = int(16 + 9 * math.sin(x * 0.045) + 6 * math.sin(x * 0.13 + 1))
        fb.vline(x, HZ - h, h + 1, mcol)
    # Tempelpelare vid horisonten
    for px in (30, 196):
        fb.fill_rect(px, HZ - 40, 14, 40, rgb(150, 110, 80))
        fb.fill_rect(px - 3, HZ - 44, 20, 5, rgb(180, 140, 100))


@native
def draw_road(fb, travel):
    n = len(RUN_Z)
    for i in range(n):
        y = HZ + 1 + i
        s = int((RUN_Z[i] + travel) * 1.4) & 1
        hw = RUN_HW[i]
        rw = hw // 7 + 1
        fb.hline(0, y, VW, GRASS_A if s else GRASS_B)
        fb.hline(120 - hw - rw, y, 2 * (hw + rw), RUMBLE_A if s else RUMBLE_B)
        fb.hline(120 - hw, y, 2 * hw, ROAD_A if s else ROAD_B)
        if s:
            d = RUN_DIV[i]
            lw = RUN_LW[i]
            fb.hline(120 - d - lw // 2, y, lw, WHITE)
            fb.hline(120 + d - lw // 2, y, lw, WHITE)


def draw_run_obj(fb, o, t):
    z = o[1]
    if z < 0.7:
        return
    s = 1 / z
    y = int(HZ + FOC / z)
    x = int(120 + o[0] * LANE_DX / z)
    if o[2] == 0:                       # hinder
        w = max(2, int(62 * s))
        h = max(2, int(34 * s))
        fb.fill_rect(x - w // 2, y - h, w, h, RUMBLE_A)
        b = max(1, h // 5)
        fb.fill_rect(x - w // 2, y - h + b, w, b, WHITE)
        fb.fill_rect(x - w // 2, y - h + 3 * b, w, b, WHITE)
        fb.fill_rect(x - w // 2, y - 2, max(1, w // 8), 2, BLACK)
        fb.fill_rect(x + w // 2 - max(1, w // 8), y - 2, max(1, w // 8), 2, BLACK)
    else:                               # mynt
        r = max(1, int(11 * s))
        rx = max(1, int(r * abs(math.sin(t * 0.15 + z))))
        cy = y - int(26 * s)
        fb.ellipse(x, cy, rx, r, YELLOW, True)
        if rx > 2:
            fb.ellipse(x, cy, max(1, rx // 2), max(1, r // 2), ORANGE, True)


def draw_runner(fb, x, t):
    y = RUN_PY
    fb.ellipse(x, y, 14, 4, rgb(30, 30, 30), True)
    leg = (t // 3) % 2
    fb.fill_rect(x - 6, y - 14, 4, 12 if leg else 8, BLUE)
    fb.fill_rect(x + 2, y - 14, 4, 8 if leg else 12, BLUE)
    fb.fill_rect(x - 7, y - 32, 14, 19, CYAN)
    fb.fill_rect(x - 10, y - 30 + (3 if leg else 0), 3, 10, SKIN)
    fb.fill_rect(x + 7, y - 30 + (0 if leg else 3), 3, 10, SKIN)
    fb.ellipse(x, y - 39, 7, 7, SKIN, True)
    fb.fill_rect(x - 7, y - 47, 14, 4, rgb(120, 60, 30))


def play_runner(lcd, keys, L, R):
    fb = lcd.pfb
    lane = 0
    px = 120.0
    obs = []          # [fil, z, typ, passerad]
    dist = 0.0
    speed = 0.12
    coins = 0
    next_row = 3.0
    t = 0
    lcd.set_bg(runner_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return None
        if keys.pressed(L):
            lane = max(-1, lane - 1)
        if keys.pressed(R):
            lane = min(1, lane + 1)
        px += (120 + lane * LANE_DX / RUN_PZ - px) * 0.45

        speed = min(0.12 + dist * 0.0009, 0.34)
        dist += speed
        next_row -= speed
        if next_row <= 0:
            next_row = random.uniform(4.0, 6.5)
            lanes = [-1, 0, 1]
            for _ in range(random.choice((1, 1, 2))):
                obs.append([lanes.pop(random.randint(0, len(lanes) - 1)), 22.0, 0, False])
            if random.random() < 0.7:
                obs.append([random.choice(lanes), 22.0, 1, False])

        crashed = False
        for o in obs:
            o[1] -= speed
            if not o[3] and o[1] <= RUN_PZ:
                o[3] = True
                if o[0] == lane:
                    if o[2] == 0:
                        crashed = True
                    else:
                        coins += 1
                        o[1] = -1
        obs = [o for o in obs if o[1] > 0.6]

        lcd.load_bg()
        draw_road(fb, dist)
        obs.sort(key=lambda o: -o[1])
        for o in obs:
            if o[1] > RUN_PZ:
                draw_run_obj(fb, o, t)
        draw_runner(fb, int(px), t)
        for o in obs:
            if o[1] <= RUN_PZ:
                draw_run_obj(fb, o, t)
        score = int(dist * 10) + coins * 25
        big_text(fb, str(score), 6, 6, WHITE, 2)
        fb.ellipse(VW - 40, 13, 6, 6, YELLOW, True)
        fb.text("%d" % coins, VW - 30, 9, WHITE)
        if t < 60 and (t // 10) % 2 == 0:
            vtext(fb, "%d <      > %d" % (L, R), 150, WHITE, 2)
        lcd.show()
        if crashed:
            for k in range(6):
                fb.rect(0, 0, VW, VH, RED if k % 2 == 0 else WHITE)
                fb.rect(1, 1, VW - 2, VH - 2, RED if k % 2 == 0 else WHITE)
                lcd.show()
                time.sleep_ms(80)
            return score
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Stående spel: SPACE (rymdskjutare)
# ---------------------------------------------------------------
SHIP_Y = 292


def draw_ship(fb, x, t):
    fb.fill_rect(x - 2, SHIP_Y - 14, 4, 18, WHITE)
    fb.fill_rect(x - 6, SHIP_Y - 4, 12, 6, CYAN)
    fb.fill_rect(x - 12, SHIP_Y, 24, 4, CYAN)
    fb.fill_rect(x - 12, SHIP_Y - 4, 3, 8, BLUE)
    fb.fill_rect(x + 9, SHIP_Y - 4, 3, 8, BLUE)
    fb.fill_rect(x - 1, SHIP_Y - 8, 2, 3, RED)
    fl = 4 + (t % 3) * 2
    fb.fill_rect(x - 3, SHIP_Y + 4, 6, fl, ORANGE)
    fb.fill_rect(x - 1, SHIP_Y + 4, 2, fl + 3, YELLOW)


def draw_alien(fb, e, t):
    x, y = int(e[0]), int(e[1])
    if e[4] == 0:
        fb.fill_rect(x - 8, y - 5, 16, 9, GREEN)
        fb.fill_rect(x - 5, y - 2, 3, 3, BG)
        fb.fill_rect(x + 2, y - 2, 3, 3, BG)
        fb.fill_rect(x - 6, y - 8, 2, 3, GREEN)
        fb.fill_rect(x + 4, y - 8, 2, 3, GREEN)
        if (t // 8) % 2:
            fb.fill_rect(x - 8, y + 4, 3, 4, GREEN)
            fb.fill_rect(x + 5, y + 4, 3, 4, GREEN)
        else:
            fb.fill_rect(x - 5, y + 4, 3, 4, GREEN)
            fb.fill_rect(x + 2, y + 4, 3, 4, GREEN)
    else:
        fb.ellipse(x, y, 14, 9, PURPLE, True)
        fb.ellipse(x, y - 2, 5, 5, WHITE, True)
        fb.fill_rect(x - 1, y - 3, 3, 3, BG)
        for i in range(e[3]):
            fb.fill_rect(x - 8 + i * 6, y + 11, 4, 2, RED)


def play_space(lcd, keys, L, R):
    fb = lcd.pfb
    x = 120.0
    bullets = []
    enemies = []      # [x, y, fas, liv, typ]
    shots = []
    parts = []
    stars = [[random.randint(0, VW - 1), random.randint(0, VH - 1), random.randint(1, 3)]
             for _ in range(40)]
    lives = 3
    inv = 60
    score = 0
    spawn = 30
    t = 0
    keys.wait_release()

    def boom(ex, ey, col):
        for _ in range(10):
            if len(parts) < 80:
                parts.append([ex, ey, random.uniform(-3, 3), random.uniform(-3, 3),
                              14, col])

    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return None
        if keys.held(L):
            x -= 5
        if keys.held(R):
            x += 5
        x = max(14, min(VW - 14, x))
        if t % 7 == 0:
            bullets.append([x, SHIP_Y - 16])

        spawn -= 1
        if spawn <= 0:
            spawn = max(14, 42 - score // 60)
            kind = 1 if random.random() < 0.2 else 0
            enemies.append([random.uniform(20, VW - 20), -14, random.uniform(0, 6.3),
                            3 if kind else 1, kind])
        fall = min(1.2 + score / 2500, 3.0)

        for b in bullets:
            b[1] -= 10
        bullets = [b for b in bullets if b[1] > -10]
        for e in enemies:
            e[1] += fall * (0.7 if e[4] else 1.0)
            e[0] += math.sin(e[1] * 0.04 + e[2]) * 1.6
            e[0] = max(14, min(VW - 14, e[0]))
            if random.random() < (0.012 if e[4] else 0.005):
                shots.append([e[0], e[1] + 10])
        for s in shots:
            s[1] += 4.5
        shots = [s for s in shots if s[1] < VH + 5]

        # Träffar
        for b in bullets:
            for e in enemies:
                if e[3] > 0 and abs(b[0] - e[0]) < (14 if e[4] else 10) \
                        and abs(b[1] - e[1]) < 10:
                    e[3] -= 1
                    b[1] = -100
                    if e[3] <= 0:
                        score += 50 if e[4] else 10
                        boom(e[0], e[1], PURPLE if e[4] else GREEN)
                    break
        enemies = [e for e in enemies if e[3] > 0 and e[1] < VH + 20]

        if inv > 0:
            inv -= 1
        else:
            hit = False
            for e in enemies:
                if abs(e[0] - x) < 16 and abs(e[1] - SHIP_Y) < 12:
                    e[3] = 0
                    hit = True
            for s in shots:
                if abs(s[0] - x) < 10 and SHIP_Y - 14 < s[1] < SHIP_Y + 6:
                    s[1] = VH + 50
                    hit = True
            if hit:
                lives -= 1
                inv = 60
                boom(x, SHIP_Y, ORANGE)
                if lives <= 0:
                    for _ in range(20):
                        fb.fill(BG)
                        for p in parts:
                            p[0] += p[2]
                            p[1] += p[3]
                            fb.fill_rect(int(p[0]), int(p[1]), 3, 3, p[5])
                        lcd.show()
                        time.sleep_ms(30)
                    return score

        # --- Rita ---
        fb.fill(BG)
        for st in stars:
            st[1] += st[2]
            if st[1] >= VH:
                st[1] = 0
                st[0] = random.randint(0, VW - 1)
            if st[2] == 3:
                fb.vline(st[0], st[1], 3, STAR_COLS[2])
            else:
                fb.pixel(st[0], st[1], STAR_COLS[st[2] - 1])
        for e in enemies:
            draw_alien(fb, e, t)
        for b in bullets:
            fb.fill_rect(int(b[0]) - 1, int(b[1]), 2, 7, YELLOW)
        for s in shots:
            fb.fill_rect(int(s[0]) - 2, int(s[1]), 4, 4, RED)
        for p in parts[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                parts.remove(p)
            else:
                fb.fill_rect(int(p[0]), int(p[1]), 2, 2, p[5])
        if inv == 0 or (t // 4) % 2 == 0:
            draw_ship(fb, int(x), t)
        big_text(fb, str(score), 6, 6, WHITE, 2)
        for i in range(lives):
            fb.fill_rect(VW - 16 - i * 14, 8, 10, 8, CYAN)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Stående spel: STACK (bygg ett så högt torn som möjligt)
# ---------------------------------------------------------------
ST_BH = 14
ST_BASE = 300


def _hue(h):
    h = h % 1.0
    i = int(h * 6)
    f = h * 6 - i
    v, p = 1.0, 0.25
    q = 1 - 0.75 * f
    tt = 0.25 + 0.75 * f
    r, g, b = ((v, tt, p), (q, v, p), (p, v, tt), (p, q, v), (tt, p, v), (v, p, q))[i % 6]
    return (int(r * 255), int(g * 255), int(b * 255))


ST_COLS = [(rgb(*_hue(i / 30)), lerp_col(_hue(i / 30), (255, 255, 255), 0.45),
            lerp_col(_hue(i / 30), (0, 0, 0), 0.35)) for i in range(30)]


def st_block(fb, x, y, w, ci):
    if w <= 0:
        return
    c, light, dark = ST_COLS[ci % 30]
    fb.fill_rect(x, y, w, ST_BH, c)
    fb.hline(x, y, w, light)
    fb.hline(x, y + ST_BH - 1, w, dark)


def play_stack(lcd, keys, L, R):
    fb = lcd.pfb
    blocks = [[70, 100]]      # [x, bredd]
    cx, cw = 0.0, 100
    vx = 2.6
    falling = []              # [x, y, w, vy, färg]
    cam = 0.0
    combo = 0
    flash = 0
    t = 0
    lcd.set_bg(draw_gradient_v)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.exit_requested():
            return None
        n = len(blocks)
        cx += vx
        if cx < 0:
            cx = 0
            vx = -vx
        elif cx + cw > VW:
            cx = VW - cw
            vx = -vx

        place = False
        for k in range(4):
            if keys.pressed(k):
                place = True
        if place:
            px, pw = blocks[-1]
            ix = int(cx)
            if abs(ix - px) <= 3:
                ix = px
                combo += 1
                flash = 8
            else:
                combo = 0
            left = max(ix, px)
            right = min(ix + cw, px + pw)
            ov = right - left
            y_now = ST_BASE - n * ST_BH
            if ov <= 0:
                falling.append([ix, y_now, cw, 0.0, n])
                for _ in range(40):
                    t1 = time.ticks_ms()
                    draw_stack(fb, lcd, blocks, None, 0, falling, cam, n - 1, 0)
                    lcd.show()
                    frame_wait(t1)
                return n - 1
            if ix < left:
                falling.append([ix, y_now, left - ix, 0.0, n])
            if ix + cw > right:
                falling.append([right, y_now, ix + cw - right, 0.0, n])
            if combo >= 3 and ov < 100:
                ov = min(100, ov + 6)           # belöning: blocket växer
                left = max(0, min(VW - ov, left - 3))
            blocks.append([left, ov])
            cw = ov
            speed = min(2.6 + len(blocks) * 0.12, 7.0)
            if len(blocks) % 2:
                cx, vx = 0.0, speed
            else:
                cx, vx = float(VW - cw), -speed

        for f in falling:
            f[3] += 0.5
            f[1] += f[3]
        falling = [f for f in falling if f[1] + cam * ST_BH < VH + 20]
        target = max(0, len(blocks) - 14)
        cam += (target - cam) * 0.15
        draw_stack(fb, lcd, blocks, cx, cw, falling, cam, len(blocks) - 1, flash)
        if flash > 0:
            flash -= 1
        if t < 60 and (t // 10) % 2 == 0:
            vtext(fb, "Tryck for att slappa", 150, WHITE)
        lcd.show()
        t += 1
        frame_wait(t0)


def draw_stack(fb, lcd, blocks, cx, cw, falling, cam, score, flash):
    lcd.load_bg()
    off = int(cam * ST_BH)
    n = len(blocks)
    for i in range(n):
        y = ST_BASE - i * ST_BH + off
        if -ST_BH < y < VH:
            st_block(fb, blocks[i][0], y, blocks[i][1], i)
    if flash > 0 and n > 1:
        y = ST_BASE - (n - 1) * ST_BH + off
        fb.rect(blocks[-1][0] - 2, y - 2, blocks[-1][1] + 4, ST_BH + 4, WHITE)
    if cx is not None:
        st_block(fb, int(cx), ST_BASE - n * ST_BH + off, cw, n)
    for f in falling:
        st_block(fb, int(f[0]), int(f[1]) + off, f[2], f[4])
    if ST_BASE + off < VH:
        fb.fill_rect(0, ST_BASE + ST_BH + off, VW, VH, rgb(30, 25, 50))
    vshadow(fb, str(score), 20, WHITE, 5)


def game_runner(lcd, keys):
    v_game(lcd, keys, "RUNNER", ORANGE,
           ("Spring och byt fil", "med vanster/hoger.", "",
            "Ta mynten och", "undvik hindren!"), "runner", play_runner)


def game_space(lcd, keys):
    v_game(lcd, keys, "SPACE", CYAN,
           ("Flytta skeppet med", "vanster/hoger.", "",
            "Skeppet skjuter", "av sig sjalvt!"), "space", play_space)


def game_stack(lcd, keys):
    v_game(lcd, keys, "STACK", YELLOW,
           ("Tryck nar blocket", "ligger over tornet.", "",
            "Perfekt 3 ganger", "i rad = storre block"), "stack", play_stack)


# Förhandsvisningar av de stående spelen (på startsidans kort)
def pv_runner(fb, x, y, t):
    for yy in range(22):
        fb.hline(x, y + yy, PV_W, SUNSET[yy * 4])
    fb.ellipse(x + 90, y + 20, 10, 10, rgb(255, 230, 120), True)
    for i in range(56):
        yy = y + 22 + i
        z = 56.0 / (i + 1)
        s = int((z + t * 0.3) * 1.4) & 1
        hw = int(70 / z) + 4
        fb.hline(x, yy, PV_W, GRASS_A if s else GRASS_B)
        fb.hline(x + 90 - hw, yy, 2 * hw, ROAD_A if s else ROAD_B)
    lane = int(math.sin(t * 0.05) * 1.5)
    rx = x + 90 + lane * 22
    fb.fill_rect(rx - 4, y + 52, 8, 12, CYAN)
    fb.ellipse(rx, y + 48, 4, 4, SKIN, True)
    fb.fill_rect(rx - 4, y + 64, 3, 6 if (t // 3) % 2 else 3, BLUE)
    fb.fill_rect(rx + 1, y + 64, 3, 3 if (t // 3) % 2 else 6, BLUE)


def pv_space(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    for i in range(20):
        fb.pixel(x + (i * 53) % PV_W, y + (i * 29 + t * (1 + i % 3)) % PV_H, STAR_COLS[i % 3])
    for i in range(5):
        ex = x + 20 + i * 34
        ey = y + 12 + int(4 * math.sin(t * 0.1 + i))
        fb.fill_rect(ex - 6, ey - 4, 12, 8, GREEN if i % 2 else PURPLE)
    sx = x + 20 + int(tri(t, 90) * 140)
    fb.fill_rect(sx - 2, y + 58, 4, 12, WHITE)
    fb.fill_rect(sx - 9, y + 66, 18, 4, CYAN)
    for k in range(3):
        by = y + 52 - ((t * 6 + k * 18) % 50)
        fb.fill_rect(sx - 1, by, 2, 5, YELLOW)


def pv_stack(fb, x, y, t):
    for yy in range(PV_H):
        fb.hline(x, y + yy, PV_W, GRAD_V[yy * 3])
    w = 70
    for i in range(5):
        bx = x + 55 + int(4 * math.sin(i * 1.7))
        c = ST_COLS[i * 3][0]
        fb.fill_rect(bx, y + PV_H - 12 - i * 12, w - i * 4, 11, c)
    mx = x + int(tri(t, 80) * (PV_W - 50))
    fb.fill_rect(mx, y + PV_H - 12 - 5 * 12 - 2, 50, 11, ST_COLS[15][0])


# ---------------------------------------------------------------
# KLOCKA. Visas på startsidan när ingen har tryckt på något en stund.
# Thonny ställer Picons klocka automatiskt när den är inkopplad till
# datorn. Annars frågar programmet efter tiden vid start (går att
# hoppa över, då finns ingen klocka).
# ---------------------------------------------------------------
IDLE_MS = 45_000            # visa klockan efter 45 s utan knapptryck
CLOCK = {"on": False}
_rtc = machine.RTC()


def clock_valid():
    return _rtc.datetime()[0] >= 2024


def set_clock(h, m):
    _rtc.datetime((2025, 1, 1, 2, h, m, 0, 0))
    CLOCK["on"] = True


def time_setup(lcd, keys):
    """Ställ in timme och minut. B hoppar över (ingen klocka)."""
    d = _rtc.datetime()
    hm = [d[4], d[5]]
    field = 0
    stars = Stars(40)
    lcd.set_bg(draw_gradient)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.back() or keys.exit_requested():
            return False
        lim = 24 if field == 0 else 60
        if keys.step(K_Y):
            hm[field] = (hm[field] + 1) % lim
        if keys.step(K_X):
            hm[field] = (hm[field] - 1) % lim
        if keys.sel():
            if field == 0:
                field = 1
            else:
                set_clock(hm[0], hm[1])
                return True
        lcd.load_bg()
        stars.draw(lcd)
        shadow_text(lcd, "VAD AR KLOCKAN?", 16, CYAN, 2)
        x0 = (W - text_w("00:00", 6)) // 2
        for i, txt in enumerate(("%02d" % hm[0], ":", "%02d" % hm[1])):
            x = x0 + (0, 96, 144)[i]
            sel = (i == 0 and field == 0) or (i == 2 and field == 1)
            if sel:
                lcd.fill_rect(x - 4, 66, 104, 60, DIM)
            col = YELLOW if sel else WHITE
            if not (sel and (t // 8) % 4 == 3):
                big_text(lcd, txt, x, 72, col, 6)
        center_text(lcd, "%d: minus   %d: plus" % (K_X, K_Y), 150, WHITE)
        center_text(lcd, "%s: %s" % (SEL_TXT, "nasta" if field == 0 else "klar!"), 166, WHITE)
        center_text(lcd, "%s: hoppa over (ingen klocka)"
                    % ("Hall 0+1" if TWO_KEYS else str(K_B)), 196, GRAY)
        center_text(lcd, "Tips: med Thonny stalls den sjalv", 222, DIM)
        lcd.show()
        t += 1
        frame_wait(t0)


def show_clock(lcd, keys):
    """Klockskärm tills någon trycker på en knapp."""
    stars = Stars(40)
    lcd.set_bg(draw_gradient)
    lcd.backlight(40)
    keys.wait_release()
    t = 0
    try:
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.any_held():
                keys.wait_release()
                return
            d = _rtc.datetime()
            h, m, s = d[4], d[5], d[6]
            lcd.load_bg()
            stars.draw(lcd, 0.5)
            dy = int(6 * math.sin(t * 0.03))
            txt = "%02d%s%02d" % (h, ":" if s % 2 == 0 else " ", m)
            x = (W - text_w(txt, 7)) // 2
            for i, ch in enumerate(txt):
                big_text(lcd, ch, x + 4, 70 + dy + 4, SHADOW, 7)
                big_text(lcd, ch, x, 70 + dy, RAINBOW[(i * 2 + t // 6) % len(RAINBOW)], 7)
                x += 56
            lcd.fill_rect(40, 150 + dy, 240, 4, DIM)
            lcd.fill_rect(40, 150 + dy, s * 4, 4, CYAN)
            center_text(lcd, "Tryck pa en knapp for att spela", 216, GRAY)
            lcd.show()
            t += 1
            frame_wait(t0)
    finally:
        lcd.backlight(100)


def game_clock(lcd, keys):
    if time_setup(lcd, keys):
        show_clock(lcd, keys)


def pv_clock(fb, x, y, t):
    fb.fill_rect(x, y, PV_W, PV_H, BG)
    if CLOCK["on"]:
        d = _rtc.datetime()
        txt = "%02d:%02d" % (d[4], d[5])
    else:
        txt = "--:--"
    center_text(fb, txt, y + 24, RAINBOW[(t // 6) % len(RAINBOW)], 4, cx=x + PV_W // 2)


# (namn, beskrivning, rekordnyckel, färg, förhandsvisning, starta, stående?)
GAMES = (
    ("PONG", "Mot datorn/en kompis", "pong", CYAN, pv_pong, game_pong, False),
    ("SNAKE", "Styr med %d och %d" % (SNAKE_LEFT, SNAKE_RIGHT), "snake", GREEN, pv_snake, game_snake, False),
    ("BREAKOUT", "Krossa alla stenar", "breakout", ORANGE, pv_breakout, game_breakout, False),
    ("FLAPPY", "Flyg mellan roren", "flappy", YELLOW, pv_flappy, game_flappy, False),
    ("TETRIS", "Fyll hela rader", "tetris", BLUE, pv_tetris, game_tetris, False),
    ("DINO", "Hoppa over kaktusar", "dino", GREEN, pv_dino, game_dino, False),
    ("SIMON", "Minns ordningen", "simon", RED, pv_simon, game_simon, False),
    ("RUNNER", "Spring, byt fil", "runner", ORANGE, pv_runner, game_runner, True),
    ("SPACE", "Skjut ner rymdvarelser", "space", CYAN, pv_space, game_space, True),
    ("STACK", "Bygg ett hogt torn", "stack", YELLOW, pv_stack, game_stack, True),
    ("KLOCKA", "Stall in klockan", None, BLUE, pv_clock, game_clock, False),
    ("KNAPPTEST", "Hitta dina knappar", None, MAGENTA, pv_keys, game_keytest, False),
)


# ---------------------------------------------------------------
# Startsida
# ---------------------------------------------------------------
CARD_X, CARD_Y, CARD_W, CARD_H = 60, 50, 200, 146


def draw_card(fb, g, x, t):
    name, desc, key, accent, preview, _, upright = g
    y = CARD_Y
    fb.fill_rect(x + 5, y + 5, CARD_W, CARD_H, SHADOW)
    fb.fill_rect(x, y, CARD_W, CARD_H, BG)
    fb.rect(x, y, CARD_W, CARD_H, accent)
    fb.rect(x + 1, y + 1, CARD_W - 2, CARD_H - 2, accent)
    preview(fb, x + 10, y + 10, t)
    fb.rect(x + 9, y + 9, PV_W + 2, PV_H + 2, DIM)
    cx = x + CARD_W // 2
    center_text(fb, name, y + 96, WHITE, 2, cx=cx)
    center_text(fb, desc, y + 118, GRAY, 1, cx=cx)
    line = ""
    if key == "pong":
        if key in SCORES:
            line = "Storsta vinst: +%d" % SCORES[key]
    elif key:
        line = "Rekord: %d" % SCORES.get(key, 0)
    if line:
        center_text(fb, line, y + 131, accent, 1, cx=cx)
    if upright:                      # märke för stående spel
        fb.fill_rect(x + CARD_W - 76, y - 7, 72, 14, accent)
        fb.text("STAENDE", x + CARD_W - 68, y - 3, BG)


def run_menu(lcd, keys, sel=0):
    stars = Stars(60)
    lcd.set_bg(draw_gradient)
    t = 0
    off = 0          # förskjutning när ett nytt kort glider in
    hint = "%d/%d: bladdra     %s: spela" % (K_X, K_Y, SEL_TXT)
    keys.wait_release()
    last_key = time.ticks_ms()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.any_held():
            last_key = t0
        elif CLOCK["on"] and time.ticks_diff(t0, last_key) > IDLE_MS:
            show_clock(lcd, keys)
            lcd.set_bg(draw_gradient)
            last_key = time.ticks_ms()
            continue
        if keys.prev_():
            sel = (sel - 1) % len(GAMES)
            off = -W
        if keys.next_():
            sel = (sel + 1) % len(GAMES)
            off = W
        if keys.sel():
            return sel
        if keys.exit_requested():
            machine.soft_reset()                 # tillbaka till startmenyn

        g = GAMES[sel]
        accent = g[3]
        lcd.load_bg()
        stars.draw(lcd, 1 + abs(off) / 25)
        wave_text(lcd, "PICO ARCADE", 10, 3, RAINBOW, t)

        draw_card(lcd, g, CARD_X + off, t)
        off = int(off * 0.55)

        bob = int(3 * math.sin(t * 0.25))
        big_text(lcd, "<", 18 - bob, 112, accent, 3)
        big_text(lcd, ">", W - 42 + bob, 112, accent, 3)

        n = len(GAMES)
        for i in range(n):
            dx = int(W // 2 + (i - (n - 1) / 2) * 16)
            if i == sel:
                lcd.fill_rect(dx - 4, 204, 8, 8, accent)
            else:
                lcd.fill_rect(dx - 2, 206, 4, 4, DIM)

        center_text(lcd, hint, 224, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Huvudprogram
# ---------------------------------------------------------------
def show_error(lcd, e):
    """Visar felet på skärmen så man ser vad som gick snett."""
    import sys
    import io
    sys.print_exception(e)
    if lcd is None:
        return
    buf = io.StringIO()
    sys.print_exception(e, buf)
    lcd.backlight(100)
    lcd.landscape()
    lcd.fill(rgb(120, 0, 0))
    lcd.text("FEL! Se Thonny-skalet", 4, 4, WHITE)
    y = 20
    for line in buf.getvalue().split("\n"):
        while line and y < H - 8:
            lcd.text(line[:39], 4, y, WHITE)
            line = line[39:]
            y += 10
    lcd.show()


def main():
    print("Pico Arcade startar...")
    if OVERCLOCK_HZ:
        try:
            machine.freq(OVERCLOCK_HZ)
        except Exception as e:
            print("Kunde inte overklocka:", e)
    print("CPU: %d MHz" % (machine.freq() // 1_000_000))
    lcd = None
    try:
        gc.collect()
        lcd = LCD()
        print("Skarm OK:", lcd.spi)
        if lcd.bg is None:
            print("Obs: inte minne till bakgrundsbuffert, kor lite langsammare")
        keys = Keys()
        _fps[1] = time.ticks_ms()
        if clock_valid():
            CLOCK["on"] = True           # Thonny har redan ställt klockan
            print("Klockan ar", "%02d:%02d" % _rtc.datetime()[4:6])
        else:
            time_setup(lcd, keys)
        sel = 0
        while True:
            sel = run_menu(lcd, keys, sel)
            gc.collect()
            try:
                GAMES[sel][5](lcd, keys)
            finally:
                lcd.landscape()
                lcd.backlight(100)
    except KeyboardInterrupt:
        print("Stoppad")
    except Exception as e:
        show_error(lcd, e)


main()
