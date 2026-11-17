

def choose(lcd, keys, title, options, col, sub="", locked=()):
    """Liten valmeny. Returnerar index, eller None (3 = tillbaka).
    locked = text för alternativ som är låsta (tom sträng = öppet)."""
    sel = 0
    t = 0
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
        theme_draw(lcd, t)
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


def icon_dino(fb, x, y, t):
    for yy in range(0, 56, 4):
        fb.fill_rect(x, y + yy, 160, 4, mix((90, 170, 255), (200, 235, 255), yy / 56))
    fb.fill_rect(x, y + 56, 160, 16, rgb(210, 180, 120))
    fb.ellipse(x + 130, y + 14, 8, 8, rgb(255, 230, 90), True)
    cx = x + 160 - (t * 3) % 180
    if cx > x - 20:
        for k in range(2):
            fb.fill_rect(cx + k * 10, y + 34, 6, 22, rgb(50, 160, 70))
    jy = int(abs(math.sin(t * 0.12)) * 22)
    c = rgb(120, 210, 120)
    fb.fill_rect(x + 30, y + 32 - jy, 12, 8, c)
    fb.fill_rect(x + 22, y + 39 - jy, 14, 10, c)
    fb.fill_rect(x + 24, y + 49 - jy, 3, 7, c)
    fb.fill_rect(x + 31, y + 49 - jy, 3, 7, c)
    fb.fill_rect(x + 37, y + 34 - jy, 2, 2, BLACK)


