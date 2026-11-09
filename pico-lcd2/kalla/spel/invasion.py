# INVASION: 0 vänster, 1 höger, 2 skjut, 3 superlaser.
SPR_SQUID = (("...##...", "..####..", ".######.", "##.##.##", "########", "..#..#..", ".#.##.#.", "#.#..#.#"),
             ("...##...", "..####..", ".######.", "##.##.##", "########", ".#.##.#.", "#......#", ".#....#."))
SPR_CRAB = (("..#.....#..", "...#...#...", "..#######..", ".##.###.##.", "###########", "#.#######.#", "#.#.....#.#", "...##.##..."),
            ("..#.....#..", "#..#...#..#", "#.#######.#", "###.###.###", "###########", ".#########.", "..#.....#..", ".#.......#."))
SPR_OCTO = (("....####....", ".##########.", "############", "###..##..###", "############", "...##..##...", "..##.##.##..", "##........##"),
            ("....####....", ".##########.", "############", "###..##..###", "############", "..###..###..", ".##..##..##.", "..##....##.."))
SPR_SHIP = ("......#......", ".....###.....", ".....###.....", ".###########.", "#############", "#############", "#############")
SPR_UFO = (".....######.....", "...##########...", "..############..", ".##.##.##.##.##.", "################", "..###..##..###..", "...#........#...")
I_COLS = (PINK, TEAL, TEAL, LIME, LIME)
I_POINTS = (30, 20, 20, 10, 10)


def sprite(rows, col, s=2):
    """Gör en liten bild (FrameBuffer) av en textmall. Svart = genomskinligt."""
    w, h = len(rows[0]) * s, len(rows) * s
    buf = bytearray(w * h * 2)
    fb = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                fb.fill_rect(x * s, y * s, s, s, col)
    return (fb, w, h, buf)


def bunker():
    b = bytearray(12 * 8)
    for y in range(8):
        for x in range(12):
            corner = (y == 0 and (x < 2 or x > 9)) or (y == 1 and (x == 0 or x == 11))
            hole = y >= 5 and 3 <= x <= 8
            b[y * 12 + x] = 0 if corner or hole else 1
    return b


BUNK_X = (34, 106, 178, 250)
BUNK_Y = 176
BUNK_C = rgb(90, 230, 120)


@native
def draw_bunkers(fb, bunks):
    for i in range(4):
        b = bunks[i]
        bx = BUNK_X[i]
        for y in range(8):
            for x in range(12):
                if b[y * 12 + x]:
                    fb.fill_rect(bx + x * 3, BUNK_Y + y * 3, 3, 3, BUNK_C)


def bunker_hit(bunks, x, y):
    """Träffar punkten ett skydd? Gör då ett hål och returnerar True."""
    for i in range(4):
        bx = BUNK_X[i]
        if bx <= x < bx + 36 and BUNK_Y <= y < BUNK_Y + 24:
            cx, cy = int(x - bx) // 3, int(y - BUNK_Y) // 3
            b = bunks[i]
            if b[cy * 12 + cx]:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < 12 and 0 <= ny < 8 and (dx == 0 and dy == 0 or random.random() < 0.5):
                            b[ny * 12 + nx] = 0
                return True
    return False


