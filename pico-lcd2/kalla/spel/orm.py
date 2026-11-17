# ORM: styr ormen till äpplena. Pilarna i hörnen: 0 upp, 1 höger, 2 ner, 3 vänster.
# Var 8:e äpple: ny nivå med nya väggar. Guldäpple = mycket poäng, chili = turbo.
OC = 12
OW, OH = 26, 17
OX, OY = (W - OW * OC) // 2, 30
O_LEVELS = (   # väggar som rektanglar (x, y, b, h) i rutor
    (),
    ((5, 4, 16, 1), (5, 12, 16, 1)),
    ((8, 2, 1, 5), (8, 10, 1, 5), (17, 2, 1, 5), (17, 10, 1, 5)),
    ((5, 3, 4, 3), (17, 3, 4, 3), (5, 11, 4, 3), (17, 11, 4, 3), (12, 6, 2, 1), (12, 10, 2, 1)),
    ((0, 4, 10, 1), (16, 4, 10, 1), (0, 12, 10, 1), (16, 12, 10, 1), (12, 0, 2, 6), (12, 11, 2, 6)),
)
O_NAMES = ("ANGEN", "KORRIDOREN", "PELARNA", "RUMMEN", "LABYRINTEN")
O_BG = [mix((6, 30, 20), (14, 50, 30), y / (H - 1)) for y in range(H)]
O_GRID = rgb(24, 64, 40)
O_WALL = rgb(120, 90, 60)
O_BODY = (rgb(90, 220, 90), rgb(60, 180, 70))


def o_walls(lv):
    w = bytearray(OW * OH)
    for x, y, b, h in O_LEVELS[lv % len(O_LEVELS)]:
        for yy in range(y, y + h):
            for xx in range(x, x + b):
                w[yy * OW + xx] = 1
    return w


