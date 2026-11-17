# RAS (stående): plattformarna åker uppåt mot spikarna i taket. Rulla av kanterna
# och fall nedåt i tid! Vänster/höger rullar bollen. Det går fortare och fortare.
#   vit = vanlig, röd = spikar, grön = studs, gul = rullband, brun = rasar
RB = 6                       # bollens radie
RAS_C = (rgb(220, 225, 240), rgb(240, 60, 60), rgb(80, 220, 110), rgb(250, 210, 40), rgb(170, 110, 60))
RAS_BG = [mix((20, 10, 50), (70, 20, 60), y / (VH - 1)) for y in range(VH)]


def play(lcd, keys):
    return v_play(lcd, keys, "RAS", VIOLET, ("Fall genom halen", "innan taket med", "spikar nar dig!", "Vanster/hoger rullar."), "ras", ras_game)


def ras_row(y, rows):
    """En rad med en eller två plattformar."""
    out = []
    n = 1 if random.random() < 0.5 else 2
    for k in range(n):
        w = random.randint(50, 90)
        x = random.randint(8, VW - 8 - w) if n == 1 else (random.randint(8, 100 - w // 2) if k == 0 else random.randint(130, VW - 8 - w))
        r = random.random()
        hard = min(0.4, rows * 0.006)
        if rows < 3:
            typ = 0
        elif r < 0.12 + hard:
            typ = 1
        elif r < 0.24 + hard:
            typ = 4
        elif r < 0.34 + hard:
            typ = 3
        elif r < 0.42 + hard:
            typ = 2
        else:
            typ = 0
        p = [float(x), float(y), w, typ, random.choice((-1, 1)), 0]   # x, y, bredd, typ, rullriktning, ras-tid
        out.append(p)
    return out


def ras_game(lcd, fb, keys, L, R):
    plats = []
    y = 120.0
    while y < VH + 40:
        plats += ras_row(y, 0)
        y += 56
    start = plats[0]
    bx, by = start[0] + start[2] / 2, start[1] - RB
    vy = 0.0
    lives = 3
    inv = 60
    coins = 0
    passed = 0
    items = []               # [platta, dx, typ] typ 0 mynt, 1 hjärta
    parts = Particles(50)
    pops = Popups()
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return None
        rise = min(4.2, 1.3 + passed * 0.035)
        if keys.held(L):
            bx -= 4.2
        if keys.held(R):
            bx += 4.2
        bx = max(RB, min(VW - RB, bx))
        # plattformar åker upp
        for p in plats:
            p[1] -= rise
            if p[5] > 0:
                p[5] -= 1
                if p[5] == 0:
                    p[3] = -1                                   # rasade
                    parts.burst(p[0] + p[2] / 2, p[1], RAS_C[4], 12, 2, 16, 0.3)
        kept = []
        for p in plats:
            if p[1] < 14:
                if p[3] >= 0:
                    passed += 1
            else:
                kept.append(p)
        plats = kept
        low = max(p[1] for p in plats) if plats else 0
        if low < VH - 20:
            row = ras_row(low + 56, passed)
            plats += row
            if random.random() < 0.35:
                q = random.choice(row)
                if q[3] in (0, 3, 4):
                    items.append([q, random.uniform(8, q[2] - 8), 1 if random.random() < 0.06 else 0])
        items = [it for it in items if it[0] in plats and it[0][3] >= 0]
        # bollen
        vy = min(8.0, vy + 0.55)
        ny = by + vy
        on = None
        for p in plats:
            if p[3] < 0:
                continue
            if p[0] - RB / 2 < bx < p[0] + p[2] + RB / 2 and by + RB <= p[1] + rise + 1 and ny + RB >= p[1]:
                on = p
                break
        if on:
            by = on[1] - RB
            if on[3] == 2:
                vy = -7.5
                parts.burst(bx, by + RB, RAS_C[2], 6, 1.5, 8)
            else:
                vy = 0.0
            if on[3] == 3:
                bx += 2.2 * on[4]
            if on[3] == 4 and on[5] == 0:
                on[5] = 16
            if on[3] == 1 and not inv:
                lives -= 1
                inv = 60
                vy = -6.0
                parts.burst(bx, by, CORAL, 16, 3, 16)
                pops.add(bx, by - 14, "AJ!", CORAL)
        else:
            by = ny
        for it in items:
            ix, iy = it[0][0] + it[1], it[0][1] - 10
            if abs(ix - bx) < 10 and abs(iy - by) < 12:
                if it[2] == 0:
                    coins += 1
                    pops.add(ix, iy - 8, "+20", YELLOW)
                    if coins >= 20:
                        goal("ras", 1)
                else:
                    lives = min(5, lives + 1)
                    pops.add(ix, iy - 8, "+1 LIV", PINK)
                parts.burst(ix, iy, YELLOW, 8, 2, 10)
                it[0] = None
        items = [it for it in items if it[0] is not None]
        if inv:
            inv -= 1
        if (by - RB < 18 or by > VH + RB) and not inv:
            lives -= 1
            parts.burst(bx, min(by, VH - 4), CORAL, 20, 3, 18)
            inv = 70
            if lives > 0:                                       # börja om på en säker platta
                best = None
                for p in plats:
                    if p[3] in (0, 3) and 120 < p[1] < 260:
                        best = p
                        break
                if best is None:
                    best = plats[len(plats) // 2]
                    best[3] = 0
                bx, by, vy = best[0] + best[2] / 2, best[1] - RB, 0.0
        score = passed * 10 + coins * 20
        if score >= 500:
            goal("ras", 0)
        if score >= 2000:
            goal("ras", 2)
        if lives <= 0:
            for k in range(25):
                t1 = time.ticks_ms()
                gradient(fb, RAS_BG, 0, VH)
                parts.draw(fb)
                stext(fb, "SLUT!", 130, CORAL, 4, VW // 2)
                lcd.show()
                wait(t1)
            return score
        # --- rita ---
        gradient(fb, RAS_BG, 0, VH)
        off = int(t * rise) % 32
        for yy in range(-32, VH, 32):
            fb.fill_rect(0, yy - off + 32, 4, 30, rgb(60, 40, 90))
            fb.fill_rect(VW - 4, yy - off + 48, 4, 30, rgb(60, 40, 90))
        for p in plats:
            if p[3] < 0:
                continue
            x, yy, w = int(p[0]), int(p[1]), p[2]
            c = RAS_C[p[3]]
            dx = random.randint(-1, 1) if p[5] else 0
            fb.fill_rect(x + dx, yy, w, 7, c)
            fb.hline(x + dx, yy, w, WHITE)
            if p[3] == 1:
                for k in range(0, w - 4, 6):
                    tri(fb, x + k, yy, x + k + 6, yy, x + k + 3, yy - 6, c)
            elif p[3] == 3:
                for k in range((t * 2 * p[4]) % 8, w, 8):
                    fb.vline(x + k, yy + 2, 4, BLACK)
            elif p[3] == 2:
                fb.fill_rect(x + w // 2 - 6, yy - 3, 12, 3, WHITE)
        for it in items:
            ix, iy = int(it[0][0] + it[1]), int(it[0][1] - 10)
            if it[2] == 0:
                wdt = int(5 * abs(math.sin(t * 0.15 + ix)))
                fb.ellipse(ix, iy, wdt + 1, 6, YELLOW, True)
            else:
                fb.ellipse(ix - 3, iy - 2, 4, 4, PINK, True)
                fb.ellipse(ix + 3, iy - 2, 4, 4, PINK, True)
                tri(fb, ix - 7, iy - 1, ix + 7, iy - 1, ix, iy + 7, PINK)
        for k in range(0, VW, 10):                                  # spiktaket
            tri(fb, k, 0, k + 10, 0, k + 5, 14, rgb(200, 200, 220))
        if not inv or (t // 3) % 2:
            fb.ellipse(int(bx), int(by), RB, RB, AMBER, True)
            fb.ellipse(int(bx) - 2, int(by) - 2, 2, 2, WHITE, True)
        parts.draw(fb)
        pops.draw(fb)
        big(fb, str(score), 6, 18, WHITE, 2)
        for i in range(lives):
            fb.ellipse(VW - 14 - i * 14, 26, 5, 5, PINK, True)
        if t < 60 and (t // 10) % 2 == 0:
            ctext(fb, "%d <    > %d" % (L, R), 280, WHITE, 2, VW // 2)
        lcd.show()
        t += 1
        wait(t0)
