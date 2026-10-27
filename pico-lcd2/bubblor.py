# BUBBLOR - bubbelskjutare för Pico Arcade
#
#   KEY0 (uppe vänster)  = sikta åt vänster (håll inne)
#   KEY1 (uppe höger)    = sikta åt höger (håll inne)
#   KEY2 (nere höger)    = skjut
#   KEY3 (nere vänster)  = byt till nästa bubbla
#   alla fyra            = paus
#
# Få tre eller fler i samma färg att sitta ihop så spricker de. Bubblor
# som inte längre hänger fast i taket ramlar ner och ger extra poäng.
# Kräver picolib.py på Picon.

from picolib import *

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
