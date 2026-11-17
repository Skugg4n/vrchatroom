# ANFALL (stående): rymdskjutare. Vänster/höger styr, skeppet skjuter själv.
# De andra knapparna: bomb (rensar skärmen, en per 1000 poäng).
SHIP_Y = 292


def play(lcd, keys):
    return v_play(lcd, keys, "ANFALL", LIME, ("Skjut ner allt som", "kommer! Lila skepp", "tal tre skott och kan", "tappa trippelskott."), "anfall", sp_game)


def draw_ship(fb, x, t, triple):
    fb.fill_rect(x - 2, SHIP_Y - 14, 4, 18, WHITE)
    fb.fill_rect(x - 6, SHIP_Y - 4, 12, 6, SKY)
    fb.fill_rect(x - 12, SHIP_Y, 24, 4, SKY)
    fb.fill_rect(x - 12, SHIP_Y - 4, 3, 8, AMBER if triple else rgb(50, 80, 200))
    fb.fill_rect(x + 9, SHIP_Y - 4, 3, 8, AMBER if triple else rgb(50, 80, 200))
    fb.fill_rect(x - 1, SHIP_Y - 8, 2, 3, CORAL)
    fl = 4 + (t % 3) * 2
    fb.fill_rect(x - 3, SHIP_Y + 4, 6, fl, AMBER)
    fb.fill_rect(x - 1, SHIP_Y + 4, 2, fl + 3, YELLOW)


