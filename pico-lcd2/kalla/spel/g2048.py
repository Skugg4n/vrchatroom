# 2048: pilarna i hörnen, 0 upp, 1 höger, 2 ner, 3 vänster.
G_N = 4
G_S = 46
G_GAP = 6
G_X = (W - (G_N * G_S + (G_N + 1) * G_GAP)) // 2
G_Y = 16
G_BOARD = rgb(60, 52, 80)
G_EMPTY = rgb(80, 72, 104)
G_BGC = [mix((30, 22, 46), (16, 26, 46), y / (H - 1)) for y in range(H)]


def play(lcd, keys):
    grid = [[0] * G_N for _ in range(G_N)]
    score = 0
    won = False
    pops = Popups()
    parts = Particles(80)

    def spawn():
        empty = [(r, c) for r in range(G_N) for c in range(G_N) if grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            grid[r][c] = 1 if random.random() < 0.9 else 2
            return (r, c)
        return None

    def cell_xy(r, c):
        return G_X + G_GAP + c * (G_S + G_GAP), G_Y + G_GAP + r * (G_S + G_GAP)

    def can_move():
        for r in range(G_N):
            for c in range(G_N):
                if grid[r][c] == 0:
                    return True
                if c + 1 < G_N and grid[r][c] == grid[r][c + 1]:
                    return True
                if r + 1 < G_N and grid[r][c] == grid[r + 1][c]:
                    return True
        return False

    def move(d):
        """d: 0 upp, 1 höger, 2 ner, 3 vänster. Returnerar (rörelser, sammanslagna, poäng)."""
        nonlocal grid
        dr, dc = ((-1, 0), (0, 1), (1, 0), (0, -1))[d]
        moves = []
        merged = []
        gain = 0
        new = [[0] * G_N for _ in range(G_N)]
        for i in range(G_N):
            # gå längs raden/kolumnen från den sida brickorna glider mot
            if dr:
                line = [(r, i) for r in (range(G_N) if dr < 0 else range(G_N - 1, -1, -1))]
            else:
                line = [(i, c) for c in (range(G_N) if dc < 0 else range(G_N - 1, -1, -1))]
            target = 0
            last = None                       # (värde, index i linjen, kan slås ihop)
            for (r, c) in line:
                v = grid[r][c]
                if not v:
                    continue
                if last and last[0] == v and last[2]:
                    tr, tc = line[last[1]]
                    new[tr][tc] = v + 1
                    gain += 1 << (v + 1)
                    merged.append((tr, tc))
                    moves.append((r, c, tr, tc, v))
                    last = (v + 1, last[1], False)
                else:
                    tr, tc = line[target]
                    new[tr][tc] = v
                    moves.append((r, c, tr, tc, v))
                    last = (v, target, True)
                    target += 1
        changed = any(m[0] != m[2] or m[1] != m[3] for m in moves)
        if changed:
            grid = new
        return (moves if changed else None), merged, gain

    spawn()
    spawn()
    pop = []
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return score
        d = -1
        for k, dd in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
            if keys.pressed(k):
                d = dd
        if d >= 0:
            moves, merged, gain = move(d)
            if moves:
                # Glid-animation
                for f in range(1, 6):
                    p = f / 5
                    draw_2048(lcd, None, score, t)
                    for (r, c, tr, tc, v) in moves:
                        x0, y0 = cell_xy(r, c)
                        x1, y1 = cell_xy(tr, tc)
                        g_tile(lcd, int(x0 + (x1 - x0) * p), int(y0 + (y1 - y0) * p), v)
                    lcd.show()
                    time.sleep_ms(14)
                score += gain
                if gain:
                    pops.add(W // 2, 6, "+%d" % gain, AMBER)
                pop = [(r, c, 6) for r, c in merged]
                for r, c in merged:
                    x, y = cell_xy(r, c)
                    parts.burst(x + G_S // 2, y + G_S // 2, G_COL[min(grid[r][c] - 1, 13)], 8, 2.5, 12)
                    e = grid[r][c]
                    if e >= 8:
                        goal("2048", 0)
                    if e >= 10:
                        goal("2048", 1)
                    if e >= 11:
                        goal("2048", 2)
                    if grid[r][c] == 11 and not won:
                        won = True
                        pops.add(W // 2, 100, "2048! DU VANN!", YELLOW, 2)
                s = spawn()
                if s:
                    pop.append((s[0], s[1], -6))
                if not can_move():
                    draw_2048(lcd, None, score, t)
                    lcd.show()
                    time.sleep_ms(900)
                    return score
        draw_2048(lcd, grid, score, t, pop)
        pop = [(r, c, k - 1 if k > 0 else k + 1) for r, c, k in pop if k != 0]
        parts.draw(lcd)
        pops.draw(lcd)
        lcd.show()
        t += 1
        wait(t0)


def draw_2048(lcd, grid, score, t, pop=()):
    gradient(lcd, G_BGC)
    size = G_N * G_S + (G_N + 1) * G_GAP
    lcd.fill_rect(G_X, G_Y, size, size, G_BOARD)
    for r in range(G_N):
        for c in range(G_N):
            x = G_X + G_GAP + c * (G_S + G_GAP)
            y = G_Y + G_GAP + r * (G_S + G_GAP)
            lcd.fill_rect(x + 2, y, G_S - 4, G_S, G_EMPTY)
            lcd.fill_rect(x, y + 2, G_S, G_S - 4, G_EMPTY)
            if grid and grid[r][c]:
                g_tile(lcd, x, y, grid[r][c])
    for r, c, k in pop:
        if grid and grid[r][c]:
            x = G_X + G_GAP + c * (G_S + G_GAP)
            y = G_Y + G_GAP + r * (G_S + G_GAP)
            if k > 0:                                     # sammanslagen: blir större
                g = k // 2
                g_tile(lcd, x - g, y - g, grid[r][c], G_S + 2 * g)
            else:                                         # ny: växer fram
                s = G_S + k * 6
                if s > 8:
                    g_tile(lcd, x + (G_S - s) // 2, y + (G_S - s) // 2, grid[r][c], s)
    # Poäng till höger, pilar i hörnen
    lcd.text("POANG", 8, 40, GRAY)
    big(lcd, str(score), 8, 52, WHITE, 2 if score < 100 else 1)
    lcd.text("REKORD", 8, 84, DIM)
    lcd.text(str(SCORES.get("2048", 0)), 8, 96, DIM)
    arrow(lcd, 12, 12, 0, AMBER)
    arrow(lcd, W - 12, 12, 1, AMBER)
    arrow(lcd, W - 12, H - 12, 2, AMBER)
    arrow(lcd, 12, H - 12, 3, AMBER)


