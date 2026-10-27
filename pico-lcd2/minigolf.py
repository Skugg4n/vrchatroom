# MINIGOLF - 9 hål för Pico Arcade
#
#   KEY0 (uppe vänster)  = sikta åt vänster (håll inne)
#   KEY1 (uppe höger)    = sikta åt höger (håll inne)
#   KEY3 (nere vänster)  = håll inne för att sikta långsamt och noga
#   KEY2 (nere höger)    = håll inne för att ladda, släpp för att slå
#   alla fyra            = paus
#
# Sand bromsar, vatten ger ett straffslag och pilarna visar sluttningar.
# Försök klara alla hål på så få slag som möjligt.
# Kräver picolib.py på Picon.

from picolib import *

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
