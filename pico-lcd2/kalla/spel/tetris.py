# TETRIS: tre lägen. 0 vänster, 1 höger, 2 vrid, 3 släpp direkt.
TC = 11                         # rutstorlek
TW, TH = 10, 20
TX, TY = 105, 10
SHAPES = (
    ((-1, 0), (0, 0), (1, 0), (2, 0)),      # I
    ((0, 0), (1, 0), (0, 1), (1, 1)),       # O
    ((-1, 0), (0, 0), (1, 0), (0, -1)),     # T
    ((-1, 0), (0, 0), (0, -1), (1, -1)),    # S
    ((-1, -1), (0, -1), (0, 0), (1, 0)),    # Z
    ((-1, -1), (-1, 0), (0, 0), (1, 0)),    # J
    ((1, -1), (-1, 0), (0, 0), (1, 0)),     # L
)
# Guld (index 7) och skräp (index 8) läggs till efter de vanliga färgerna
if len(T_FILL) == 7:
    for c in ((255, 215, 0), (110, 110, 135)):
        T_FILL.append(rgb(*c))
        T_LIGHT.append(mix(c, (255, 255, 255), 0.6))
        T_DARK.append(mix(c, (0, 0, 0), 0.45))
T_GHOST = [mix(c, C_BG, 0.6) for c in T_RAW]
GOLD, JUNK = 8, 9                     # värden i brädet (färg + 1)
T_BOARD = rgb(16, 16, 38)
T_GRID = rgb(28, 28, 58)
T_BG = [mix((20, 18, 50), (8, 30, 50), y / (H - 1)) for y in range(H)]
T_POINTS = (0, 100, 300, 500, 800)


@native
def t_board(fb, board):
    for y in range(TH):
        row = board[y]
        for x in range(TW):
            v = row[x]
            if v:
                t_cell(fb, TX + x * TC, TY + y * TC, v - 1)


