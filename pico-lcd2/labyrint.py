# LABYRINT 3D
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Gå runt i en 3D-labyrint och hitta utgången. Varje nivå blir större.
# Samla mynt, hitta nyckeln (från nivå 3) och akta dig för spökena
# (från nivå 4).
#
# Styrning (bara KEY0 och KEY1 behövs):
#   håll 0       = sväng vänster
#   håll 1       = sväng höger
#   0+1 kort     = börja gå / stanna
#   håll 0+1     = paus / meny
#
# Kör med F5 i Thonny. Vill du att spelet startar av sig själv, lägg en
# main.py på Picon med raden: import labyrint
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
FRAME_MS = 40
SAVE_FILE = "labyrint.json"
LONG = 40                    # håll 0+1 så här många bilder = meny


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
BG = rgb(6, 6, 16)
YELLOW = rgb(255, 220, 40)
CYAN = rgb(0, 230, 255)
RED = rgb(255, 60, 80)
GREEN = rgb(80, 230, 110)
PURPLE = rgb(190, 80, 255)
SHADOW = rgb(30, 0, 50)


# ---------------------------------------------------------------
# Skärm och knappar
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
            return json.load(f)
    except Exception:
        return {"level": 1, "best": 0}


def store(save):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(save, f)
    except Exception:
        pass


# ---------------------------------------------------------------
# Grafik för labyrinten
# ---------------------------------------------------------------
NR = 80                      # antal strålar
CW = W // NR                 # bredd per stråle
FOG = (8, 6, 18)
NSH = 14                     # ljusnivåer
WALL_BASES = ((150, 140, 185), (190, 150, 110))   # vanlig vägg, kantvägg
# SHADES[typ][sida][nivå]
SHADES = []
for base in WALL_BASES:
    sides = []
    for side in (1.0, 0.72):
        lv = []
        for i in range(NSH):
            f = 1.0 / (1 + i * 0.55)
            c = (base[0] * side, base[1] * side, base[2] * side)
            lv.append(rgb(*lerp(FOG, c, f)))
        sides.append(lv)
    SHADES.append(sides)
