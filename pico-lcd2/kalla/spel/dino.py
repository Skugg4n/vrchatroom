# DINO: spring, hoppa och ducka. Det går fortare och fortare!
#   1 eller 2 hoppa (håll = högre, tryck igen i luften = dubbelhopp)
#   0 eller 3 ducka (i luften: snabbt ner)
D_GROUND = 200
D_X = 46
D_SKIES = (   # dag, solnedgång, natt, gryning (himmel uppe, nere)
    ((90, 170, 255), (200, 235, 255)),
    ((90, 40, 120), (255, 150, 80)),
    ((6, 6, 30), (40, 20, 70)),
    ((120, 120, 200), (255, 200, 170)),
)
D_COL = rgb(120, 210, 120)
D_DARK = rgb(60, 140, 70)
CACT = rgb(50, 160, 70)
CACT_D = rgb(30, 110, 50)
D_HILL = bytearray(64)
for _i in range(64):
    D_HILL[_i] = 30 + int(16 * math.sin(_i * 0.4) + 9 * math.sin(_i * 1.1 + 2))


def d_sky(a, b, f):
    t0 = [D_SKIES[a][0][k] + (D_SKIES[b][0][k] - D_SKIES[a][0][k]) * f for k in range(3)]
    t1 = [D_SKIES[a][1][k] + (D_SKIES[b][1][k] - D_SKIES[a][1][k]) * f for k in range(3)]
    return [mix(t0, t1, y / (D_GROUND - 1)) for y in range(D_GROUND)]


