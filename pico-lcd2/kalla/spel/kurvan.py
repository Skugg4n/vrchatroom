# KURVAN: P1 0/3, P2 1/2.
KY0 = 20
KW, KH = W // 2, (H - KY0) // 2
K_SPEED = 1.5
K_TURN = 0.085


def play(lcd, keys):
    mode = choose(lcd, keys, "KURVAN", ("MOT DATORN", "MOT 2 DATORER", "2 SPELARE"), TEAL,
                  "Sist kvar vinner rundan. Forst till 5!")
    if mode is None:
        return None
    n = 3 if mode == 1 else 2
    cpu = [False, mode != 2, True][:n]
    names = ["DU" if mode != 2 else "SPELARE 1", "DATORN" if mode == 0 else ("DATOR 1" if mode == 1 else "SPELARE 2"),
             "DATOR 2"][:n]
    ctrl = [(K0, K3), (K1, K2), None]
    points = [0] * n
    target = 5
    grid = bytearray(KW * KH)

    def free(px, py):
        if px < 1 or py < KY0 + 1 or px >= W - 1 or py >= H - 1:
            return False
        return grid[(int(py - KY0) >> 1) * KW + (int(px) >> 1)] == 0

    def look(p, turn, steps=34):
        x, y, a = p[0], p[1], p[2]
        for i in range(steps):
            a += turn * K_TURN
            x += math.cos(a) * K_SPEED * 2
            y += math.sin(a) * K_SPEED * 2
            if not free(x, y):
                return i
        return steps

    while True:                                    # en runda
        for i in range(len(grid)):
            grid[i] = 0
        pl = []
        for i in range(n):
            while True:
                x = random.uniform(50, W - 50)
                y = random.uniform(KY0 + 40, H - 40)
                if all((x - q[0]) ** 2 + (y - q[1]) ** 2 > 3600 for q in pl):
                    break
            a = math.atan2(KY0 + (H - KY0) / 2 - y, W / 2 - x) + random.uniform(-0.8, 0.8)
            pl.append([x, y, a, True, random.randint(60, 140), 0, 0, x, y])   # x,y,vinkel,lever,till glapp,glapp,ai-sväng,förra x,y
        for c in range(75):                        # nedräkning
            t0 = time.ticks_ms()
            keys.update()
            k_field(lcd, names, points, n)
            for i, p in enumerate(pl):
                ex, ey = p[0] + math.cos(p[2]) * 14, p[1] + math.sin(p[2]) * 14
                lcd.line(int(p[0]), int(p[1]), int(ex), int(ey), K_COLS[i])
                lcd.ellipse(int(p[0]), int(p[1]), 3, 3, K_COLS[i], True)
                if not cpu[i] and (c // 8) % 2 == 0:
                    lab = "%d/%d" % ctrl[i]
                    lcd.text(lab, int(p[0]) - 12, int(p[1]) + 8, WHITE)
            stext(lcd, str(3 - c // 25), 100, WHITE, 5)
            lcd.show()
            wait(t0)
        k_field(lcd, names, points, n)
        t = 0
        keys.wait_release()
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return points[0]
            for i, p in enumerate(pl):
                if not p[3]:
                    continue
                if cpu[i]:
                    if t % 3 == i % 3:
                        best, bt = -1, 0
                        for turn in (0, -1, 1):
                            s = look(p, turn) + random.random() * 2
                            if s > best:
                                best, bt = s, turn
                        p[6] = bt
                    turn = p[6]
                else:
                    turn = (-1 if keys.held(ctrl[i][0]) else 0) + (1 if keys.held(ctrl[i][1]) else 0)
                p[2] += turn * K_TURN
                p[7], p[8] = p[0], p[1]
                p[0] += math.cos(p[2]) * K_SPEED
                p[1] += math.sin(p[2]) * K_SPEED
                ax = p[0] + math.cos(p[2]) * 2.5
                ay = p[1] + math.sin(p[2]) * 2.5
                if not free(ax, ay):
                    p[3] = False
                    lcd.ellipse(int(p[0]), int(p[1]), 6, 6, WHITE, False)
                    lcd.ellipse(int(p[0]), int(p[1]), 4, 4, K_COLS[i], True)
                    continue
                # Glapp i svansen ibland
                p[4] -= 1
                if p[4] <= 0:
                    p[5] = 7
                    p[4] = random.randint(70, 150)
                if p[5] > 0:
                    p[5] -= 1
                    if grid[(int(p[8] - KY0) >> 1) * KW + (int(p[7]) >> 1)] == 0:
                        lcd.fill_rect(int(p[7]) - 1, int(p[8]) - 1, 3, 3, BG)
                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, WHITE)
                else:
                    lcd.fill_rect(int(p[0]) - 1, int(p[1]) - 1, 3, 3, K_COLS[i])
                    grid[(int(p[1] - KY0) >> 1) * KW + (int(p[0]) >> 1)] = i + 1
            alive = [i for i, p in enumerate(pl) if p[3]]
            hud_k(lcd, names, points, n)
            lcd.show()
            t += 1
            wait(t0, 25)
            if len(alive) <= 1:
                if alive:
                    points[alive[0]] += 1
                    if alive[0] == 0 and mode != 2:
                        goal("kurvan", 0)
                    msg = "%s TAR RUNDAN" % names[alive[0]]
                    col = K_COLS[alive[0]]
                else:
                    msg, col = "OAVGJORT", GRAY
                lcd.fill_rect(30, 96, 260, 44, BG)
                lcd.rect(30, 96, 260, 44, col)
                ctext(lcd, msg, 106, col, 1 if len(msg) > 18 else 2)
                ctext(lcd, "  ".join("%d" % q for q in points), 126, WHITE)
                hud_k(lcd, names, points, n)
                lcd.show()
                time.sleep_ms(1600)
                break
        if max(points) >= target:
            w = points.index(max(points))
            if w == 0 and mode == 0:
                goal("kurvan", 1)
            if w == 0 and mode == 1:
                goal("kurvan", 2)
            return ("%s VANN!" % names[w], points[0], "kurvan" if mode != 2 else None,
                    "Dina vunna rundor:", False, str)


def k_field(lcd, names, points, n):
    lcd.fill(BG)
    lcd.rect(0, KY0, W, H - KY0, LINE)
    lcd.rect(1, KY0 + 1, W - 2, H - KY0 - 2, LINE)
    hud_k(lcd, names, points, n)


def hud_k(lcd, names, points, n):
    lcd.fill_rect(0, 0, W, KY0, BG)
    for i in range(n):
        x = 6 + i * 106
        lcd.fill_rect(x, 6, 8, 8, K_COLS[i])
        lcd.text("%s %d" % (names[i], points[i]), x + 12, 6, K_COLS[i])