CEIL = [rgb(*lerp((26, 22, 52), FOG, y / (H // 2))) for y in range(H // 2)]
FLOOR = [rgb(*lerp(FOG, (62, 48, 44), y / (H // 2))) for y in range(H // 2)]


def view_bg(lcd):
    for y in range(H // 2):
        lcd.hline(0, y, W, CEIL[y])
        lcd.hline(0, H // 2 + y, W, FLOOR[y])


@native
def cast(fb, m, mw, px, py, dx, dy, plx, ply, zbuf, mid):
    for c in range(NR):
        camx = 2.0 * c / NR - 1.0
        rdx = dx + plx * camx
        rdy = dy + ply * camx
        mx = int(px)
        my = int(py)
        ddx = abs(1.0 / rdx) if rdx != 0 else 1e9
        ddy = abs(1.0 / rdy) if rdy != 0 else 1e9
        if rdx < 0:
            sx = -1
            sdx = (px - mx) * ddx
        else:
            sx = 1
            sdx = (mx + 1.0 - px) * ddx
        if rdy < 0:
            sy = -1
            sdy = (py - my) * ddy
        else:
            sy = 1
            sdy = (my + 1.0 - py) * ddy
        side = 0
        hit = 0
        n = 0
        while hit == 0 and n < 64:
            if sdx < sdy:
                sdx += ddx
                mx += sx
                side = 0
            else:
                sdy += ddy
                my += sy
                side = 1
            hit = m[my * mw + mx]
            n += 1
        if side == 0:
            d = sdx - ddx
            wx = py + d * rdy
        else:
            d = sdy - ddy
            wx = px + d * rdx
        if d < 0.05:
            d = 0.05
        zbuf[c] = d
        wx -= int(wx)
        h = int(H / d)
        lvl = int(d * 1.6)
        if lvl >= NSH:
            lvl = NSH - 1
        typ = 1 if hit == 2 else 0
        col = SHADES[typ][side][lvl]
        if wx < 0.06 or wx > 0.94:              # mörka kanter = tydliga block
            col = SHADES[typ][1][min(NSH - 1, lvl + 4)]
        top = mid - h // 2
        fb.fill_rect(c * CW, top, CW, h, col)


# ---------------------------------------------------------------
# Labyrint
# ---------------------------------------------------------------
def make_maze(cw, ch, loops):
    mw, mh = cw * 2 + 1, ch * 2 + 1
    m = bytearray([1]) * (mw * mh)
    seen = bytearray(cw * ch)
    seen[0] = 1
    m[mw + 1] = 0
    stack = [(0, 0)]
    while stack:
        x, y = stack[-1]
        nb = []
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < cw and 0 <= ny < ch and not seen[ny * cw + nx]:
                nb.append((nx, ny))
        if nb:
            nx, ny = nb[random.randint(0, len(nb) - 1)]
            seen[ny * cw + nx] = 1
            m[(y + ny + 1) * mw + (x + nx + 1)] = 0
            m[(2 * ny + 1) * mw + 2 * nx + 1] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    # Ta bort några väggar så att det blir flera vägar
    for _ in range(loops):
        x = random.randint(1, mw - 2)
        y = random.randint(1, mh - 2)
        if m[y * mw + x] and (x % 2) != (y % 2):
            m[y * mw + x] = 0
    return m, mw, mh


def expand(maze, mw, cells):
    """Gör om labyrinten till en karta med gångar som är 2 rutor breda.
    Rum (cx, cy) blir rutorna 3*cx+1..3*cx+2, mitten är 3*cx+2."""
    n = cells * 3 + 1
    m = bytearray([1]) * (n * n)
    for y in range(n):
        for x in range(n):
            xi, yi = x % 3, y % 3
            if xi and yi:
                m[y * n + x] = 0
            elif xi == 0 and yi and 0 < x < n - 1:
                if maze[(2 * (y // 3) + 1) * mw + 2 * (x // 3)] == 0:
                    m[y * n + x] = 0
            elif yi == 0 and xi and 0 < y < n - 1:
                if maze[(2 * (y // 3)) * mw + 2 * (x // 3) + 1] == 0:
                    m[y * n + x] = 0
    # Ytterkanten får en annan färg
    for i in range(n):
        m[i] = 2
        m[(n - 1) * n + i] = 2
        m[i * n] = 2
        m[i * n + n - 1] = 2
    return m, n


def bfs(m, mw, mh, sx, sy):
    dist = [-1] * (mw * mh)
    dist[sy * mw + sx] = 0
    q = [(sx, sy)]
    i = 0
    while i < len(q):
        x, y = q[i]
        i += 1
        d = dist[y * mw + x] + 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            k = ny * mw + nx
            if m[k] == 0 and dist[k] < 0:
                dist[k] = d
                q.append((nx, ny))
    return dist


def cell_list(cells):
    return [(x, y) for y in range(cells) for x in range(cells)]


def cdist(dist, mw, c):
    return dist[(2 * c[1] + 1) * mw + 2 * c[0] + 1]


def ctr(c):
    return c * 3 + 2.0


# ---------------------------------------------------------------
# Sprites (mynt, nyckel, utgång, spöken)
# ---------------------------------------------------------------
COIN_SH = [rgb(*lerp(FOG, (255, 210, 40), 1.0 / (1 + i * 0.5))) for i in range(NSH)]
KEY_SH = [rgb(*lerp(FOG, (60, 230, 255), 1.0 / (1 + i * 0.5))) for i in range(NSH)]
GHOST_SH = [rgb(*lerp(FOG, (230, 230, 255), 1.0 / (1 + i * 0.45))) for i in range(NSH)]
PORTAL_A = [rgb(*lerp(FOG, (200, 80, 255), 1.0 / (1 + i * 0.4))) for i in range(NSH)]
PORTAL_B = [rgb(*lerp(FOG, (90, 255, 220), 1.0 / (1 + i * 0.4))) for i in range(NSH)]
LOCK_SH = [rgb(*lerp(FOG, (120, 60, 60), 1.0 / (1 + i * 0.4))) for i in range(NSH)]


def draw_sprite(fb, kind, sx, sy, px, py, dx, dy, plx, ply, zbuf, mid, t, locked):
    rx = sx - px
    ry = sy - py
    inv = 1.0 / (plx * dy - dx * ply)
    tx = inv * (dy * rx - dx * ry)
    tz = inv * (-ply * rx + plx * ry)
    if tz < 0.2:
        return
    scx = int(W / 2 * (1 + tx / tz))
    size = int(H / tz)
    lvl = min(NSH - 1, int(tz * 1.6))
    if kind == 0:                                  # mynt som snurrar
        r = size * 0.16 * (0.35 + 0.65 * abs(math.sin(t * 0.12 + sx)))
        cy = mid + int(size * 0.18)
        ry_ = size * 0.16
        col = COIN_SH[lvl]
    elif kind == 1:                                # nyckel (romb)
        r = size * 0.14
        cy = mid + int(size * (0.05 + 0.04 * math.sin(t * 0.15)))
        ry_ = r * 1.4
        col = KEY_SH[lvl]
    elif kind == 2:                                # utgång (portal)
        r = size * 0.34
        cy = mid
        ry_ = size * 0.46
        col = LOCK_SH[lvl] if locked else (PORTAL_A[lvl] if (t // 6) % 2 else PORTAL_B[lvl])
    else:                                          # spöke
        r = size * 0.26
        cy = mid + int(size * 0.05 + 4 * math.sin(t * 0.2))
        ry_ = r
        col = GHOST_SH[lvl]
    if r < 1:
        return
    x0 = int(scx - r)
    x1 = int(scx + r)
    c0 = max(0, x0 // CW)
    c1 = min(NR - 1, x1 // CW)
    for c in range(c0, c1 + 1):
        if zbuf[c] <= tz:
            continue
        xc = c * CW + CW // 2
        u = (xc - scx) / r
        if u < -1 or u > 1:
            continue
        if kind == 1:
            half = int(ry_ * (1 - abs(u)))
            fb.fill_rect(c * CW, cy - half, CW, 2 * half + 1, col)
        elif kind == 3:
            half = int(ry_ * math.sqrt(1 - u * u))
            fb.fill_rect(c * CW, cy - half, CW, half + int(r * 1.1), col)
            if 0.2 < abs(u) < 0.55:                   # ögon
                fb.fill_rect(c * CW, cy - int(r * 0.25), CW, max(2, int(r * 0.3)), BLACK)
        else:
            half = int(ry_ * math.sqrt(1 - u * u))
            fb.fill_rect(c * CW, cy - half, CW, 2 * half + 1, col)
            if kind == 2 and abs(u) < 0.6:            # mörk insida i portalen
                ih = int(half * 0.75)
                fb.fill_rect(c * CW, cy - ih, CW, 2 * ih + 1, BLACK if locked else FOG_C)


FOG_C = rgb(*FOG)


# ---------------------------------------------------------------
# En nivå
# ---------------------------------------------------------------
def play_level(lcd, keys, level, lives, score):
    """Returnerar (resultat, liv, poäng). resultat = 'klar', 'dod' eller 'meny'."""
    cells = min(4 + level, 12)
    maze, zw, zh = make_maze(cells, cells, 1 + level * 2)
    dist = bfs(maze, zw, zh, 1, 1)
    m, mw = expand(maze, zw, cells)
    mh = mw
    free = cell_list(cells)
    exit_c = max(free, key=lambda c: cdist(dist, zw, c))
    need_key = level >= 3
    sprites = []                                    # [typ, x, y]
    if need_key:
        dexit = bfs(maze, zw, zh, 2 * exit_c[0] + 1, 2 * exit_c[1] + 1)
        cand = [c for c in free if cdist(dist, zw, c) > 4 and c != exit_c]
        kc = max(cand, key=lambda c: cdist(dexit, zw, c) + random.randint(0, 6))
        sprites.append([1, ctr(kc[0]), ctr(kc[1])])
    n_coins = 4 + level
    pool = [c for c in free if c != (0, 0) and c != exit_c]
    for _ in range(min(n_coins, len(pool))):
        c = pool.pop(random.randint(0, len(pool) - 1))
        sprites.append([0, ctr(c[0]), ctr(c[1])])
    sprites.append([2, ctr(exit_c[0]), ctr(exit_c[1])])
    ghosts = []                                     # [x, y, mål-rum x, mål-rum y]
    for _ in range(0 if level < 4 else min(3, (level - 2) // 2)):
        far = [c for c in free if cdist(dist, zw, c) > 8]
        if far:
            c = far[random.randint(0, len(far) - 1)]
            ghosts.append([ctr(c[0]), ctr(c[1]), c[0], c[1]])
    gspeed = 0.035 + level * 0.003

    # Spelaren börjar i första rummet och tittar mot en öppen gång
    px, py = 2.0, 2.0
    ang = 0.0 if maze[zw + 2] == 0 else math.pi / 2
    walking = False
    has_key = False
    coins = 0
    zbuf = [1e9] * NR
    seen = bytearray(mw * mh)
    MS = max(2, min(4, 76 // mw))                   # minikartans rutstorlek
    mm_w = mw * MS
    mini = bytearray(mm_w * mm_w * 2)
    mfb = framebuf.FrameBuffer(mini, mm_w, mm_w, framebuf.RGB565)
    mfb.fill(BLACK)
    msg, msg_t = ("Hitta utgangen!" if not need_key else "Hitta nyckeln!"), 70
    hurt = 0
    t = 0
    start = time.ticks_ms()
    lcd.set_bg(view_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.long():
            r = pause(lcd, keys)
            if r:
                return "meny", lives, score
            lcd.set_bg(view_bg)
            keys.wait_release()
        if keys.chord_tap:
            walking = not walking
        if not keys.chorded:
            if keys.now[0]:
                ang -= 0.075
            if keys.now[1]:
                ang += 0.075
        dx, dy = math.cos(ang), math.sin(ang)
        plx, ply = -dy * 0.66, dx * 0.66
        if walking:
            sp = 0.055
            nx, ny = px + dx * sp, py + dy * sp
            mg = 0.22
            if m[int(py) * mw + int(nx + (mg if dx > 0 else -mg))] == 0:
                px = nx
            if m[int(ny + (mg if dy > 0 else -mg)) * mw + int(px)] == 0:
                py = ny

        # Avslöja minikartan runt spelaren
        cx, cy = int(px), int(py)
        for yy in range(max(0, cy - 1), min(mh, cy + 2)):
            for xx in range(max(0, cx - 1), min(mw, cx + 2)):
                k = yy * mw + xx
                if not seen[k]:
                    seen[k] = 1
                    mfb.fill_rect(xx * MS, yy * MS, MS, MS, DIM if m[k] else rgb(25, 25, 45))

        # Plocka upp saker
        for s in sprites[:]:
            if (s[1] - px) ** 2 + (s[2] - py) ** 2 < 0.45:
                if s[0] == 0:
                    sprites.remove(s)
                    coins += 1
                    score += 10
                elif s[0] == 1:
                    sprites.remove(s)
                    has_key = True
                    msg, msg_t = "Nyckel! Hitta utgangen", 70
                elif s[0] == 2:
                    if need_key and not has_key:
                        if msg_t <= 0:
                            msg, msg_t = "Last! Du behover nyckeln", 50
                    else:
                        secs = time.ticks_diff(time.ticks_ms(), start) // 1000
                        bonus = max(0, 200 - secs) + level * 50
                        return level_done(lcd, keys, level, lives, score,
                                          coins, n_coins, secs, bonus)

        # Spöken vandrar i gångarna
        for g in ghosts:
            tx_, ty_ = ctr(g[2]), ctr(g[3])
            ddx, ddy = tx_ - g[0], ty_ - g[1]
            dl = math.sqrt(ddx * ddx + ddy * ddy)
            if dl < gspeed:
                g[0], g[1] = tx_, ty_
                opts = []
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if maze[(2 * g[3] + 1 + oy) * zw + 2 * g[2] + 1 + ox] == 0:
                        opts.append((g[2] + ox, g[3] + oy))
                if random.random() < 0.6:            # jaga spelaren ibland
                    opts.sort(key=lambda c: abs(ctr(c[0]) - px) + abs(ctr(c[1]) - py))
                    g[2], g[3] = opts[0]
                else:
                    g[2], g[3] = opts[random.randint(0, len(opts) - 1)]
            else:
                g[0] += ddx / dl * gspeed
                g[1] += ddy / dl * gspeed
            if hurt == 0 and (g[0] - px) ** 2 + (g[1] - py) ** 2 < 0.35:
                lives -= 1
                hurt = 45
                if lives <= 0:
                    return "dod", 0, score
                msg, msg_t = "Aj! Ett spoke!", 50

        # --- Rita ---
        bob = int(2 * math.sin(t * 0.4)) if walking else 0
        mid = H // 2 + bob
        lcd.load_bg()
        cast(lcd, m, mw, px, py, dx, dy, plx, ply, zbuf, mid)
        allsp = [(s[0], s[1], s[2]) for s in sprites] + [(3, g[0], g[1]) for g in ghosts]
        allsp.sort(key=lambda s: -((s[1] - px) ** 2 + (s[2] - py) ** 2))
        locked = need_key and not has_key
        for kind, sx, sy in allsp:
            draw_sprite(lcd, kind, sx, sy, px, py, dx, dy, plx, ply, zbuf, mid, t, locked)
        if hurt > 0:
            hurt -= 1
            if hurt % 6 < 3:
                lcd.rect(0, 0, W, H, RED)
                lcd.rect(1, 1, W - 2, H - 2, RED)

        # Minikarta uppe till höger
        ox = W - mm_w - 4
        lcd.fill_rect(ox - 2, 2, mm_w + 4, mm_w + 4, BLACK)
        lcd.blit(mfb, ox, 4)
        for s in sprites:
            k = int(s[2]) * mw + int(s[1])
            if seen[k] and s[0] != 0:
                lcd.fill_rect(ox + int(s[1]) * MS, 4 + int(s[2]) * MS, MS, MS,
                              CYAN if s[0] == 1 else PURPLE)
        ppx, ppy = ox + int(px * MS), 4 + int(py * MS)
        lcd.fill_rect(ppx - 1, ppy - 1, 3, 3, YELLOW)
        lcd.line(ppx, ppy, ppx + int(dx * 5), ppy + int(dy * 5), YELLOW)

        # Text
        lcd.text("NIVA %d" % level, 6, 6, WHITE)
        lcd.text("MYNT %d/%d" % (coins, n_coins), 6, 18, YELLOW)
        for i in range(lives):
            lcd.fill_rect(6 + i * 12, 32, 8, 8, RED)
        if has_key:
            lcd.text("NYCKEL", 6, 46, CYAN)
        if msg_t > 0:
            msg_t -= 1
            lcd.fill_rect(0, H - 26, W, 18, BLACK)
            ctext(lcd, msg, H - 21, WHITE)
        elif not walking and (t // 15) % 2 == 0:
            ctext(lcd, "0+1: ga   hall 0/1: svang", H - 14, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def pause(lcd, keys):
    """Paus. True = till menyn."""
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
        for i, s in enumerate(("FORTSATT", "TILL MENYN")):
            col = BG if i == sel else WHITE
            if i == sel:
                lcd.fill_rect(90, 114 + i * 20, 140, 16, YELLOW)
            ctext(lcd, s, 118 + i * 20, col)
        lcd.text("0/1 valj  0+1 ok", 96, 158, GRAY)
        lcd.show()
        frame_wait(t0)


def level_done(lcd, keys, level, lives, score, coins, n_coins, secs, bonus):
    total = score + bonus
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 15 and (keys.chord_tap or keys.tapped[0] or keys.tapped[1]):
            return "klar", lives, total
        lcd.fill(BG)
        for _ in range(30):
            lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3,
                          random.choice((YELLOW, CYAN, PURPLE, GREEN)))
        stext(lcd, "NIVA %d KLAR!" % level, 30 + int(4 * math.sin(t * 0.2)), GREEN, 3)
        ctext(lcd, "Mynt: %d av %d" % (coins, n_coins), 96, YELLOW, 2)
        ctext(lcd, "Tid: %d s" % secs, 124, WHITE, 2)
        ctext(lcd, "Bonus: +%d" % bonus, 152, CYAN, 2)
        ctext(lcd, "Poang: %d" % total, 186, WHITE, 2)
        if (t // 10) % 2 == 0:
            ctext(lcd, "Tryck for nasta niva", 220, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Titel och spelets gång
# ---------------------------------------------------------------
def title(lcd, keys, save):
    """Returnerar startnivå."""
    opts = ["NY START"]
    if save["level"] > 1:
        opts.insert(0, "FORTSATT NIVA %d" % save["level"])
    sel = 0
    t = 0
    ang = 0.0
    maze, zw, zh = make_maze(4, 4, 6)
    m, mw = expand(maze, zw, 4)
    zbuf = [1e9] * NR
    lcd.set_bg(view_bg)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.tapped[0]:
            sel = (sel - 1) % len(opts)
        if keys.tapped[1]:
            sel = (sel + 1) % len(opts)
        if keys.chord_tap:
            return save["level"] if opts[sel].startswith("FORT") else 1
        if keys.long():
            machine.soft_reset()                 # tillbaka till startmenyn
        # Bakgrund: en vy som sakta snurrar
        ang += 0.012
        dx, dy = math.cos(ang), math.sin(ang)
        lcd.load_bg()
        cast(lcd, m, mw, 2.0, 2.0, dx, dy, -dy * 0.66, dx * 0.66, zbuf, H // 2)
        stext(lcd, "LABYRINT", 24 + int(3 * math.sin(t * 0.1)), CYAN, 4)
        ctext(lcd, "3D", 64, PURPLE, 3)
        for i, s in enumerate(opts):
            y = 120 + i * 30
            if i == sel:
                lcd.fill_rect(50, y - 6, 220, 26, CYAN)
                ctext(lcd, s, y, BG, 2)
            else:
                lcd.fill_rect(50, y - 6, 220, 26, BLACK)
                ctext(lcd, s, y, WHITE, 2)
        lcd.fill_rect(0, 196, W, 44, BLACK)
        ctext(lcd, "Rekord: %d" % save["best"], 202, YELLOW)
        ctext(lcd, "0/1 valj  0+1 start  hall 0+1 meny", 222, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def game_over(lcd, keys, score, level, save):
    new = score > save["best"]
    if new:
        save["best"] = score
        store(save)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 20 and (keys.chord_tap or keys.tapped[0] or keys.tapped[1]):
            return
        lcd.fill(BG)
        stext(lcd, "GAME OVER", 40, RED, 3)
        ctext(lcd, "Du kom till niva %d" % level, 90, WHITE, 2)
        ctext(lcd, str(score), 120, WHITE, 5)
        if new and (t // 8) % 2 == 0:
            ctext(lcd, "NYTT REKORD!", 176, YELLOW, 2)
        elif not new:
            ctext(lcd, "Rekord: %d" % save["best"], 180, GRAY)
        ctext(lcd, "Tryck for att fortsatta", 220, GRAY)
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
    while True:
        level = title(lcd, keys, save)
        lives, score = 3, 0
        while True:
            gc.collect()
            res, lives, score = play_level(lcd, keys, level, lives, score)
            if res == "meny":
                break
            if res == "dod":
                game_over(lcd, keys, score, level, save)
                break
            level += 1
            if level > save["level"]:
                save["level"] = level
                store(save)


main()