def icon_orm(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(10, 40, 26))
    path = ((4, 2), (5, 2), (6, 2), (7, 2), (7, 3), (7, 4), (8, 4), (9, 4), (10, 4))
    n = 3 + (t // 6) % 7
    for i in range(min(n, len(path))):
        px, py = path[i]
        fb.fill_rect(x + px * 12, y + py * 12, 11, 11, rgb(90, 220, 90) if i % 2 else rgb(60, 180, 70))
    fb.ellipse(x + 12 * 11 + 6, y + 4 * 12 + 6, 5, 5, CORAL, True)


def icon_stapla(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, rgb(40, 60, 120))
    for i in range(5):
        w = 70 - i * 6
        fb.fill_rect(x + 45 + i * 3, y + 60 - i * 10, w, 10, sb_icon(i))
    mx = x + 20 + int(50 + 50 * math.sin(t * 0.08))
    fb.fill_rect(mx - 25, y + 6, 46, 10, sb_icon(5))
    fb.rect(x + 140, y + 4, 14, 24, WHITE)                     # "stående"-märke
    fb.fill_rect(x + 145, y + 24, 4, 2, WHITE)


def sb_icon(i):
    a = i * 0.25
    return rgb(int(150 + 100 * math.sin(a)), int(150 + 100 * math.sin(a + 2.1)), int(150 + 100 * math.sin(a + 4.2)))


def icon_rusa(fb, x, y, t):
    for yy in range(0, 30, 3):
        fb.fill_rect(x, y + yy, 160, 3, mix((40, 20, 90), (255, 150, 90), yy / 30))
    fb.fill_rect(x, y + 30, 160, 42, rgb(30, 100, 50))
    tri(fb, x + 80, y + 30, x + 20, y + 72, x + 140, y + 72, rgb(80, 72, 70))
    for k in range(3):
        yy = y + 32 + ((t * 2 + k * 14) % 40)
        fb.fill_rect(x + 79, yy, 2, 4, WHITE)
    fb.fill_rect(x + 74, y + 40, 12, 14, TEAL)
    fb.ellipse(x + 80, y + 36, 5, 5, rgb(255, 200, 150), True)
    fb.fill_rect(x + 74 + ((t // 3) % 2) * 6, y + 54, 5, 8, rgb(50, 80, 200))
    fb.rect(x + 140, y + 4, 14, 24, WHITE)
    fb.fill_rect(x + 145, y + 24, 4, 2, WHITE)


def icon_anfall(fb, x, y, t):
    fb.fill_rect(x, y, 160, 72, BG)
    for i in range(14):
        fb.pixel(x + (i * 37) % 160, y + (i * 23 + t) % 72, WHITE)
    for k in range(3):
        ax = x + 30 + k * 40
        ay = y + 10 + (t + k * 9) % 20
        fb.fill_rect(ax - 6, ay - 4, 12, 7, LIME if k != 1 else VIOLET)
    sx = x + 80 + int(30 * math.sin(t * 0.07))
    fb.fill_rect(sx - 2, y + 50, 4, 12, WHITE)
    fb.fill_rect(sx - 9, y + 58, 18, 4, SKY)
    for k in range(3):
        fb.fill_rect(sx - 1, y + 44 - ((t * 6 + k * 15) % 40), 2, 5, YELLOW)
    fb.rect(x + 140, y + 4, 14, 24, WHITE)
    fb.fill_rect(x + 145, y + 24, 4, 2, WHITE)


# ---------------------------------------------------------------
# Teman för menyn (låses upp med stjärnor)
# ---------------------------------------------------------------
THEMES = (   # namn, stjärnor som behövs, himmel uppe/nere
    ("NATT", 0, ((10, 10, 34), (40, 16, 60))),
    ("HAV", 5, ((10, 70, 120), (4, 20, 50))),
    ("SOLNEDGANG", 10, ((70, 20, 90), (250, 120, 60))),
    ("SKOG", 16, ((8, 30, 24), (30, 70, 40))),
    ("SNO", 22, ((40, 50, 90), (130, 150, 190))),
    ("RYMD", 28, ((0, 0, 8), (16, 6, 36))),
    ("RETRO", 35, ((30, 0, 60), (230, 60, 150))),
    ("GULD", 42, ((70, 46, 6), (150, 110, 24))),
)
_THEME_BG = [None, -1]
TH_PTS = [((i * 73 + 11) % W, (i * 37 + 5) % H, i) for i in range(40)]
TH_MOUNT = bytearray(41)
for _i in range(41):
    TH_MOUNT[_i] = 40 + int(18 * math.sin(_i * 0.5) + 10 * math.sin(_i * 1.3 + 1))


def theme_bg():
    i = SCORES.get("theme", 0) % len(THEMES)
    if _THEME_BG[1] != i:
        a, b = THEMES[i][2]
        _THEME_BG[0] = [mix(a, b, y / (H - 1)) for y in range(H)]
        _THEME_BG[1] = i
    return _THEME_BG[0]


def theme_draw(fb, t):
    """Menyns bakgrund: en liten animerad scen för varje tema."""
    bg = theme_bg()
    gradient(fb, bg)
    n = SCORES.get("theme", 0) % len(THEMES)
    if n == 0:                                          # NATT: stjärnor, måne, stjärnfall
        for x, y, i in TH_PTS:
            if (t // 5 + i) % 9:
                fb.fill_rect(x, y, 2 if i % 5 == 0 else 1, 2 if i % 5 == 0 else 1, (WHITE, GRAY, DIM)[i % 3])
        fb.ellipse(104, 196, 15, 15, rgb(250, 240, 200), True)
        fb.ellipse(97, 191, 13, 13, bg[191], True)
        k = t % 160
        if k < 24:
            x, y = 20 + k * 11, 30 + k * 4
            fb.line(x, y, x - 22, y - 8, WHITE)
            fb.line(x - 22, y - 8, x - 40, y - 15, GRAY)
    elif n == 1:                                        # HAV: bubblor, fiskar, sjögräs
        for x, y, i in TH_PTS[:16]:
            by = H - ((t * (1 + i % 3) + y) % (H + 20))
            bx = x + int(4 * math.sin(t * 0.08 + i))
            fb.ellipse(bx, by, 2 + i % 3, 2 + i % 3, rgb(150, 210, 255))
        for i, c in enumerate((CORAL, AMBER, YELLOW, PINK)):
            d = 1 if i % 2 else -1
            sp = 1 + i % 3
            x = (t * sp + i * 97) % (W + 60) - 30
            if d < 0:
                x = W - x
            y = 60 + i * 38 + int(6 * math.sin(t * 0.05 + i))
            fb.ellipse(x, y, 9, 5, c, True)
            tri(fb, x - d * 8, y, x - d * 15, y - 5, x - d * 15, y + 5, c)
            fb.fill_rect(x + d * 4, y - 2, 2, 2, BLACK)
        fb.fill_rect(0, H - 10, W, 10, rgb(200, 170, 110))
        for k in range(9):
            bx = 12 + k * 37
            for j in range(6):
                fb.fill_rect(bx + int(4 * math.sin(t * 0.07 + j * 0.6 + k)), H - 16 - j * 9, 4, 10, rgb(40, 160, 90))
    elif n == 2:                                        # SOLNEDGÅNG: retro-sol, berg, fåglar
        sy = 150 + int(6 * math.sin(t * 0.02))
        fb.ellipse(70, sy, 50, 50, rgb(255, 210, 80), True)
        for k in range(6):
            fb.fill_rect(10, sy + 6 + k * 8, 120, 2 + k // 2, bg[min(H - 1, sy + 6 + k * 8)])
        for i in range(40):
            h = TH_MOUNT[i]
            fb.fill_rect(i * 8, H - h, 8, h, rgb(50, 16, 50))
        for k in range(3):
            x = (t + k * 120) % (W + 40) - 20
            y = 50 + k * 22 + int(3 * math.sin(t * 0.2 + k))
            w = 4 if (t // 6 + k) % 2 else 2
            fb.line(x - 6, y - w, x, y, BLACK)
            fb.line(x, y, x + 6, y - w, BLACK)
    elif n == 3:                                        # SKOG: granar och eldflugor
        for k in range(9):
            x = k * 38 + (12 if k % 2 else 0)
            h = 90 + (k * 37) % 50
            c = rgb(14, 60, 34) if k % 2 else rgb(20, 80, 44)
            fb.fill_rect(x + 12, H - 20, 6, 20, rgb(60, 40, 20))
            for j in range(5):
                w = 30 - j * 5
                fb.fill_rect(x + 15 - w // 2, H - 20 - (j + 1) * h // 6, w, h // 6 + 2, c)
        for x, y, i in TH_PTS[:18]:
            fx = (x + int(20 * math.sin(t * 0.03 + i))) % W
            fy = 40 + (y + int(14 * math.sin(t * 0.05 + i * 2))) % 170
            if (t // 4 + i) % 6 < 4:
                fb.fill_rect(fx, fy, 2, 2, rgb(220, 255, 120))
    elif n == 4:                                        # SNÖ: snöfall, kullar, snögubbe
        fb.ellipse(70, H + 40, 140, 70, rgb(230, 238, 250), True)
        fb.ellipse(260, H + 50, 130, 80, rgb(210, 222, 245), True)
        fb.ellipse(112, 204, 14, 14, WHITE, True)
        fb.ellipse(112, 182, 10, 10, WHITE, True)
        fb.fill_rect(109, 181, 2, 2, BLACK)
        fb.fill_rect(115, 181, 2, 2, BLACK)
        fb.fill_rect(112, 184, 5, 2, AMBER)
        for x, y, i in TH_PTS:
            fy = (y + t * (1 + i % 2)) % H
            fx = (x + int(8 * math.sin(t * 0.04 + i))) % W
            fb.fill_rect(fx, fy, 2 + i % 2, 2 + i % 2, WHITE)
    elif n == 5:                                        # RYMD: ljusfart och planet
        for x, y, i in TH_PTS[:30]:
            a = i * 0.7
            dx, dy = math.cos(a), math.sin(a)
            r = (t * (2 + i % 4) + i * 13) % 200
            x0, y0 = 160 + int(dx * r), 120 + int(dy * r)
            l = 2 + r // 25
            fb.line(x0, y0, x0 + int(dx * l), y0 + int(dy * l), WHITE if r > 60 else GRAY)
        fb.ellipse(50, 196, 26, 26, rgb(90, 140, 220), True)
        fb.ellipse(44, 190, 10, 6, rgb(140, 190, 250), True)
        fb.ellipse(50, 196, 44, 8, rgb(220, 190, 120))
    elif n == 6:                                        # RETRO: sol och rutnät
        fb.ellipse(70, 120, 44, 44, rgb(255, 200, 60), True)
        for k in range(5):
            fb.fill_rect(20, 96 + k * 6, 100, 1 + k // 2, bg[96 + k * 6])
        fb.fill_rect(0, 122, W, H - 122, rgb(20, 0, 40))
        c = rgb(255, 60, 200)
        fb.hline(0, 122, W, c)
        for k in range(8):
            f = ((k + (t % 20) / 20) / 8)
            fb.hline(0, 122 + int(118 * f * f), W, c)
        for k in range(-8, 9):
            fb.line(70 + k * 10, 122, 70 + k * 60, H, c)
    else:                                               # GULD: myntregn
        for x, y, i in TH_PTS[:20]:
            cy = (y + t * (2 + i % 3)) % (H + 20) - 10
            w = int(6 * abs(math.sin(t * 0.1 + i)))
            fb.ellipse(x, cy, w + 1, 7, YELLOW, True)
            if w > 2:
                fb.ellipse(x, cy, w - 2, 4, AMBER, True)
        for x, y, i in TH_PTS[20:]:
            if (t // 3 + i) % 10 == 0:
                fb.hline(x - 4, y, 9, WHITE)
                fb.vline(x, y - 4, 9, WHITE)


# ---------------------------------------------------------------
# Stående spel (skärmen vriden ett kvarts varv)
# ---------------------------------------------------------------
V_BG = [mix((14, 12, 44), (60, 16, 80), y / (VH - 1)) for y in range(VH)]


def v_calibrate(lcd, keys):
    """Frågar vilken knapp som är vänster och höger när man håller skärmen stående."""
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    got = []
    t = 0
    keys.wait_release()
    while len(got) < 2:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return False
        for k in range(4):
            if keys.pressed(k) and k not in got:
                got.append(k)
                break
        gradient(fb, V_BG, 0, VH)
        stars.draw(fb)
        stext(fb, "STAENDE", 18, TEAL, 3, VW // 2)
        ctext(fb, "Vrid skarmen sa att", 64, WHITE, 1, VW // 2)
        ctext(fb, "pilen pekar uppat", 76, WHITE, 1, VW // 2)
        bob = int(4 * math.sin(t * 0.2))
        tri(fb, 100, 116 + bob, 140, 116 + bob, 120, 94 + bob, YELLOW)
        fb.fill_rect(111, 116 + bob, 19, 36, YELLOW)
        ctext(fb, "Tryck pa knappen", 186, WHITE, 1, VW // 2)
        ctext(fb, "som sitter till", 198, WHITE, 1, VW // 2)
        stext(fb, "VANSTER" if not got else "HOGER", 218, YELLOW, 3, VW // 2)
        if (t // 8) % 2 == 0:
            if not got:
                big(fb, "<", 8, 262, YELLOW, 4)
            else:
                big(fb, ">", VW - 40, 262, YELLOW, 4)
        if got:
            ctext(fb, "Vanster = KEY%d" % got[0], 300, GRAY, 1, VW // 2)
        lcd.show()
        t += 1
        wait(t0)
    SCORES["_vl"], SCORES["_vr"] = got[0], got[1]
    save_scores()
    keys.wait_release()
    return True


def v_start(lcd, keys, title, col, lines, key, L, R):
    """Startskärm. Svar: 'go', 'exit' eller 'calib'."""
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            keys.wait_release()
            return "exit"
        if keys.pressed(L) or keys.pressed(R):
            return "go"
        for k in range(4):
            if k != L and k != R and keys.pressed(k):
                return "calib"
        gradient(fb, V_BG, 0, VH)
        stars.draw(fb)
        stext(fb, title, 40 + int(4 * math.sin(t * 0.15)), col, 4, VW // 2)
        for i, line in enumerate(lines):
            ctext(fb, line, 110 + i * 14, WHITE, 1, VW // 2)
        ctext(fb, "Rekord: %d" % SCORES.get(key, 0), 196, col, 1, VW // 2)
        if (t // 10) % 2 == 0:
            ctext(fb, "Tryck %d eller %d" % (L, R), 232, YELLOW, 2, VW // 2)
        ctext(fb, "%d = vanster   %d = hoger" % (L, R), 264, GRAY, 1, VW // 2)
        ctext(fb, "Annan knapp: stall in", 284, DIM, 1, VW // 2)
        ctext(fb, "Hall alla 4: till menyn", 300, DIM, 1, VW // 2)
        lcd.show()
        t += 1
        wait(t0)


def v_over(lcd, keys, key, score, col, L, R):
    """Slutskärm i stående läge. True = spela igen."""
    best, new = submit(key, score)
    fb = lcd.pfb
    stars = Stars(30, VW, VH)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if t > 15:
            if keys.pressed(L):
                return True
            if keys.pressed(R) or keys.pause():
                keys.wait_release()
                return False
        gradient(fb, V_BG, 0, VH)
        stars.draw(fb)
        if new:
            for _ in range(20):
                fb.fill_rect(random.randint(0, VW - 3), random.randint(0, VH - 3), 3, 3,
                             random.choice(CONFETTI))
        dy = int(4 * math.sin(t * 0.2))
        stext(fb, "GAME", 40 + dy, col, 4, VW // 2)
        stext(fb, "OVER", 80 + dy, col, 4, VW // 2)
        ctext(fb, str(score), 140, WHITE, 4, VW // 2)
        if new:
            if (t // 8) % 2 == 0:
                ctext(fb, "NYTT REKORD!", 196, YELLOW, 2, VW // 2)
        else:
            ctext(fb, "Rekord: %d" % best, 200, GRAY, 1, VW // 2)
        ctext(fb, "%d: spela igen" % L, 256, WHITE, 1, VW // 2)
        ctext(fb, "%d: till menyn" % R, 272, WHITE, 1, VW // 2)
        lcd.show()
        t += 1
        wait(t0)


def v_play(lcd, keys, title, col, lines, key, fn):
    """Kör ett stående spel. fn(lcd, fb, keys, L, R) ger poäng (None = avbrutet)."""
    lcd.portrait()
    try:
        if "_vl" not in SCORES and not v_calibrate(lcd, keys):
            return None
        while True:
            L, R = SCORES["_vl"], SCORES["_vr"]
            r = v_start(lcd, keys, title, col, lines, key, L, R)
            if r == "exit":
                return None
            if r == "calib":
                if not v_calibrate(lcd, keys):
                    return None
                continue
            while True:
                gc.collect()
                score = fn(lcd, lcd.pfb, keys, L, R)
                if score is None:
                    break
                if not v_over(lcd, keys, key, score, col, L, R):
                    return None
    finally:
        lcd.landscape()
        keys.wait_release()


# ---------------------------------------------------------------
# Spelen läses in från kommentarerna längst ner i den här filen
# ---------------------------------------------------------------
GAME_MOD = "_spel"


def unload_game():
    import sys
    if GAME_MOD in sys.modules:
        del sys.modules[GAME_MOD]
    gc.collect()


def load_game(name):
    """Plockar ut spelets kod (rader '#|...' efter '#@@ namn') till filen _spel.py
    och importerar den. Importen läser filen bit för bit, så det behövs ingen
    stor sammanhängande minnesbit. Bara ett spel i minnet åt gången."""
    unload_game()
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
    out = open(GAME_MOD + ".py", "w")
    out.write("from __main__ import *\n")      # spelet ser menyns/grundens namn
    on = False
    for line in src:
        if line.startswith("#@@ "):
            if on:
                break
            on = line[4:].strip() == name
            continue
        if on and line.startswith("#|"):
            out.write(line[2:])
    src.close()
    out.close()
    gc.collect()
    return __import__(GAME_MOD)


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
    ("dino", "DINO", rgb(120, 210, 120), ("Hoppa over kaktusar,", "ducka for faglar.", "Fortare och fortare!"),
     ("ducka", "hoppa", "ducka", "hoppa"), icon_dino),
    ("studs", "STUDS", SKY, ("Studsa hogt upp! Nya", "varldar, jetpack och", "monster pa vagen."),
     ("vanster", "hoger", "", "skjut"), icon_studs),
    ("pac", "SPOKJAKT", YELLOW, ("At alla prickar!", "Stora prickar gor", "spoken atbara."),
     ("upp", "hoger", "vanster", "ner"), icon_pac),
    ("orm", "ORM", rgb(90, 220, 90), ("At applen och vax.", "Guldapple och chili!", "Nya banor var 8:e."),
     ("upp", "hoger", "vanster", "ner"), icon_orm),
    ("2048", "2048", G_COL[4], ("Skjut brickorna at", "ett hall. Lika tal", "slas ihop. Na 2048!"),
     ("upp", "hoger", "vanster", "ner"), icon_2048),
    ("invasion", "INVASION", LIME, ("Skjut ner invasionen", "innan den landar.", "Full matare = laser"),
     ("vanster", "hoger", "laser", "skjut"), icon_invasion),
    ("kross", "KROSS", CORAL, ("Krossa alla stenar.", "Lila tal flera slag,", "X-stenar sprangs."),
     ("vanster", "hoger", "skjut", "skjut"), icon_kross),
    ("kurvan", "KURVAN", VIOLET, ("Rita en linje och", "krocka inte! Mot", "datorn eller 2 spel."),
     ("P1 <", "P2 <", "P1 >", "P2 >"), icon_kurvan),
    ("stapla", "STAPLA", CORAL, ("STAENDE SPEL!", "Bygg ett hogt torn.", "Perfekt = vaxer."),
     None, icon_stapla),
    ("rusa", "RUSA", AMBER, ("STAENDE SPEL!", "Spring, byt fil och", "hoppa over hinder."),
     None, icon_rusa),
    ("anfall", "ANFALL", LIME, ("STAENDE SPEL!", "Skjut ner allt som", "kommer. Bomber!"),
     None, icon_anfall),
)


def menu(lcd, keys, sel):
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
        theme_draw(lcd, t)
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
        rtext(lcd, "/%d" % (3 * len(GAMES)), W - 4, 14, GRAY)
        # Listan (rullar, 10 rader syns)
        first = max(0, min(sel - 4, len(GAMES) - 10))
        if first > 0:
            tri(lcd, 66, 36, 76, 36, 71, 31, WHITE)
        if first + 10 < len(GAMES):
            tri(lcd, 66, 234, 76, 234, 71, 239, WHITE)
        for i in range(first, min(len(GAMES), first + 10)):
            g = GAMES[i]
            y = 38 + (i - first) * 20
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
        lcd.hline(150, 190, 160, LINE)
        if ctrl is None:
            ctext(lcd, "Vrid skarmen nar", 196, WHITE, 1, 230)
            ctext(lcd, "spelet startar.", 210, WHITE, 1, 230)
        else:
            a, b, c, d = ctrl
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
        theme_draw(lcd, t)
        big(lcd, "STJARNOR", 14, 11, SHADOW, 3)
        big(lcd, "STJARNOR", 12, 9, YELLOW, 3)
        star(lcd, 236, 20, 10, YELLOW)
        big(lcd, "%d/%d" % (total_stars(), 3 * len(GAMES)), 250, 13, YELLOW, 1)
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
        lcd.text("MENYTEMA (2 byter):", 12, 154, WHITE)
        cur = SCORES.get("theme", 0)
        for i, (tn, need, cols) in enumerate(THEMES):
            x = 12 + (i % 4) * 75
            y = 166 + (i // 4) * 25
            a, b = cols
            lcd.fill_rect(x, y, 70, 21, mix(a, b, 0.5) if need <= n else PANEL)
            if i == cur:
                lcd.rect(x - 2, y - 2, 74, 25, WHITE)
            if need > n:
                lcd.text("%d" % need, x + 14, y + 7, AMBER)
                star(lcd, x + 46, y + 10, 5, AMBER)
            else:
                lcd.text(tn[:8], x + 3, y + 7, WHITE)
        ctext(lcd, "0/1 byt spel   3 tillbaka", 228, WHITE)
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
            play = ns.play
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
            play = ns = None
            unload_game()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            play = ns = None
            unload_game()
            show_error(lcd, e)
            keys.wait_release()
            while True:
                keys.update()
                if any(keys.now):
                    break
                time.sleep_ms(20)
