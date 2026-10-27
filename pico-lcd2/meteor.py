# METEORER - ett Asteroids-spel för Pico Arcade
#
#   KEY0 (uppe vänster)  = sväng vänster
#   KEY1 (uppe höger)    = sväng höger
#   KEY3 (nere vänster)  = gasa
#   KEY2 (nere höger)    = skjut (håll inne för att skjuta hela tiden)
#   alla fyra            = paus
#
# Kräver picolib.py på Picon.

from picolib import *

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