def draw_alien(fb, e, t):
    x, y = int(e[0]), int(e[1])
    if e[4] == 0:
        fb.fill_rect(x - 8, y - 5, 16, 9, LIME)
        fb.fill_rect(x - 5, y - 2, 3, 3, BG)
        fb.fill_rect(x + 2, y - 2, 3, 3, BG)
        fb.fill_rect(x - 6, y - 8, 2, 3, LIME)
        fb.fill_rect(x + 4, y - 8, 2, 3, LIME)
        k = 0 if (t // 8) % 2 else 3
        fb.fill_rect(x - 8 + k, y + 4, 3, 4, LIME)
        fb.fill_rect(x + 5 - k, y + 4, 3, 4, LIME)
    elif e[4] == 1:
        fb.ellipse(x, y, 14, 9, VIOLET, True)
        fb.ellipse(x, y - 2, 5, 5, WHITE, True)
        fb.fill_rect(x - 1, y - 3, 3, 3, BG)
        for i in range(e[3]):
            fb.fill_rect(x - 8 + i * 6, y + 11, 4, 2, CORAL)
    else:                                   # meteor
        fb.ellipse(x, y, 9, 9, rgb(140, 110, 90), True)
        fb.ellipse(x - 3, y - 2, 3, 3, rgb(100, 80, 60), True)


def sp_game(lcd, fb, keys, L, R):
    B = [k for k in (K0, K1, K2, K3) if k != L and k != R]
    x = 120.0
    bullets = []
    enemies = []      # [x, y, fas, liv, typ]  typ 0 grön, 1 lila, 2 meteor
    shots = []
    drops = []        # [x, y]  trippelskott
    stars = Stars(40, VW, VH)
    parts = Particles(80)
    pops = Popups()
    lives = 3
    inv = 60
    score = 0
    purple = 0
    triple = 0
    bombs = 1
    next_bomb = 1000
    spawn = 30
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return None
        if keys.held(L):
            x -= 5
        if keys.held(R):
            x += 5
        x = max(14, min(VW - 14, x))
        if bombs and any(keys.pressed(k) for k in B):
            bombs -= 1
            for e in enemies:
                parts.burst(e[0], e[1], AMBER, 8, 3, 14)
                score += 10
            enemies = []
            shots = []
            for k in range(6):
                fb.fill(WHITE if k % 2 == 0 else BG)
                lcd.show()
                time.sleep_ms(30)
        if t % 6 == 0:
            bullets.append([x, SHIP_Y - 16, 0])
            if triple:
                bullets.append([x - 8, SHIP_Y - 10, -1.5])
                bullets.append([x + 8, SHIP_Y - 10, 1.5])
        if triple:
            triple -= 1
        spawn -= 1
        if spawn <= 0:
            spawn = max(10, 40 - score // 60)
            r = random.random()
            kind = 1 if r < 0.18 else 2 if r < 0.3 and score > 300 else 0
            enemies.append([random.uniform(20, VW - 20), -14, random.uniform(0, 6.3),
                            3 if kind == 1 else 2 if kind == 2 else 1, kind])
        fall = min(1.2 + score / 2500, 3.4)
        for b in bullets:
            b[1] -= 10
            b[0] += b[2]
        bullets = [b for b in bullets if b[1] > -10]
        for e in enemies:
            e[1] += fall * (0.7 if e[4] == 1 else 1.4 if e[4] == 2 else 1.0)
            if e[4] != 2:
                e[0] += math.sin(e[1] * 0.04 + e[2]) * 1.6
            e[0] = max(14, min(VW - 14, e[0]))
            if e[4] != 2 and random.random() < (0.012 if e[4] else 0.005):
                shots.append([e[0], e[1] + 10])
        for s in shots:
            s[1] += 4.5
        shots = [s for s in shots if s[1] < VH + 5]
        for d in drops:
            d[1] += 2
            if abs(d[0] - x) < 14 and abs(d[1] - SHIP_Y) < 14:
                triple = 300
                d[1] = VH + 50
                pops.add(x, SHIP_Y - 30, "TRIPPEL!", AMBER)
        drops = [d for d in drops if d[1] < VH + 10]
        for b in bullets:
            for e in enemies:
                if e[3] > 0 and abs(b[0] - e[0]) < (14 if e[4] == 1 else 10) and abs(b[1] - e[1]) < 10:
                    e[3] -= 1
                    b[1] = -100
                    if e[3] <= 0:
                        score += (10, 50, 20)[e[4]]
                        parts.burst(e[0], e[1], (LIME, VIOLET, rgb(140, 110, 90))[e[4]], 10, 2.5, 14)
                        if e[4] == 1:
                            purple += 1
                            if purple >= 10:
                                goal("anfall", 1)
                            if random.random() < 0.4:
                                drops.append([e[0], e[1]])
                    break
        enemies = [e for e in enemies if e[3] > 0 and e[1] < VH + 20]
        if score >= next_bomb:
            next_bomb += 1000
            bombs += 1
            pops.add(VW // 2, 60, "+1 BOMB", CORAL)
        if score >= 500:
            goal("anfall", 0)
        if score >= 2000:
            goal("anfall", 2)
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
                parts.burst(x, SHIP_Y, AMBER, 20, 3, 18)
                if lives <= 0:
                    for _ in range(25):
                        t1 = time.ticks_ms()
                        fb.fill(BG)
                        parts.draw(fb)
                        lcd.show()
                        wait(t1)
                    return score
        fb.fill(BG)
        stars.draw(fb, 0.0, 1.5)
        for e in enemies:
            draw_alien(fb, e, t)
        for d in drops:
            fb.ellipse(int(d[0]), int(d[1]), 7, 7, AMBER, True)
            fb.text("3", int(d[0]) - 3, int(d[1]) - 3, BG)
        for b in bullets:
            fb.fill_rect(int(b[0]) - 1, int(b[1]), 2, 7, YELLOW)
        for s in shots:
            fb.fill_rect(int(s[0]) - 2, int(s[1]), 4, 4, CORAL)
        parts.draw(fb)
        pops.draw(fb)
        if inv == 0 or (t // 4) % 2 == 0:
            draw_ship(fb, int(x), t, triple)
        big(fb, str(score), 6, 6, WHITE, 2)
        for i in range(lives):
            fb.fill_rect(VW - 16 - i * 14, 8, 10, 8, SKY)
        fb.text("BOMB %d (%d/%d)" % (bombs, B[0], B[1]), 6, 26, CORAL if bombs else DIM)
        lcd.show()
        t += 1
        wait(t0)
