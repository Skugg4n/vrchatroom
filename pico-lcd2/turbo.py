# TURBO - racingspel i 3D för Pico Arcade
#
#   KEY0 (uppe vänster)  = styr vänster
#   KEY1 (uppe höger)    = styr höger
#   KEY2 (nere höger)    = gasa
#   KEY3 (nere vänster)  = bromsa
#   alla fyra            = paus
#
# Kör så långt du kan innan tiden tar slut. Varje kontrollpunkt ger mer tid.
# Kräver picolib.py på Picon.

from picolib import *
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
