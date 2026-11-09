# STUDS: 0 vänster, 1 höger, 2 skjut.
# Ju högre du kommer, desto fler världar: NATTEN, HIMLEN, RYMDEN, GALAXEN.
# Power-ups: jetpack (flyger rakt upp), fjäderskor (6 superstudsar), stjärnor (+50).
S_GRAV = 0.36
S_JUMP = -8.6
S_SPRING = -13.5
# namn, höjd, himmel uppe, himmel nere, rutnät/dekor
S_WORLDS = (
    ("NATTEN", 0, (16, 20, 44), (36, 18, 56), (30, 32, 66)),
    ("HIMLEN", 300, (60, 120, 220), (150, 200, 255), (130, 180, 245)),
    ("RYMDEN", 800, (4, 4, 16), (20, 10, 40), (60, 60, 90)),
    ("GALAXEN", 1500, (30, 0, 50), (90, 20, 90), (160, 80, 200)),
)


def play(lcd, keys):
    parts = Particles(70)
    pops = Popups()
    stars = Stars(40)
    px, py, vx, vy = W / 2, 200.0, 0.0, S_JUMP
    face = 1
    cam = 0.0
    best_y = py
    bonus = 0
    plats = [[W / 2 - 22, 220.0, 0, 0.0, False]]      # x, y, typ, fart, trasig
    items = []                                         # platta, sort (0 jetpack, 1 skor, 2 stjärna)
    monsters = []                                      # x, y, fart, fas
    bats = []                                          # x, y, fart, fas
    bullets = []
    top = 220.0
    squash = 0
    jet = 0
    shoes = 0
    world = 0
    bg = [mix(S_WORLDS[0][2], S_WORLDS[0][3], y / (H - 1)) for y in range(H)]
    banner = 0
    t = 0
    keys.wait_release()

    def spawn_until(limit):
        nonlocal top
        while top > limit:
            height = (200 - top) / 10
            gmax = min(88, 40 + height * 0.04)
            gmin = min(60, 22 + height * 0.02)
            top -= random.uniform(gmin, gmax)
            r = random.random()
            if height > 300 and r < 0.15 + min(0.2, height / 8000):
                typ, spd = 1, random.choice((-1, 1)) * random.uniform(0.8, 1.8 + height / 2000)
            elif r > 0.92:
                typ, spd = 3, 0.0
            elif height > 300 and r > 0.78:
                typ, spd = 4, 0.0                           # moln: håller för ett studs
            else:
                typ, spd = 0, 0.0
            p = [random.uniform(4, W - 48), top, typ, spd, False]
            plats.append(p)
            if typ in (0, 1) and height > 60:
                q = random.random()
                if q < 0.025:
                    items.append([p, 0])
                elif q < 0.05:
                    items.append([p, 1])
                elif q < 0.16:
                    items.append([p, 2])
            if height > 150 and random.random() < 0.25:           # extra platta som går sönder
                plats.append([random.uniform(4, W - 48), top + random.uniform(10, 25), 2, 0.0, False])
            if height > 500 and random.random() < 0.05 + min(0.06, height / 30000):
                monsters.append([random.uniform(20, W - 20), top - 30, random.choice((-1, 1)) * 0.8, 0.0])
            if height > 350 and random.random() < 0.04 + min(0.05, height / 40000):
                d = random.choice((-1, 1))
                bats.append([-20.0 if d > 0 else W + 20.0, top - 20, d * random.uniform(1.2, 2.2), 0.0])

    def score():
        return int((200 - best_y) / 10) + bonus

    def die():
        for k in range(30):
            t1 = time.ticks_ms()
            draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
                       px, py + k * 6, cam, face, 0, t, score(), 0, 0)
            lcd.show()
            wait(t1)
        return score()

    spawn_until(cam - 40)
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return score()
        if keys.held(K0):
            vx -= 0.7
            face = -1
        if keys.held(K1):
            vx += 0.7
            face = 1
        vx *= 0.86
        vx = max(-5.5, min(5.5, vx))
        if keys.pressed(K2):
            bullets.append([px, py - 10])
        px += vx
        if px < -8:
            px += W + 16
        elif px > W + 8:
            px -= W + 16
        oy = py
        if jet:
            jet -= 1
            vy = -11.0
            parts.burst(px, py + 12, random.choice((AMBER, CORAL, YELLOW)), 2, 1.5, 10, 0.2)
        else:
            vy += S_GRAV
        py += vy
        if squash > 0:
            squash -= 1
        # Landa på plattor (bara på väg ner)
        if vy > 0:
            for p in plats:
                if p[4]:
                    continue
                if p[0] - 6 <= px <= p[0] + 50 and oy + 10 <= p[1] <= py + 10:
                    if p[2] == 2:
                        p[4] = True
                        parts.burst(p[0] + 22, p[1], S_PLAT_C[2], 10, 2, 16, 0.2)
                        continue
                    py = p[1] - 10
                    if p[2] == 3 or shoes:
                        vy = S_SPRING
                        pops.add(px, py - 20, "BOING!", AMBER)
                        if shoes and p[2] != 3:
                            shoes -= 1
                    else:
                        vy = S_JUMP
                    squash = 5
                    if p[2] == 4:                           # molnet går upp i rök
                        p[4] = True
                        parts.burst(p[0] + 22, p[1] + 3, WHITE, 14, 2, 18)
                    break
        for p in plats:
            if p[2] == 1:
                p[0] += p[3]
                if p[0] < 2 or p[0] > W - 46:
                    p[3] = -p[3]
            if p[4]:
                p[1] += 4
        # Power-ups
        for it in items:
            p = it[0]
            ix, iy = p[0] + 22, p[1] - 12
            if abs(px - ix) < 14 and abs(py - iy) < 16:
                if it[1] == 0:
                    jet = max(jet, 80)
                    pops.add(px, py - 20, "JETPACK!", AMBER, 2)
                elif it[1] == 1:
                    shoes = 6
                    pops.add(px, py - 20, "FJADERSKOR!", CORAL)
                else:
                    bonus += 50
                    pops.add(px, py - 20, "+50", YELLOW)
                parts.burst(ix, iy, YELLOW, 12, 2.5, 14)
                it[1] = -1
        items = [it for it in items if it[1] >= 0 and not it[0][4] and it[0][1] < cam + H + 20]
        # Monster
        for m in monsters:
            m[3] += 0.08
            m[0] += m[2]
            if m[0] < 14 or m[0] > W - 14:
                m[2] = -m[2]
            my = m[1] + math.sin(m[3]) * 4
            if abs(px - m[0]) < 14 and abs(py - my) < 14:
                if jet or (vy > 0 and py < my):
                    if not jet:
                        vy = S_JUMP * 1.1
                    m[1] = 1e9
                    parts.burst(px, py + 8, VIOLET, 16, 3, 18)
                    pops.add(px, py - 10, "+200", VIOLET)
                    bonus += 200
                    goal("studs", 1)
                else:
                    return die()
        for b in bats:
            b[3] += 0.2
            b[0] += b[2]
            by = b[1] + math.sin(b[3]) * 6
            if abs(px - b[0]) < 12 and abs(py - by) < 11:
                if jet or (vy > 0 and py < by):
                    if not jet:
                        vy = S_JUMP
                    b[1] = 1e9
                    parts.burst(px, py + 8, rgb(110, 60, 160), 12, 2.5, 14)
                    pops.add(px, py - 10, "+100", VIOLET)
                    bonus += 100
                else:
                    return die()
        for b in bullets:
            b[1] -= 9
            for m in monsters + bats:
                if abs(b[0] - m[0]) < 12 and abs(b[1] - m[1]) < 14:
                    parts.burst(m[0], m[1], VIOLET, 14, 3, 16)
                    pops.add(m[0], m[1] - 10, "+200", VIOLET)
                    m[1] = 1e9
                    b[1] = -1e9
                    bonus += 200
                    goal("studs", 1)
        bullets = [b for b in bullets if b[1] > cam - 20]
        monsters = [m for m in monsters if m[1] < cam + H + 40]
        bats = [b for b in bats if b[1] < cam + H + 40 and -40 < b[0] < W + 40]
        # Kameran följer med uppåt
        if py < cam + 100:
            cam = py - 100
        best_y = min(best_y, py)
        h = int((200 - best_y) / 10)
        if world < len(S_WORLDS) - 1 and h >= S_WORLDS[world + 1][1]:
            world += 1
            wd = S_WORLDS[world]
            bg = [mix(wd[2], wd[3], y / (H - 1)) for y in range(H)]
            banner = 70
        sc = score()
        if sc >= 500:
            goal("studs", 0)
        if sc >= 2000:
            goal("studs", 2)
        plats = [p for p in plats if p[1] < cam + H + 20]
        spawn_until(cam - 40)
        if py > cam + H + 20:
            return die()
        draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
                   px, py, cam, face, squash, t, sc, jet, shoes)
        parts.draw(lcd, 0, -int(cam))
        pops.draw(lcd, 0, -int(cam))
        if banner:
            banner -= 1
            if (banner // 6) % 2 or banner > 40:
                stext(lcd, S_WORLDS[world][0], 100, YELLOW, 3)
        lcd.show()
        t += 1
        wait(t0)


def draw_studs(lcd, bg, world, stars, plats, items, monsters, bats, bullets,
               px, py, cam, face, squash, t, score, jet, shoes):
    gradient(lcd, bg)
    dec = rgb(*S_WORLDS[world][4])
    c = int(cam)
    if world == 0:
        off = -c % 20
        for y in range(off, H, 20):
            lcd.hline(0, y, W, dec)
        for x in range(0, W, 20):
            lcd.vline(x, 0, H, dec)
    elif world == 1:
        for k in range(5):
            cy = (k * 70 - c // 3) % (H + 60) - 30
            cx = (k * 97) % W
            lcd.ellipse(cx, cy, 30, 9, dec, True)
            lcd.ellipse(cx + 18, cy - 5, 16, 8, dec, True)
    else:
        stars.draw(lcd, 0.0, 0.6 if world == 2 else 1.2)
        if world == 3:
            pyy = (40 - c // 6) % (H + 80) - 40
            lcd.ellipse(250, pyy, 26, 26, rgb(200, 90, 160), True)
            lcd.ellipse(250, pyy, 40, 6, rgb(240, 200, 120))
    for p in plats:
        x, y = int(p[0]), int(p[1]) - c
        col = S_PLAT_C[p[2]]
        if p[4]:
            if p[2] != 4:
                lcd.fill_rect(x, y, 20, 6, col)
                lcd.fill_rect(x + 24, y + 2, 20, 6, col)
            continue
        if p[2] == 4:
            lcd.ellipse(x + 12, y + 4, 12, 5, col, True)
            lcd.ellipse(x + 30, y + 4, 14, 6, col, True)
            lcd.ellipse(x + 22, y + 1, 10, 5, col, True)
            continue
        lcd.fill_rect(x + 2, y, 40, 7, col)
        lcd.fill_rect(x, y + 2, 44, 3, col)
        lcd.hline(x + 3, y + 1, 38, WHITE if p[2] != 2 else rgb(220, 170, 120))
        if p[2] == 2:
            lcd.vline(x + 15, y, 7, BG)
            lcd.vline(x + 30, y, 7, BG)
        if p[2] == 3:
            lcd.fill_rect(x + 16, y - 6, 12, 6, GRAY)
            lcd.fill_rect(x + 14, y - 8, 16, 3, CORAL)
    for it in items:
        ix, iy = int(it[0][0]) + 22, int(it[0][1]) - 12 - c + int(2 * math.sin(t * 0.2))
        if it[1] == 0:                                      # jetpack
            lcd.fill_rect(ix - 7, iy - 7, 6, 12, GRAY)
            lcd.fill_rect(ix + 1, iy - 7, 6, 12, GRAY)
            lcd.fill_rect(ix - 7, iy - 8, 14, 3, CORAL)
            lcd.fill_rect(ix - 6, iy + 5, 4, 3, AMBER)
            lcd.fill_rect(ix + 2, iy + 5, 4, 3, AMBER)
        elif it[1] == 1:                                    # fjäderskor
            lcd.fill_rect(ix - 8, iy, 7, 4, CORAL)
            lcd.fill_rect(ix + 1, iy, 7, 4, CORAL)
            for k in range(3):
                lcd.hline(ix - 7, iy + 5 + k * 2, 5, GRAY)
                lcd.hline(ix + 2, iy + 5 + k * 2, 5, GRAY)
        else:
            star(lcd, ix, iy, 7, YELLOW)
    for m in monsters:
        mx, my = int(m[0]), int(m[1] + math.sin(m[3]) * 4) - c
        lcd.ellipse(mx, my, 12, 10, VIOLET, True)
        lcd.ellipse(mx - 4, my - 3, 3, 3, WHITE, True)
        lcd.ellipse(mx + 4, my - 3, 3, 3, WHITE, True)
        lcd.pixel(mx - 4, my - 2, BLACK)
        lcd.pixel(mx + 4, my - 2, BLACK)
        lcd.hline(mx - 5, my + 5, 10, BLACK)
        for k in (-8, -2, 4):
            lcd.fill_rect(mx + k, my + 8 + (t // 5 + k) % 2, 3, 4, VIOLET)
    for b in bats:
        bx, by = int(b[0]), int(b[1] + math.sin(b[3]) * 6) - c
        fl = 5 if (t // 3) % 2 else -4
        tri(lcd, bx, by, bx - 13, by - 3 + fl, bx - 4, by + 4, rgb(70, 40, 110))
        tri(lcd, bx, by, bx + 13, by - 3 + fl, bx + 4, by + 4, rgb(70, 40, 110))
        lcd.ellipse(bx, by, 5, 5, rgb(110, 60, 160), True)
        lcd.fill_rect(bx - 3, by - 2, 2, 2, YELLOW)
        lcd.fill_rect(bx + 2, by - 2, 2, 2, YELLOW)
    for b in bullets:
        lcd.ellipse(int(b[0]), int(b[1]) - c, 3, 3, AMBER, True)
    # Hopparen
    x, y = int(px), int(py) - c
    sq = 3 if squash else 0
    if jet:
        lcd.fill_rect(x - 13, y - 6, 5, 12, GRAY)
        lcd.fill_rect(x - 13, y + 6, 5, 4 + t % 3, AMBER)
    lcd.ellipse(x, y - 2 + sq, 9, 9 - sq, LIME, True)
    lcd.fill_rect(x - 9, y + 2, 18, 6 - sq, LIME)
    lcd.fill_rect(x - 9, y + 6 - sq, 18, 2, rgb(60, 150, 70))
    lcd.fill_rect(x + 8 if face > 0 else x - 14, y - 4, 6, 4, LIME)      # näsa
    lcd.fill_rect(x + face * 3 - 1, y - 6, 3, 3, WHITE)
    lcd.pixel(x + face * 4, y - 5, BLACK)
    fc = CORAL if shoes else rgb(60, 150, 70)
    for k in (-6, -1, 4):
        lcd.fill_rect(x + k, y + 8 - sq, 2, 4 + sq, fc)
    big(lcd, str(score), 6, 6, WHITE, 2)
    lcd.text("REKORD %d" % SCORES.get("studs", 0), 6, 26, GRAY if world == 1 else DIM)
    if shoes:
        rtext(lcd, "SKOR x%d" % shoes, W - 6, 6, CORAL)
