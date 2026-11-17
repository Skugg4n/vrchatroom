# TURBO (stående): kör så fort du kan och väj mellan bilarna!
#   vänster/höger styr. De andra två knapparna: NITRO (när mätaren är full).
#   Kör nära en bil utan att krocka = NARA! (+ poäng och nitro)
RX0, RX1 = 24, 216            # vägkanterna
LANES = 4
LW = (RX1 - RX0) // LANES     # 48
PY = 252                      # din bils y (överkant)
CW, CH = 24, 40
CAR_COLS = (rgb(230, 60, 60), rgb(60, 130, 255), rgb(250, 210, 40), rgb(240, 240, 240),
            rgb(60, 200, 110), rgb(250, 130, 30), rgb(180, 80, 230))
ROAD = rgb(60, 60, 68)
GRASS = (rgb(40, 140, 60), rgb(34, 120, 52))


def play(lcd, keys):
    return v_play(lcd, keys, "TURBO", CORAL, ("Kor sa fort du kan!", "Vanster/hoger styr.", "Andra knapparna: NITRO", "Kor nara = bonus!"), "turbo", car_game)


def draw_car(fb, x, y, col, me=False, t=0):
    x, y = int(x), int(y)
    fb.fill_rect(x + 2, y, CW - 4, CH, col)
    fb.fill_rect(x, y + 4, CW, CH - 8, col)
    fb.fill_rect(x + 4, y + (8 if me else 24), CW - 8, 8, rgb(40, 50, 80))       # ruta
    fb.fill_rect(x + 4, y + (26 if me else 6), CW - 8, 5, rgb(40, 50, 80))
    fb.fill_rect(x - 1, y + 6, 3, 8, BLACK)                                    # hjul
    fb.fill_rect(x + CW - 2, y + 6, 3, 8, BLACK)
    fb.fill_rect(x - 1, y + CH - 14, 3, 8, BLACK)
    fb.fill_rect(x + CW - 2, y + CH - 14, 3, 8, BLACK)
    if me:
        fb.fill_rect(x + 4, y + CH - 2, 5, 2, CORAL)
        fb.fill_rect(x + CW - 9, y + CH - 2, 5, 2, CORAL)
    else:
        fb.fill_rect(x + 3, y + CH - 3, 5, 3, rgb(255, 60, 40))                   # bromsljus
        fb.fill_rect(x + CW - 8, y + CH - 3, 5, 3, rgb(255, 60, 40))