def play(lcd, keys):
    spr = [[sprite(SPR_SQUID[f], PINK) for f in (0, 1)],
           [sprite(SPR_CRAB[f], TEAL) for f in (0, 1)],
           [sprite(SPR_OCTO[f], LIME) for f in (0, 1)]]
    kind_of_row = (0, 1, 1, 2, 2)
    ship = sprite(SPR_SHIP, SKY)
    ufo_s = sprite(SPR_UFO, CORAL)
    stars = Stars(40)
    parts = Particles(160)
    pops = Popups()
    shake = Shake()
    score, lives, wave = 0, 3, 0
    px = W / 2
    inv = 0
    cool = 0
    power, power_t = "", 0
    shield = False
    meter = 0
    beam = 0
    t = 0
    keys.wait_release()
    while True:                                           # en våg
        wave += 1
        alive = [[True] * 8 for _ in range(5)]
        fx, fy = 26.0, 30.0 + min(wave - 1, 5) * 8
        fdir = 1
        step_t = 0
        frame = 0
        shots, aliens_shots, drops = [], [], []
        bunks = [bunker() for _ in range(4)]
        ufo = None
        banner = 60
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            n_alive = sum(sum(1 for a in r if a) for r in alive)
            if n_alive == 0:
                break
            # --- Spelaren ---
            if keys.held(K0):
                px -= 3.2
            if keys.held(K1):
                px += 3.2
            px = max(14, min(W - 14, px))
            if cool > 0:
                cool -= 1
            if keys.held(K2) and cool == 0 and len(shots) < 6:
                shots.append([px, 206.0, 0.0])
                if power == "T":
                    shots.append([px, 206.0, -1.5])
                    shots.append([px, 206.0, 1.5])
                cool = 6 if power == "R" else 14
            if keys.pressed(K3) and meter >= 10:
                goal("invasion", 1)
                meter = 0
                beam = 20
                shake.hit(6)
            if power_t > 0:
                power_t -= 1
                if power_t == 0:
                    power = ""
            # --- Formationen ---
            step_t += 1
            interval = max(1, n_alive // 3)
            if step_t >= interval:
                step_t = 0
                frame ^= 1
                minx, maxx = W, 0
                maxy = 0
                for r in range(5):
                    for c in range(8):
                        if alive[r][c]:
                            x = fx + c * 28
                            minx = min(minx, x)
                            maxx = max(maxx, x + 24)
                            maxy = max(maxy, fy + r * 20 + 16)
                if (fdir > 0 and maxx + 4 > W - 4) or (fdir < 0 and minx - 4 < 4):
                    fdir = -fdir
                    fy += 8
                else:
                    fx += 4 * fdir
                if maxy >= BUNK_Y:                         # rensar skydden de rör vid
                    for i in range(4):
                        for y in range(8):
                            if BUNK_Y + y * 3 < maxy:
                                for x in range(12):
                                    bunks[i][y * 12 + x] = 0
                if maxy >= 206:
                    lives = 0
            if random.random() < 0.025 + wave * 0.005 and len(aliens_shots) < 2 + wave // 2:
                cols = [c for c in range(8) if any(alive[r][c] for r in range(5))]
                if cols:
                    c = random.choice(cols)
                    r = max(r for r in range(5) if alive[r][c])
                    aliens_shots.append([fx + c * 28 + 11, fy + r * 20 + 16])
            # --- UFO ---
            if ufo is None and random.random() < 0.003:
                d = random.choice((-1, 1))
                ufo = [-34.0 if d > 0 else W + 2.0, 1.6 * d]
            if ufo:
                ufo[0] += ufo[1]
                if ufo[0] < -40 or ufo[0] > W + 8:
                    ufo = None
            # --- Skott ---
            for s in shots:
                s[1] -= 7
                s[0] += s[2]
                if s[1] < 16 or bunker_hit(bunks, s[0], s[1]):
                    s[1] = -99
                    continue
                if ufo and ufo[0] <= s[0] <= ufo[0] + 32 and 18 <= s[1] <= 32:
                    pts = random.choice((50, 100, 150, 300))
                    score += pts
                    pops.add(ufo[0] + 16, 20, str(pts), CORAL)
                    parts.burst(ufo[0] + 16, 25, CORAL, 24, 3.5, 22)
                    shake.hit(5)
                    ufo = None
                    s[1] = -99
                    continue
                r = int((s[1] - fy) // 20)
                c = int((s[0] - fx) // 28)
                if 0 <= r < 5 and 0 <= c < 8 and alive[r][c]:
                    ax, ay = fx + c * 28, fy + r * 20
                    w = spr[kind_of_row[r]][0][1]
                    if ax <= s[0] <= ax + w and ay <= s[1] <= ay + 16:
                        alive[r][c] = False
                        s[1] = -99
                        score += I_POINTS[r]
                        meter = min(10, meter + 1)
                        parts.burst(ax + w / 2, ay + 8, I_COLS[r], 12, 2.5, 14)
                        pops.add(ax + w / 2, ay, str(I_POINTS[r]), I_COLS[r])
                        if random.random() < 0.08:
                            drops.append([ax + w / 2, ay + 8, random.choice("TRS")])
            shots = [s for s in shots if s[1] > 0]
            for s in aliens_shots:
                s[1] += 3.2 + wave * 0.2
                if bunker_hit(bunks, s[0], s[1]):
                    s[1] = H + 99
                elif inv == 0 and abs(s[0] - px) < 12 and 204 <= s[1] <= 220:
                    s[1] = H + 99
                    if shield:
                        shield = False
                        parts.burst(px, 210, TEAL, 14, 2.5, 14)
                    else:
                        lives -= 1
                        inv = 90
                        parts.burst(px, 210, SKY, 30, 4, 28)
                        parts.burst(px, 210, AMBER, 20, 3, 22)
                        shake.hit(9)
            aliens_shots = [s for s in aliens_shots if s[1] < H]
            for d in drops:
                d[1] += 1.6
                if abs(d[0] - px) < 16 and 204 <= d[1] <= 222:
                    d[1] = H + 99
                    if d[2] == "S":
                        shield = True
                        pops.add(px, 190, "SKOLD", TEAL)
                    else:
                        power, power_t = d[2], 420
                        pops.add(px, 190, "TRIPPEL" if d[2] == "T" else "SNABB", AMBER)
            drops = [d for d in drops if d[1] < H]
            # --- Superlaser ---
            if beam > 0:
                beam -= 1
                for r in range(5):
                    for c in range(8):
                        ax = fx + c * 28
                        w = spr[kind_of_row[r]][0][1]
                        if alive[r][c] and ax - 6 <= px <= ax + w + 6:
                            alive[r][c] = False
                            score += I_POINTS[r]
                            parts.burst(ax + w / 2, fy + r * 20 + 8, I_COLS[r], 10, 3, 14)
                aliens_shots = [s for s in aliens_shots if abs(s[0] - px) > 8]
                if ufo and ufo[0] <= px <= ufo[0] + 32:
                    score += 300
                    pops.add(ufo[0] + 16, 20, "300", CORAL)
                    ufo = None
            if inv > 0:
                inv -= 1
            if score >= 3000:
                goal("invasion", 2)
            if lives <= 0:
                lcd.show()
                time.sleep_ms(600)
                return score

            # --- Rita ---
            ox, oy = shake.offset()
            lcd.fill(BLACK)
            stars.draw(lcd, 0.0, 0.3)
            for r in range(5):
                sp = spr[kind_of_row[r]][frame]
                for c in range(8):
                    if alive[r][c]:
                        lcd.blit(sp[0], int(fx + c * 28) + ox, int(fy + r * 20) + oy, 0)
            if ufo:
                lcd.blit(ufo_s[0], int(ufo[0]) + ox, 18 + oy, 0)
            draw_bunkers(lcd, bunks)
            for s in shots:
                lcd.fill_rect(int(s[0]) - 1 + ox, int(s[1]) + oy, 2, 7, YELLOW)
            for s in aliens_shots:
                zz = (t // 3) % 2
                lcd.fill_rect(int(s[0]) - 1 + zz + ox, int(s[1]) + oy, 2, 4, CORAL)
                lcd.fill_rect(int(s[0]) - zz + ox, int(s[1]) + 4 + oy, 2, 4, CORAL)
            for d in drops:
                c = {"T": CORAL, "R": AMBER, "S": TEAL}[d[2]]
                lcd.fill_rect(int(d[0]) - 6, int(d[1]) - 5, 12, 10, c)
                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
            if beam > 0:
                w = 4 + (beam % 3) * 2
                lcd.fill_rect(int(px) - w // 2 - 2, 16, w + 4, 196, PINK)
                lcd.fill_rect(int(px) - w // 2, 16, w, 196, WHITE)
            if inv == 0 or (t // 4) % 2:
                lcd.blit(ship[0], int(px) - 13 + ox, 206 + oy, 0)
                if shield:
                    lcd.ellipse(int(px) + ox, 212 + oy, 18, 11, TEAL)
            parts.draw(lcd, ox, oy)
            pops.draw(lcd, ox, oy)
            lcd.fill_rect(0, 0, W, 14, BG)
            lcd.text(str(score), 4, 3, WHITE)
            lcd.text("VAG %d" % wave, 132, 3, GRAY)
            for i in range(lives):
                lcd.blit(ship[0], W - 30 - i * 30, 0, 0)
            lcd.fill_rect(4, H - 6, 60, 4, LINE)
            lcd.fill_rect(4, H - 6, meter * 6, 4, PINK if meter >= 10 else VIOLET)
            if meter >= 10 and (t // 6) % 2:
                lcd.text("3 LASER!", 70, H - 9, PINK)
            if power:
                lcd.text("TRIPPEL" if power == "T" else "SNABB", W - 60, H - 9, AMBER)
            if banner > 0:
                banner -= 1
                stext(lcd, "VAG %d" % wave, 110, WHITE, 3)
            lcd.show()
            t += 1
            wait(t0)
        score += 100 * wave
        if wave >= 3:
            goal("invasion", 0)
        pops.add(W // 2, 130, "VAG KLAR +%d" % (100 * wave), LIME, 2)