def fmt_time(f):
    """Bilder (30 per sekund) till m:ss.t"""
    s10 = f * 10 // 30
    return "%d:%02d.%d" % (s10 // 600, (s10 // 10) % 60, s10 % 10)


def play(lcd, keys):
    n = total_stars()
    mode = choose(lcd, keys, "TETRIS", ("MARATON", "SPRINT 40", "SKATT"), TEAL,
                  "Las upp lagen med stjarnor",
                  ("", "" if n >= 3 else "3 stj", "" if n >= 8 else "8 stj"))
    if mode is None:
        return None
    return tetris(lcd, keys, mode)


def tetris(lcd, keys, mode):
    board = [bytearray(TW) for _ in range(TH)]
    bag = []
    golds = 0
    if mode == 2:                       # SKATT: skräprader med guld längst ner
        for y in range(TH - 9, TH):
            hole = random.randint(0, TW - 1)
            for x in range(TW):
                if x != hole:
                    board[y][x] = JUNK
            if y >= TH - 7 and y % 2 == 1:
                gx = random.randint(0, TW - 1)
                if gx == hole:
                    gx = (gx + 1) % TW
                board[y][gx] = GOLD
                golds += 1
    found = 0
    clock = 0
    rise = 0

    def nxt():
        if not bag:
            bag.extend(shuffled(7))
        return bag.pop()

    def fits(cells, px, py):
        for cx, cy in cells:
            x = px + cx
            y = py + cy
            if x < 0 or x >= TW or y >= TH:
                return False
            if y >= 0 and board[y][x]:
                return False
        return True

    queue = [nxt(), nxt(), nxt()]
    cur = nxt()
    cells = SHAPES[cur]
    px, py = 4, 1
    score = lines = 0
    level = 1
    fall = 0
    lock = 0
    resets = 0
    combo = -1
    parts = Particles(160)
    pops = Popups()
    shake = Shake()
    banner, btxt, bcol = 0, "", WHITE
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause() and pause(lcd, keys):
            return None if mode else score
        clock += 1
        if mode == 2:                   # skräp stiger upp var 15:e sekund
            rise += 1
            if rise >= 450:
                rise = 0
                if any(board[0]):
                    return ("BEGRAVD!", found, None, "Guld hittat: %d av %d" % (found, golds), False, str)
                del board[0]
                hole = random.randint(0, TW - 1)
                row = bytearray(TW)
                for x in range(TW):
                    if x != hole:
                        row[x] = JUNK
                board.append(row)
                shake.hit(4)
                if not fits(cells, px, py):  # skräpet knuffar upp biten
                    py -= 1
        moved = False
        if keys.repeat(K0, 8, 2) and fits(cells, px - 1, py):
            px -= 1
            moved = True
        if keys.repeat(K1, 8, 2) and fits(cells, px + 1, py):
            px += 1
            moved = True
        if keys.pressed(K2) and cur != 1:
            r = tuple((-cy, cx) for cx, cy in cells)
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)):
                if fits(r, px + dx, py + dy):
                    cells = r
                    px += dx
                    py += dy
                    moved = True
                    break
        if moved and lock and resets < 15:        # man hinner flytta lite på marken
            lock = 1
            resets += 1
        drop = False
        if keys.pressed(K3):                      # släpp direkt
            n = 0
            while fits(cells, px, py + 1):
                py += 1
                n += 1
            score += n * 2
            drop = True
            shake.hit(3)
            for cx, cy in cells:
                parts.burst(TX + (px + cx) * TC + 5, TY + (py + cy) * TC + 10,
                            T_LIGHT[cur], 2, 1.5, 10)
        # Tyngdkraft
        fall += 1
        interval = max(2, int(30 * (0.84 ** (level - 1)))) if mode == 0 else (8 if mode == 1 else 14)
        if fall >= interval:
            fall = 0
            if fits(cells, px, py + 1):
                py += 1
        on_ground = not fits(cells, px, py + 1)
        lock = lock + 1 if on_ground else 0
        if on_ground and (lock > 16 or drop):
            for cx, cy in cells:
                if py + cy >= 0:
                    board[py + cy][px + cx] = cur + 1
            full = []
            for y in range(TH):
                if all(board[y]):
                    full.append(y)
            if full:
                combo += 1
                for y in full:
                    for x in range(TW):
                        if board[y][x] == GOLD:
                            found += 1
                            pops.add(TX + x * TC + 5, TY + y * TC - 6, "GULD!", YELLOW)
                for k in range(8):                # blinka raderna
                    gradient(lcd, T_BG)
                    lcd.fill_rect(TX - 1, TY - 1, TW * TC + 1, TH * TC + 1, T_BOARD)
                    t_board(lcd, board)
                    for y in full:
                        if k % 2 == 0:
                            lcd.fill_rect(TX, TY + y * TC, TW * TC - 1, TC - 1, WHITE)
                    lcd.show()
                    time.sleep_ms(30)
                for y in full:
                    for x in range(TW):
                        parts.burst(TX + x * TC + 5, TY + y * TC + 5, T_FILL[board[y][x] - 1], 3, 3, 16)
                    del board[y]
                    board.insert(0, bytearray(TW))
                gain = T_POINTS[len(full)] * level + max(0, combo) * 50 * level
                score += gain
                lines += len(full)
                if lines >= 20:
                    goal("tetris", 0)
                if len(full) == 4:
                    goal("tetris", 1)
                new_level = lines // 10 + 1 if mode == 0 else level
                pops.add(TX + TW * TC // 2, TY + full[0] * TC, "+%d" % gain, AMBER)
                if len(full) == 4:
                    banner, btxt, bcol = 50, "TETRIS!", PINK
                    shake.hit(8)
                elif combo >= 2:
                    banner, btxt, bcol = 35, "KOMBO x%d" % combo, TEAL
                if new_level > level:
                    level = new_level
                    banner, btxt, bcol = 50, "NIVA %d" % level, LIME
                    if level >= 6:
                        goal("tetris", 2)
                if mode == 1 and lines >= 40:
                    return ("SNABBT!", clock, "tetris_sprint", "40 rader", True, fmt_time)
                if mode == 2 and found >= golds:
                    return ("SKATTEN HITTAD!", clock, "tetris_skatt", "Allt guld pa", True, fmt_time)
            else:
                combo = -1
            cur = queue.pop(0)
            queue.append(nxt())
            cells = SHAPES[cur]
            px, py = 4, 1
            lock = resets = 0
            fall = 0
            if not fits(cells, px, py):
                for k in range(20):
                    lcd.fill_rect(TX, TY + (19 - k) * TC, TW * TC - 1, TC - 1, DIM)
                    lcd.show()
                    time.sleep_ms(30)
                if mode == 1:
                    return ("GAME OVER", lines, None, "Rader av 40", False, str)
                if mode == 2:
                    return ("GAME OVER", found, None, "Guld hittat av %d" % golds, False, str)
                return score

        # --- Rita ---
        ox, oy = shake.offset()
        gradient(lcd, T_BG)
        lcd.fill_rect(TX - 4 + ox, TY - 4 + oy, TW * TC + 7, TH * TC + 7, LINE)
        lcd.fill_rect(TX - 1 + ox, TY - 1 + oy, TW * TC + 1, TH * TC + 1, T_BOARD)
        for x in range(1, TW):
            lcd.vline(TX + x * TC - 1 + ox, TY + oy, TH * TC - 1, T_GRID)
        for y in range(1, TH):
            lcd.hline(TX + ox, TY + y * TC - 1 + oy, TW * TC - 1, T_GRID)
        if ox or oy:
            for y in range(TH):
                for x in range(TW):
                    v = board[y][x]
                    if v:
                        t_cell(lcd, TX + x * TC + ox, TY + y * TC + oy, v - 1)
        else:
            t_board(lcd, board)
        gy = py
        while fits(cells, px, gy + 1):
            gy += 1
        for cx, cy in cells:
            if gy + cy >= 0:
                lcd.rect(TX + (px + cx) * TC, TY + (gy + cy) * TC, 10, 10, T_GHOST[cur])
        for cx, cy in cells:
            if py + cy >= 0:
                t_cell(lcd, TX + (px + cx) * TC + ox, TY + (py + cy) * TC + oy, cur)
        # Nästa bitar
        lcd.fill_rect(228, 10, 84, 136, PANEL)
        lcd.text("NASTA", 250, 16, GRAY)
        for i, q in enumerate(queue):
            s = 10 if i == 0 else 7
            bx, by = 262, 46 + i * 34 + (0 if i == 0 else 6)
            for cx, cy in SHAPES[q]:
                t_cell(lcd, bx + cx * (s + 1), by + cy * (s + 1), q, s)
        # Poäng
        lcd.fill_rect(8, 10, 88, 160, PANEL)
        if mode == 0:
            lcd.text("POANG", 16, 18, GRAY)
            big(lcd, str(score), 16, 30, WHITE, 2 if score < 100000 else 1)
            lcd.text("RADER", 16, 62, GRAY)
            big(lcd, str(lines), 16, 74, WHITE, 2)
            lcd.text("NIVA", 16, 106, GRAY)
            big(lcd, str(level), 16, 118, LIME, 3)
            lcd.text("REKORD", 16, 150, DIM)
            lcd.text(str(SCORES.get("tetris", 0)), 16, 160, DIM)
        else:
            lcd.text("TID", 16, 18, GRAY)
            big(lcd, fmt_time(clock), 14, 30, WHITE, 1)
            if mode == 1:
                lcd.text("RADER KVAR", 16, 62, GRAY)
                big(lcd, str(max(0, 40 - lines)), 16, 74, AMBER, 3)
                rk = SCORES.get("tetris_sprint")
            else:
                lcd.text("GULD", 16, 62, GRAY)
                big(lcd, "%d/%d" % (found, golds), 16, 74, YELLOW, 2)
                lcd.text("SKRAP OM", 16, 106, GRAY)
                big(lcd, "%d" % ((450 - rise) // 30), 16, 118, CORAL, 2)
                rk = SCORES.get("tetris_skatt")
            if rk:
                lcd.text("REKORD", 16, 150, DIM)
                lcd.text(fmt_time(rk), 16, 160, DIM)
        lcd.text("0 <  > 1", 18, 196, DIM)
        lcd.text("3 slapp", 18, 208, DIM)
        lcd.text("2 vrid", 18, 220, DIM)
        parts.draw(lcd, ox, oy)
        pops.draw(lcd, ox, oy)
        if banner > 0:
            banner -= 1
            stext(lcd, btxt, 100, bcol, 3, TX + TW * TC // 2)
        lcd.show()
        t += 1
        wait(t0)


