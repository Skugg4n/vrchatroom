

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
