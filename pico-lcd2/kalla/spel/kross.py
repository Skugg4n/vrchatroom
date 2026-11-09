# KROSS: 0 vänster, 1 höger, 2/3 skjut iväg bollen (2 = laser).
K_LEVELS = (
    ("1111111111", "2222222222", "3333333333", "4444444444", "5555555555"),
    ("..AAAAAA..", ".A111111A.", "A11XXXX11A", "A11111111A", ".AAAAAAAA."),
    ("M..1111..M", "M.1BBBB1.M", "M.1B33B1.M", "M.1BBBB1.M", "M..1111..M"),
    ("X1X1X1X1X1", "1A1A1A1A1A", "2B2B2B2B2B", "1A1A1A1A1A", "X1X1X1X1X1"),
    ("....11....", "...1221...", "..123321..", ".12344321.", "1234554321", ".AAAAAAAA.", "MM......MM"),
    ("AXAXAXAXAX", "1111111111", "MMMM..MMMM", "2222222222", "B........B", "BBBBBBBBBB"),
)
BR_RAW = ((255, 95, 100), (255, 170, 60), (255, 225, 70), (125, 230, 110), (80, 165, 255))
BR_N = [rgb(*c) for c in BR_RAW]
BR_L = [mix(c, (255, 255, 255), 0.5) for c in BR_RAW]
BR_D = [mix(c, (0, 0, 0), 0.4) for c in BR_RAW]
BR_HARD = (rgb(120, 70, 210), rgb(160, 110, 255), rgb(200, 160, 255))
BR_METAL = rgb(150, 155, 175)
BR_X = rgb(255, 120, 40)
B_BW, B_BH = 30, 11
B_TOP = 26
PADY = 222