def car_game(lcd, fb, keys, L, R):
    N = [k for k in (K0, K1, K2, K3) if k != L and k != R]
    x = RX0 + LW + (LW - CW) / 2
    vx = 0.0
    speed = 9.0               # pixlar per bildruta
    dist = 0.0
    scroll = 0.0
    nitro = 0.0               # mätare 0..100
    boost = 0
    near = 0
    bonus = 0
    cars = []                 # [x, y, egen fart, färg, nära-räknad]
    gap = 0.0
    parts = Particles(50)
    pops = Popups()
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return None
        if keys.held(L):
            vx -= 1.3
        if keys.held(R):
            vx += 1.3
        vx *= 0.78
        x += vx
        if nitro >= 100 and any(keys.pressed(k) for k in N):
            boost = 90
            nitro = 0.0
            pops.add(VW // 2, 200, "NITRO!", AMBER, 2)
        base = min(24.0, 9.0 + dist / 2500)          # fortare och fortare
        target = base + (9 if boost else 0)
        speed += (target - speed) * 0.08
        if boost:
            boost -= 1
        dist += speed
        scroll = (scroll + speed) % 40
        # utanför vägen: skakigt och långsamt
        off = x < RX0 or x + CW > RX1
        if off:
            speed *= 0.93
            if t % 2:
                parts.burst(x + CW / 2, PY + CH, rgb(120, 90, 50), 2, 1.5, 8)
        x = max(4.0, min(VW - CW - 4.0, x))
        # nya bilar
        gap -= speed
        if gap <= 0:
            lane = random.randint(0, LANES - 1)
            own = random.uniform(3.0, 7.0)
            cars.append([RX0 + lane * LW + (LW - CW) / 2, -CH - 10.0, own, random.choice(CAR_COLS), False])
            if dist > 3000 and random.random() < 0.35:              # ibland två bredvid varandra
                lane2 = (lane + random.choice((1, 2, 3))) % LANES
                cars.append([RX0 + lane2 * LW + (LW - CW) / 2, -CH - 70.0, own, random.choice(CAR_COLS), False])
            gap = random.uniform(70, 150) * (1 if dist > 1500 else 1.4)
        crash = False
        for c in cars:
            c[1] += speed - c[2]
            # bilar byter ibland fil
            if random.random() < 0.004:
                c[0] += random.choice((-LW, LW))
                c[0] = max(RX0 + (LW - CW) / 2, min(RX1 - LW + (LW - CW) / 2, c[0]))
            if c[1] + CH > PY + 4 and c[1] < PY + CH - 4:
                dx = abs((c[0] + CW / 2) - (x + CW / 2))
                if dx < CW - 3:
                    crash = True
                elif dx < CW + 12 and not c[4]:
                    c[4] = True
                    near += 1
                    bonus += 50
                    nitro = min(100.0, nitro + 20)
                    pops.add(x + CW / 2, PY - 10, "NARA! +50", YELLOW)
                    if near >= 10:
                        goal("turbo", 1)
        cars = [c for c in cars if c[1] < VH + 20]
        nitro = min(100.0, nitro + 0.08)
        score = int(dist / 20) + bonus
        if score >= 2000:
            goal("turbo", 0)
        if score >= 8000:
            goal("turbo", 2)
        # --- rita ---
        s = int(scroll)
        for y in range(-40, VH, 40):
            fb.fill_rect(0, y + s, VW, 20, GRASS[0])
            fb.fill_rect(0, y + s + 20, VW, 20, GRASS[1])
        fb.fill_rect(RX0, 0, RX1 - RX0, VH, ROAD)
        for y in range(-40, VH, 20):
            c = CORAL if ((y + s) // 20) % 2 else WHITE
            fb.fill_rect(RX0 - 5, y + s % 20, 5, 20, c)
            fb.fill_rect(RX1, y + s % 20, 5, 20, c)
        for k in range(1, LANES):
            lx = RX0 + k * LW
            for y in range(-40, VH, 40):
                fb.fill_rect(lx - 1, y + s, 3, 20, WHITE)
        if speed > 16:                                  # fartstreck
            for k in range(6):
                sx = (k * 41 + t * 7) % VW
                sy = (k * 67 + t * 31) % VH
                fb.vline(sx, sy, int(speed * 2), rgb(200, 200, 220))
        for c in cars:
            draw_car(fb, c[0], c[1], c[3])
        if boost:
            for k in range(3):
                fb.fill_rect(int(x) + 6 + k * 4, PY + CH, 3, 6 + random.randint(0, 10), random.choice((AMBER, YELLOW, CORAL)))
        draw_car(fb, x, PY, SKY if not boost else AMBER, True, t)
        parts.draw(fb)
        pops.draw(fb)
        big(fb, str(score), 6, 6, WHITE, 2)
        kmh = int(speed * 12)
        rtext(fb, "%d km/h" % kmh, VW - 6, 8, YELLOW if boost else WHITE)
        fb.rect(6, 26, 80, 8, WHITE)
        fb.fill_rect(7, 27, int(78 * nitro / 100), 6, AMBER if nitro >= 100 else rgb(120, 90, 40))
        if nitro >= 100 and (t // 6) % 2:
            fb.text("NITRO! (%d/%d)" % (N[0], N[1]), 92, 26, AMBER)
        if t < 60 and (t // 10) % 2 == 0:
            ctext(fb, "%d <    > %d" % (L, R), 150, WHITE, 2, VW // 2)
        lcd.show()
        if crash:
            for k in range(30):
                t1 = time.ticks_ms()
                if k == 0:
                    parts.burst(x + CW / 2, PY + CH / 2, AMBER, 30, 4, 24)
                fb.fill_rect(0, 0, VW, VH, ROAD if k % 4 < 2 else rgb(120, 30, 30))
                for c in cars:
                    draw_car(fb, c[0], c[1], c[3])
                draw_car(fb, x, PY, rgb(90, 90, 90), True)
                parts.draw(fb)
                stext(fb, "KRASCH!", 120, CORAL, 4, VW // 2)
                lcd.show()
                wait(t1)
            return score
        t += 1
        wait(t0)