def draw_dino(fb, x, y, t, air, duck, shield):
    c = D_COL
    if shield:
        fb.ellipse(x + 12, y + 10, 20, 18, SKY if (t // 3) % 2 else WHITE)
    if duck:
        fb.fill_rect(x, y + 10, 24, 10, c)
        fb.fill_rect(x + 18, y + 6, 12, 8, c)
        fb.fill_rect(x + 24, y + 8, 2, 2, BLACK)
        k = (t // 2) % 2
        fb.fill_rect(x + 4, y + 20, 3, 4 - k * 2, D_DARK)
        fb.fill_rect(x + 14, y + 20, 3, 2 + k * 2, D_DARK)
        return
    fb.fill_rect(x + 10, y, 14, 9, c)                    # huvud
    fb.fill_rect(x + 18, y + 2, 2, 2, BLACK)             # öga
    fb.fill_rect(x + 18, y + 7, 6, 1, D_DARK)            # mun
    fb.fill_rect(x + 2, y + 8, 14, 10, c)                # kropp
    fb.fill_rect(x - 2, y + 8, 4, 5, c)                  # svans
    fb.fill_rect(x + 16, y + 11, 3, 2, c)                # arm
    if air:
        fb.fill_rect(x + 4, y + 18, 3, 6, D_DARK)
        fb.fill_rect(x + 11, y + 18, 3, 6, D_DARK)
    else:
        k = (t // 2) % 2
        fb.fill_rect(x + 4, y + 18, 3, 6 if k else 3, D_DARK)
        fb.fill_rect(x + 11, y + 18, 3, 3 if k else 6, D_DARK)


def draw_cactus(fb, x, w, h):
    top = D_GROUND - h
    for sx in range(x, x + w, 10):
        fb.fill_rect(sx + 2, top, 6, h, CACT)
        fb.vline(sx + 3, top + 1, h - 2, CACT_D)
        fb.fill_rect(sx - 1, top + h // 3, 3, 3, CACT)
        fb.fill_rect(sx - 1, top + h // 3 - 6, 3, 6, CACT)
        fb.fill_rect(sx + 8, top + h // 2, 3, 3, CACT)
        fb.fill_rect(sx + 8, top + h // 2 - 5, 3, 5, CACT)


def draw_bird(fb, x, y, t):
    c = rgb(200, 70, 200)
    fb.fill_rect(x + 4, y + 4, 16, 6, c)
    fb.fill_rect(x, y + 5, 5, 3, AMBER)
    fb.fill_rect(x + 5, y + 5, 2, 2, BLACK)
    if (t // 4) % 2:
        tri(fb, x + 8, y + 4, x + 16, y + 4, x + 12, y - 8, c)
    else:
        tri(fb, x + 8, y + 9, x + 16, y + 9, x + 12, y + 19, c)


def play(lcd, keys):
    dy = vy = 0.0                # höjd över marken och fart uppåt
    jumps = 0
    dist = 0.0
    speed = 5.5
    coins = 0
    shield = False
    obs = []                     # [x, typ, a, b]  typ 0 kaktus (bredd, höjd), 1 fågel (y)
    items = []                   # [x, y, typ]  typ 0 mynt, 1 sköld
    gap = 160
    phase = 0
    bg = d_sky(0, 0, 0)
    trans = 0
    parts = Particles(50)
    pops = Popups()
    shake = Shake()
    pebbles = [[random.randint(0, W), random.randint(D_GROUND + 4, H - 4)] for _ in range(14)]
    t = 0
    started = False
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return int(dist / 10) + coins * 10
        jp = keys.pressed(K1) or keys.pressed(K2)
        jh = keys.held(K1) or keys.held(K2)
        duck = keys.held(K0) or keys.held(K3)
        if not started:
            started = jp
        else:
            if jp and (dy == 0 or jumps < 2):
                vy = 9.5 if dy == 0 else 8.0
                jumps = 1 if dy == 0 else 2
                if jumps == 2:
                    parts.burst(D_X + 10, D_GROUND - int(dy), WHITE, 6, 1.5, 8)
            if dy > 0 or vy > 0:
                dy += vy
                vy -= 0.55 if jh and vy > 0 else 0.95
                if duck:
                    vy -= 1.6
                if dy <= 0:
                    dy = vy = 0.0
                    jumps = 0
                    parts.burst(D_X + 10, D_GROUND, rgb(200, 180, 140), 3, 1, 6)
            speed = min(5.5 + dist / 1300, 14.0)
            dist += speed
            score = int(dist / 10) + coins * 10
            # himmel: dag -> solnedgång -> natt -> gryning
            p = int(dist / 10) // 400 % 4
            if p != phase:
                trans = 64
                old, phase = phase, p
            if trans:
                trans -= 1
                if trans % 8 == 0:
                    bg = d_sky(old, phase, 1 - trans / 64)
            for o in obs:
                o[0] -= speed
            for it in items:
                it[0] -= speed
            if obs and obs[0][0] < -40:
                obs.pop(0)
            items = [it for it in items if it[0] > -20]
            if not obs or obs[-1][0] < W - gap:
                sc = int(dist / 10)
                r = random.random()
                x = W + 20
                if sc > 250 and r < 0.3:
                    obs.append([x, 1, random.choice((D_GROUND - 22, D_GROUND - 30, D_GROUND - 30, D_GROUND - 58)), 0])
                else:
                    n = random.choice((1, 1, 2, 2, 3)) if sc > 100 else random.choice((1, 1, 2))
                    h = random.randint(22, 32 + min(14, sc // 100))
                    obs.append([x, 0, n * 10, h])
                    if random.random() < 0.45:               # mynt i en båge över kaktusen
                        for k in range(5):
                            items.append([x - 30 + k * 20 + n * 5, D_GROUND - h - 18 - int(22 * math.sin(k * 0.78)), 0])
                if random.random() < 0.03 and not shield:
                    items.append([x + gap // 2, D_GROUND - 70, 1])
                gap = random.randint(140, 240) + int(speed * 9)
            # Krockar
            if duck and dy == 0:
                bx0, bx1, by0, by1 = D_X + 2, D_X + 28, D_GROUND - 14, D_GROUND
            else:
                bx0, bx1, by0, by1 = D_X + 4, D_X + 20, D_GROUND - 24 - dy, D_GROUND - dy
            for it in items:
                ix, iy = it[0], it[1]
                if bx0 - 6 < ix < bx1 + 6 and by0 - 8 < iy < by1 + 8:
                    if it[2] == 0:
                        coins += 1
                        parts.burst(ix, iy, YELLOW, 6, 1.6, 10)
                        if coins >= 50:
                            goal("dino", 1)
                    else:
                        shield = True
                        pops.add(ix, iy - 10, "SKOLD!", SKY)
                    it[0] = -99
            for o in obs:
                ox = o[0]
                if o[1] == 0:
                    x0, x1, y0, y1 = ox + 2, ox + o[2] - 1, D_GROUND - o[3] + 3, D_GROUND
                else:
                    x0, x1, y0, y1 = ox + 2, ox + 18, o[2], o[2] + 12
                if x0 < bx1 and x1 > bx0 and y0 < by1 and y1 > by0:
                    if shield:
                        shield = False
                        o[0] = -99
                        shake.hit(6)
                        parts.burst(ox + 8, y0 + 6, SKY, 16, 3, 16)
                        continue
                    shake.hit(10)
                    for k in range(24):
                        t1 = time.ticks_ms()
                        d_draw(lcd, bg, phase, dist, obs, items, pebbles, parts, pops, shake,
                               dy, t, False, False, coins, score)
                        stext(lcd, "AJ!", 80, CORAL, 4)
                        lcd.show()
                        wait(t1)
                    return score
            if score >= 500:
                goal("dino", 0)
            if score >= 2000:
                goal("dino", 2)
            for p_ in pebbles:
                p_[0] -= speed
                if p_[0] < 0:
                    p_[0] += W
                    p_[1] = random.randint(D_GROUND + 4, H - 4)
        d_draw(lcd, bg, phase, dist, obs, items, pebbles, parts, pops, shake, dy, t,
               duck and dy == 0, dy > 0 or not started, coins, int(dist / 10) + coins * 10, shield)
        if not started:
            stext(lcd, "DINO", 50, LIME, 5)
            if (t // 10) % 2 == 0:
                ctext(lcd, "1/2 hoppa   0/3 ducka", 120, WHITE)
        lcd.show()
        t += 1
        wait(t0)


def d_draw(lcd, bg, phase, dist, obs, items, pebbles, parts, pops, shake, dy, t,
           duck, air, coins, score, shield=False):
    ox, oy = shake.offset()
    gradient(lcd, bg, 0, D_GROUND)
    d = int(dist)
    # sol eller måne
    if phase == 2:
        for i in range(24):
            lcd.pixel((i * 73 + 11) % W, (i * 37 + 5) % 120, WHITE)
        lcd.ellipse(260, 46, 14, 14, rgb(250, 245, 210), True)
        lcd.ellipse(253, 42, 12, 12, bg[42], True)
    elif phase != 2:
        sy = 50 if phase == 0 else 120
        lcd.ellipse(260, sy, 18, 18, rgb(255, 230, 90) if phase != 1 else rgb(255, 150, 60), True)
    # moln och kullar
    for k in range(4):
        cx = (k * 110 - d // 6) % (W + 80) - 40
        cy = 30 + k * 17
        cc = rgb(255, 255, 255) if phase != 2 else rgb(60, 60, 90)
        lcd.ellipse(cx, cy, 22, 7, cc, True)
        lcd.ellipse(cx + 12, cy - 4, 12, 6, cc, True)
    hc = (rgb(120, 190, 120), rgb(110, 50, 90), rgb(30, 30, 60), rgb(150, 140, 190))[phase]
    sc = d // 3
    for i in range(0, W, 8):
        h = D_HILL[((i + sc) // 8) % 64]
        lcd.fill_rect(i, D_GROUND - h, 8, h, hc)
    lcd.fill_rect(0, D_GROUND, W, H - D_GROUND, rgb(210, 180, 120) if phase != 2 else rgb(70, 60, 60))
    lcd.hline(0, D_GROUND, W, rgb(120, 90, 50))
    for p in pebbles:
        lcd.fill_rect(int(p[0]), p[1], 3, 1, rgb(140, 110, 70))
    for it in items:
        x, y = int(it[0]) + ox, int(it[1]) + oy
        if it[2] == 0:
            w = int(5 * abs(math.sin(t * 0.15 + it[0] * 0.05)))
            lcd.ellipse(x, y, w + 1, 6, YELLOW, True)
        else:
            lcd.ellipse(x, y, 9, 9, SKY)
            star(lcd, x, y, 6, WHITE)
    for o in obs:
        if o[1] == 0:
            draw_cactus(lcd, int(o[0]) + ox, o[2], o[3])
        else:
            draw_bird(lcd, int(o[0]) + ox, o[2] + oy, t)
    y = D_GROUND - 24 - int(dy)
    draw_dino(lcd, D_X + ox, y + oy, t, air, duck, shield)
    parts.draw(lcd)
    pops.draw(lcd)
    big(lcd, str(score), W - 8 - len(str(score)) * 16, 8, WHITE, 2)
    lcd.ellipse(14, 14, 5, 6, YELLOW, True)
    lcd.text("%d" % coins, 24, 10, WHITE)
    lcd.text("REKORD %d" % SCORES.get("dino", 0), 8, 26, WHITE if phase == 2 else BLACK)