def play(lcd, keys):
    parts = Particles(140)
    pops = Popups()
    shake = Shake()
    score, lives, lvl = 0, 3, 0
    bg = [mix((18, 14, 40), (8, 22, 44), y / (H - 1)) for y in range(H)]
    while True:                                   # en bana
        layout = K_LEVELS[lvl % len(K_LEVELS)]
        speed0 = min(3.6 + lvl * 0.3, 6.0)
        typ = bytearray(10 * 8)                   # 0 ingen, 1-5 vanlig, 6 hård, 8 metall, 9 sprängsten
        hp = bytearray(10 * 8)
        for r, row in enumerate(layout):
            for c, ch in enumerate(row):
                i = r * 10 + c
                if ch in "12345":
                    typ[i], hp[i] = int(ch), 1
                elif ch == "A":
                    typ[i], hp[i] = 6, 2
                elif ch == "B":
                    typ[i], hp[i] = 6, 3
                elif ch == "M":
                    typ[i], hp[i] = 8, 255
                elif ch == "X":
                    typ[i], hp[i] = 9, 1
        pw, pdx = 48, (W - 48) / 2
        balls = [[0.0, 0.0, 0.0, 0.0]]
        attached = True
        drops = []
        lasers = []
        effects = {}                              # namn -> bilder kvar
        banner = 50
        t = 0
        keys.wait_release()

        def left():
            for i in range(80):
                if typ[i] and typ[i] != 8:
                    return True
            return False

        def destroy(i, chain=0):
            nonlocal score
            tp = typ[i]
            typ[i] = 0
            hp[i] = 0
            r, c = i // 10, i % 10
            bx, by = c * 32 + 1 + B_BW / 2, B_TOP + r * 13 + B_BH / 2
            col = BR_N[tp - 1] if tp <= 5 else (BR_X if tp == 9 else BR_HARD[1])
            parts.burst(bx, by, col, 8, 2.5, 14)
            gain = 10 if tp <= 5 else (30 if tp == 6 else 40)
            score += gain
            if random.random() < 0.14:
                drops.append([bx, by, random.choice("WMSL+W")])
            if tp == 9:                               # sprängsten tar grannarna
                shake.hit(5)
                parts.burst(bx, by, AMBER, 18, 4, 18)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 10:
                            j = nr * 10 + nc
                            if typ[j] and typ[j] != 8:
                                destroy(j, chain + 1)

        def hit_brick(x, y):
            r = int((y - B_TOP) // 13)
            c = int(x // 32)
            if 0 <= r < 8 and 0 <= c < 10:
                i = r * 10 + c
                if typ[i]:
                    if typ[i] != 8:
                        hp[i] -= 1
                        if hp[i] == 0:
                            destroy(i)
                    return True
            return False

        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            wide = effects.get("W", 0) > 0
            pw = 72 if wide else 48
            if keys.held(K0):
                pdx -= 6
            if keys.held(K1):
                pdx += 6
            pdx = max(0, min(W - pw, pdx))
            slow = 0.7 if effects.get("S", 0) else 1.0
            spd = speed0 * slow
            if attached:
                balls = [[pdx + pw / 2, PADY - 5.0, 0.0, 0.0]]
                if banner == 0 and (keys.pressed(K2) or keys.pressed(K3)):
                    attached = False
                    a = random.uniform(-0.5, 0.5)
                    balls[0][2], balls[0][3] = math.sin(a) * spd, -math.cos(a) * spd
            elif effects.get("L", 0) and keys.pressed(K2):
                lasers.append([pdx + 4, PADY - 4.0])
                lasers.append([pdx + pw - 4, PADY - 4.0])
            for k in list(effects):
                effects[k] -= 1
                if effects[k] <= 0:
                    del effects[k]
            # --- Bollar ---
            keep = []
            for b in balls:
                if attached:
                    keep.append(b)
                    continue
                sp = math.sqrt(b[2] * b[2] + b[3] * b[3])
                if sp > 0:
                    b[2] *= spd / sp
                    b[3] *= spd / sp
                for _ in range(2):
                    b[0] += b[2] / 2
                    if b[0] < 3 or b[0] > W - 3:
                        b[2] = -b[2]
                        b[0] = max(3, min(W - 3, b[0]))
                    elif hit_brick(b[0] + (3 if b[2] > 0 else -3), b[1]):
                        b[2] = -b[2]
                        b[0] += b[2] / 2
                    b[1] += b[3] / 2
                    if b[1] < 20:
                        b[3] = abs(b[3])
                    elif hit_brick(b[0], b[1] + (3 if b[3] > 0 else -3)):
                        b[3] = -b[3]
                        b[1] += b[3] / 2
                if b[3] > 0 and PADY - 4 <= b[1] <= PADY + 4 and pdx - 3 <= b[0] <= pdx + pw + 3:
                    rel = (b[0] - (pdx + pw / 2)) / (pw / 2)
                    a = max(-1.0, min(1.0, rel)) * 1.1
                    b[2], b[3] = math.sin(a) * spd, -math.cos(a) * spd
                    b[1] = PADY - 5
                if b[1] < H + 5:
                    keep.append(b)
            balls = keep
            if not balls:
                lives -= 1
                shake.hit(8)
                if lives <= 0:
                    return score
                attached = True
                effects = {}
                balls = [[0.0, 0.0, 0.0, 0.0]]
            for l in lasers:
                l[1] -= 7
                if hit_brick(l[0], l[1]):
                    l[1] = -9
            lasers = [l for l in lasers if l[1] > 18]
            for d in drops:
                d[1] += 1.8
                if PADY - 6 <= d[1] <= PADY + 6 and pdx - 6 <= d[0] <= pdx + pw + 6:
                    d[1] = H + 99
                    score += 50
                    k = d[2]
                    if k == "M" and balls and not attached:
                        b = balls[0]
                        for a in (-0.6, 0.6):
                            balls.append([b[0], b[1], math.sin(a) * spd, -math.cos(a) * spd])
                        pops.add(d[0], PADY - 20, "MULTIBOLL", PINK)
                        goal("kross", 1)
                    elif k == "+":
                        lives += 1
                        pops.add(d[0], PADY - 20, "+1 LIV", LIME)
                    else:
                        effects[k] = 500
                        pops.add(d[0], PADY - 20, {"W": "BRED", "S": "LANGSAM", "L": "LASER"}.get(k, ""), AMBER)
            drops = [d for d in drops if d[1] < H]
            if not left():
                score += 500
                lvl += 1
                if lvl >= 2:
                    goal("kross", 0)
                if lvl >= 5:
                    goal("kross", 2)
                pops.add(W // 2, 120, "BANAN KLAR! +500", LIME, 2)
                for _ in range(40):
                    t1 = time.ticks_ms()
                    gradient(lcd, bg)
                    pops.draw(lcd)
                    parts.draw(lcd)
                    lcd.show()
                    wait(t1)
                break
            if banner > 0:
                banner -= 1

            # --- Rita ---
            ox, oy = shake.offset()
            gradient(lcd, bg)
            for i in range(80):
                tp = typ[i]
                if not tp:
                    continue
                x = (i % 10) * 32 + 1 + ox
                y = B_TOP + (i // 10) * 13 + oy
                if tp <= 5:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_N[tp - 1])
                    lcd.hline(x, y, B_BW, BR_L[tp - 1])
                    lcd.hline(x, y + B_BH - 1, B_BW, BR_D[tp - 1])
                elif tp == 6:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_HARD[min(2, hp[i] - 1)])
                    lcd.rect(x, y, B_BW, B_BH, WHITE if hp[i] >= 3 else BR_HARD[2])
                elif tp == 8:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_METAL)
                    lcd.hline(x, y + 2, B_BW, WHITE)
                    lcd.rect(x, y, B_BW, B_BH, DIM)
                else:
                    lcd.fill_rect(x, y, B_BW, B_BH, BR_X if (t // 6) % 2 else CORAL)
                    lcd.text("X", x + 11, y + 2, WHITE)
            for d in drops:
                c = {"W": SKY, "M": PINK, "S": TEAL, "L": CORAL, "+": LIME}[d[2]]
                lcd.fill_rect(int(d[0]) - 8, int(d[1]) - 5, 16, 10, c)
                lcd.text(d[2], int(d[0]) - 3, int(d[1]) - 4, BG)
            for l in lasers:
                lcd.fill_rect(int(l[0]) - 1, int(l[1]), 2, 8, CORAL)
            pc = CORAL if effects.get("L", 0) else SKY
            lcd.fill_rect(int(pdx) + ox, PADY + oy, pw, 7, pc)
            lcd.hline(int(pdx) + 2 + ox, PADY + 1 + oy, pw - 4, WHITE)
            for b in balls:
                lcd.ellipse(int(b[0]) + ox, int(b[1]) + oy, 3, 3, WHITE, True)
            parts.draw(lcd, ox, oy)
            pops.draw(lcd, ox, oy)
            lcd.fill_rect(0, 0, W, 16, BG)
            lcd.text(str(score), 4, 4, WHITE)
            lcd.text("BANA %d" % (lvl + 1), 130, 4, AMBER)
            for i in range(lives):
                lcd.ellipse(W - 10 - i * 12, 8, 4, 4, CORAL, True)
            if banner > 0:
                stext(lcd, "BANA %d" % (lvl + 1), 130, WHITE, 3)
            elif attached and (t // 10) % 2 == 0:
                ctext(lcd, "2  skjut ivag bollen", 170, GRAY)
            lcd.show()
            t += 1
            wait(t0)