def play(lcd, keys):
    level = 0
    score = 0
    eaten = 0
    parts = Particles(60)
    pops = Popups()
    while True:
        walls = o_walls(level)
        snake = [(6, 8), (5, 8), (4, 8), (3, 8)]
        d = 1
        turns = []
        grow = 0
        apple = None
        gold = None            # (ruta, tid kvar)
        chili = None
        turbo = 0
        level_apples = 0
        tick = 0
        t = 0

        def free():
            while True:
                c = (random.randint(0, OW - 1), random.randint(0, OH - 1))
                if not walls[c[1] * OW + c[0]] and c not in snake and c != apple:
                    return c

        apple = free()
        banner = 60
        keys.wait_release()
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            for k in (K0, K1, K2, K3):
                if keys.pressed(k) and len(turns) < 3:
                    last = turns[-1] if turns else d
                    if k != last and k != (last + 2) % 4:
                        turns.append(k)
            if banner:
                banner -= 1
            else:
                tick += 1
                delay = max(2, 7 - eaten // 6)
                if turbo:
                    turbo -= 1
                    delay = max(1, delay - 2)
                if tick >= delay:
                    tick = 0
                    if turns:
                        d = turns.pop(0)
                    dx, dy = DIRS4[d]
                    hx, hy = snake[0][0] + dx, snake[0][1] + dy
                    head = (hx, hy)
                    body = snake if grow else snake[:-1]
                    if not (0 <= hx < OW and 0 <= hy < OH) or walls[hy * OW + hx] or head in body:
                        for k in range(30):
                            t1 = time.ticks_ms()
                            o_draw(lcd, walls, snake, apple, gold, chili, score, level, t, k % 4 < 2, turbo)
                            stext(lcd, "KRASCH!", 100, CORAL, 4)
                            lcd.show()
                            wait(t1)
                        return score
                    snake.insert(0, head)
                    if grow:
                        grow -= 1
                    else:
                        snake.pop()
                    px, py = OX + hx * OC + 6, OY + hy * OC + 6
                    if head == apple:
                        eaten += 1
                        level_apples += 1
                        grow += 1
                        pts = 10 * (level + 1) * (2 if turbo else 1)
                        score += pts
                        parts.burst(px, py, CORAL, 10, 2, 12)
                        pops.add(px, py - 8, "+%d" % pts, WHITE)
                        apple = free()
                        if gold is None and random.random() < 0.18:
                            gold = [free(), 150]
                        if chili is None and random.random() < 0.12:
                            chili = [free(), 200]
                        if eaten >= 20:
                            goal("orm", 0)
                        if eaten >= 60:
                            goal("orm", 2)
                    if gold and head == gold[0]:
                        score += 100 * (level + 1)
                        grow += 3
                        parts.burst(px, py, YELLOW, 16, 2.5, 16)
                        pops.add(px, py - 8, "GULD!", YELLOW)
                        gold = None
                    if chili and head == chili[0]:
                        turbo = 150
                        parts.burst(px, py, AMBER, 16, 2.5, 16)
                        pops.add(px, py - 8, "TURBO! x2", AMBER)
                        chili = None
                    if level_apples >= 8:
                        level += 1
                        if level >= 3:
                            goal("orm", 1)
                        for k in range(30):
                            t1 = time.ticks_ms()
                            o_draw(lcd, walls, snake, None, None, None, score, level - 1, t, True, 0)
                            stext(lcd, "NIVA %d!" % (level + 1), 100, LIME, 4)
                            lcd.show()
                            wait(t1)
                        break
                if gold:
                    gold[1] -= 1
                    if gold[1] <= 0:
                        gold = None
                if chili:
                    chili[1] -= 1
                    if chili[1] <= 0:
                        chili = None
            o_draw(lcd, walls, snake, apple, gold, chili, score, level, t, True, turbo)
            parts.draw(lcd)
            pops.draw(lcd)
            if banner:
                stext(lcd, "NIVA %d" % (level + 1), 92, LIME, 3)
                ctext(lcd, O_NAMES[level % len(O_NAMES)], 126, WHITE, 2)
            lcd.show()
            t += 1
            wait(t0)


def o_draw(lcd, walls, snake, apple, gold, chili, score, level, t, show, turbo):
    gradient(lcd, O_BG)
    for x in range(OW + 1):
        lcd.vline(OX + x * OC, OY, OH * OC, O_GRID)
    for y in range(OH + 1):
        lcd.hline(OX, OY + y * OC, OW * OC, O_GRID)
    lcd.rect(OX - 2, OY - 2, OW * OC + 5, OH * OC + 5, O_WALL)
    for x, y, b, h in O_LEVELS[level % len(O_LEVELS)]:
        lcd.fill_rect(OX + x * OC, OY + y * OC, b * OC, h * OC, O_WALL)
        lcd.rect(OX + x * OC, OY + y * OC, b * OC, h * OC, rgb(80, 60, 40))
    if apple:
        ax, ay = OX + apple[0] * OC + 6, OY + apple[1] * OC + 7
        lcd.ellipse(ax, ay, 5, 5, CORAL, True)
        lcd.fill_rect(ax, ay - 8, 2, 4, rgb(120, 70, 30))
        lcd.fill_rect(ax + 2, ay - 7, 3, 2, LIME)
    if gold and (gold[1] > 40 or (t // 3) % 2):
        gx, gy = OX + gold[0][0] * OC + 6, OY + gold[0][1] * OC + 6
        lcd.ellipse(gx, gy, 6, 6, YELLOW, True)
        star(lcd, gx, gy, 4, WHITE)
    if chili and (chili[1] > 40 or (t // 3) % 2):
        cx, cy = OX + chili[0][0] * OC, OY + chili[0][1] * OC
        lcd.fill_rect(cx + 2, cy + 4, 8, 5, rgb(240, 40, 30))
        lcd.fill_rect(cx + 8, cy + 2, 3, 3, LIME)
    if show:
        n = len(snake)
        for i in range(n - 1, -1, -1):
            x, y = snake[i]
            c = (AMBER if (i + t) % 2 else CORAL) if turbo else O_BODY[i % 2]
            lcd.fill_rect(OX + x * OC + 1, OY + y * OC + 1, OC - 1, OC - 1, c)
        hx, hy = OX + snake[0][0] * OC, OY + snake[0][1] * OC
        lcd.fill_rect(hx + 3, hy + 3, 2, 2, BLACK)
        lcd.fill_rect(hx + 8, hy + 3, 2, 2, BLACK)
    big(lcd, str(score), OX, 6, WHITE, 2)
    rtext(lcd, "NIVA %d  %s" % (level + 1, O_NAMES[level % len(O_NAMES)]), W - 30, 10, LIME)
    arrow(lcd, 10, 12, 0, DIM)
    arrow(lcd, W - 10, 12, 1, DIM)
