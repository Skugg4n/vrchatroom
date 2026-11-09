# LADOR (Sokoban): knuffa alla lådor till de gröna prickarna.
#   pilarna i hörnen: 0 upp, 1 höger, 2 ner, 3 vänster
#   håll alla fyra: 0 ångra, 1 börja om, 2 fortsätt, 3 till banorna
# Banorna är skapade av verktyg/gen_ladr.py och kontrollerade med en lösare.

LEVELS = (
    (4, ('#######', '#  #  #', '#  $. #', '#$    #', '#+#  ##', '######-')),  # minst 4 knuffar
    (6, ('#######', '#@    #', '#  #$ #', '#.$   #', '#.  ###', '#####--')),  # minst 6 knuffar
    (4, ('######-', '# .#@##', '#   $ #', '# $  .#', '#    ##', '######-')),  # minst 4 knuffar
    (4, ('#######', '# #. @#', '#  $$##', '#    ##', '#    .#', '#######')),  # minst 4 knuffar
    (4, ('#######', '#   $.#', '#   $@#', '#  #. #', '#   ###', '#####--')),  # minst 4 knuffar
    (8, ('########', '#      #', '#   $@##', '# $    #', '# #.$  #', '## . . #', '-#######')),  # minst 8 knuffar
    (8, ('#######-', '# $ . ##', '# $.##@#', '#   #  #', '#   .$ #', '### #  #', '--######')),  # minst 8 knuffar
    (9, ('########', '#    #.#', '#    $ #', '# .   .#', '#   #$$#', '# ## @ #', '########')),  # minst 9 knuffar
    (8, ('########', '#@##   #', '# $  . #', '# $ .# #', '# $  # #', '#   .  #', '########')),  # minst 8 knuffar
    (10, ('########', '#+ #   #', '#$# $ .#', '#   # ##', '#  #   #', '#  $  .#', '########')),  # minst 10 knuffar
    (9, ('-#######', '##@# . #', '# $#   #', '#   #$ #', '#    . #', '# . $  #', '########')),  # minst 9 knuffar
    (8, ('########', '#@  # .#', '#$#$# $#', '#      #', '#    # #', '#..#   #', '########')),  # minst 8 knuffar
    (15, ('-########', '##@#  # #', '#.$  .# #', '#      .#', '###     #', '#  $$   #', '#       #', '#########')),  # minst 15 knuffar
    (14, ('-########', '##  # #.#', '#     @ #', '# $##   #', '#    #$ #', '###.    #', '#.  $  ##', '########-')),  # minst 14 knuffar
    (14, ('########-', '#.     ##', '#     . #', '#      ##', '# #$$  .#', '##@$  # #', '#  #    #', '#########')),  # minst 14 knuffar
    (15, ('########-', '#   #  ##', '# $ # $ #', '#    @# #', '# $   . #', '#    .###', '# ## .  #', '#########')),  # minst 15 knuffar
    (14, ('#########', '#.@ #   #', '#    $  #', '# $  ####', '#    #  #', '# $  #  #', '# .  .  #', '#########')),  # minst 14 knuffar
    (18, ('#######--', '#  #  ###', '# $@$  .#', '# $ #   #', '#     ..#', '#  .  $ #', '#    # ##', '########-')),  # minst 18 knuffar
    (16, ('-########', '##    . #', '#   .$ ##', '#     $ #', '# .# ##@#', '#  #  $ #', '#  $   .#', '#########')),  # minst 16 knuffar
    (16, ('-#######-', '## ## @##', '#  # $$ #', '#     $.#', '#     $ #', '#    .  #', '#.    #.#', '#########')),  # minst 16 knuffar
)

L_FLOOR = (rgb(58, 46, 38), rgb(52, 42, 34))
L_WALL = rgb(120, 90, 160)
L_WALL_L = rgb(160, 130, 200)
L_WALL_D = rgb(70, 50, 100)
L_GOAL = rgb(90, 230, 120)
L_BG = [mix((24, 16, 30), (40, 24, 20), y / (H - 1)) for y in range(H)]


def l_parse(rows):
    walls, goals, boxes = set(), set(), []
    p = (0, 0)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                walls.add((x, y))
            if ch in ".*+":
                goals.add((x, y))
            if ch in "$*":
                boxes.append((x, y))
            if ch in "@+":
                p = (x, y)
    return walls, goals, boxes, p


def l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, hud):
    gradient(lcd, L_BG)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "-":
                continue
            px, py = ox + x * ts, oy + y * ts
            if (x, y) in walls:
                lcd.fill_rect(px, py, ts, ts, L_WALL)
                lcd.hline(px, py, ts, L_WALL_L)
                lcd.vline(px, py, ts, L_WALL_L)
                lcd.hline(px, py + ts - 1, ts, L_WALL_D)
                lcd.vline(px + ts - 1, py, ts, L_WALL_D)
            else:
                lcd.fill_rect(px, py, ts, ts, L_FLOOR[(x + y) % 2])
                if (x, y) in goals:
                    r2 = ts // 4 + (1 if (t // 8) % 2 else 0)
                    lcd.ellipse(px + ts // 2, py + ts // 2, r2, r2, L_GOAL)
                    lcd.ellipse(px + ts // 2, py + ts // 2, 2, 2, L_GOAL, True)
    for b in boxes:
        crate(lcd, ox + b[0] * ts + 1, oy + b[1] * ts + 1, ts - 2, b in goals)
    hero(lcd, ox + p[0] * ts + ts // 2, oy + p[1] * ts + ts // 2 - 1, 1 if face != 3 else -1, t)
    lcd.fill_rect(0, 0, W, 14, BG)
    lcd.text(hud, 4, 3, WHITE)
    for d, (x, y) in enumerate(((10, 24), (W - 10, 24), (W - 10, H - 10), (10, H - 10))):
        arrow(lcd, x, y, d, DIM, 4)


def l_time(f):
    s = f // 30
    return "%d:%02d" % (s // 60, s % 60)


def play(lcd, keys):
    best = SCORES.get("ladr_best", [0] * len(LEVELS))
    if len(best) != len(LEVELS):
        best = (best + [0] * len(LEVELS))[:len(LEVELS)]
    sel = 0
    for i in range(len(LEVELS)):
        if best[i]:
            sel = min(i + 1, len(LEVELS) - 1)
    while True:
        sel = l_select(lcd, keys, best, sel)
        if sel is None:
            return None
        res = l_level(lcd, keys, sel)
        if res:
            moves, frames = res
            if not best[sel] or moves < best[sel]:
                best[sel] = moves
            SCORES["ladr_best"] = best
            bt = SCORES.get("ladr_time", [0] * len(LEVELS))
            bt = (bt + [0] * len(LEVELS))[:len(LEVELS)]
            if not bt[sel] or frames < bt[sel]:
                bt[sel] = frames
            SCORES["ladr_time"] = bt
            save_scores()
            done = sum(1 for b in best if b)
            if done >= 5:
                goal("ladr", 0)
            if done >= 12:
                goal("ladr", 1)
            if done >= len(LEVELS):
                goal("ladr", 2)
            if sel < len(LEVELS) - 1:
                sel += 1


def l_select(lcd, keys, best, sel):
    stars = Stars(30)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        unlocked = 0
        while unlocked < len(LEVELS) and best[unlocked]:
            unlocked += 1
        if keys.repeat(K0, 10, 4):
            sel = (sel - 1) % len(LEVELS)
        if keys.repeat(K1, 10, 4):
            sel = (sel + 1) % len(LEVELS)
        if keys.pressed(K2) and sel <= unlocked:
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            return None
        gradient(lcd, L_BG)
        stars.draw(lcd)
        big(lcd, "LADOR", 12, 10, SHADOW, 3)
        big(lcd, "LADOR", 10, 8, AMBER, 3)
        done = sum(1 for b in best if b)
        rtext(lcd, "%d/%d klara" % (done, len(LEVELS)), W - 8, 12, GRAY)
        rtext(lcd, "0/1 valj 2 spela 3 ut", W - 8, 24, DIM)
        for i in range(len(LEVELS)):
            x = 14 + (i % 5) * 60
            y = 42 + (i // 5) * 40
            if i == sel:
                lcd.fill_rect(x - 3, y - 3, 58, 36, WHITE)
            if best[i]:
                c = rgb(90, 200, 110)
            elif i <= unlocked:
                c = AMBER
            else:
                c = LINE
            lcd.fill_rect(x, y, 52, 30, c)
            ctext(lcd, str(i + 1), y + 7, BG, 2, x + 26)
        p = LEVELS[sel][0]
        lcd.fill_rect(10, 206, 300, 30, PANEL)
        if sel > unlocked:
            ctext(lcd, "Klara banan innan forst", 216, AMBER)
        elif best[sel]:
            bt = SCORES.get("ladr_time", [0] * len(LEVELS))
            tt = bt[sel] if sel < len(bt) else 0
            ctext(lcd, "Basta: %d drag  %s  minst %d" % (best[sel], l_time(tt), p), 216, WHITE)
        else:
            ctext(lcd, "Ny bana! Minst %d knuffar." % p, 216, WHITE)
        lcd.show()
        t += 1
        wait(t0)


def l_level(lcd, keys, n):
    rows = LEVELS[n][1]
    walls, goals, boxes0, p0 = l_parse(rows)
    w, h = max(len(r) for r in rows), len(rows)
    ts = min(24, (W - 40) // w, (H - 24) // h)
    ox = (W - w * ts) // 2
    oy = 16 + (H - 16 - h * ts) // 2
    boxes, p = list(boxes0), p0
    hist = []
    moves = 0
    face = 1
    frames = 0
    parts = Particles(60)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            r = l_menu(lcd, keys, rows, walls, goals, boxes, p, face, ts, ox, oy, hist)
            if r == "exit":
                return None
            if r == "restart":
                boxes, p, hist, moves, frames = list(boxes0), p0, [], 0, 0
            elif r:
                boxes, p, moves = r
        frames += 1
        for k in (K0, K1, K2, K3):
            if keys.repeat(k, 8, 3):
                dx, dy = DIRS4[k]
                face = k
                nxt = (p[0] + dx, p[1] + dy)
                if nxt in walls:
                    continue
                if nxt in boxes:
                    to = (nxt[0] + dx, nxt[1] + dy)
                    if to in walls or to in boxes:
                        continue
                    hist.append((p, list(boxes), moves))
                    boxes[boxes.index(nxt)] = to
                    if to in goals:
                        parts.burst(ox + to[0] * ts + ts // 2, oy + to[1] * ts + ts // 2, L_GOAL, 10, 2, 12)
                else:
                    hist.append((p, list(boxes), moves))
                p = nxt
                moves += 1
                break
        on = sum(1 for b in boxes if b in goals)
        hud = "BANA %d   DRAG %d   %s   %d/%d" % (n + 1, moves, l_time(frames), on, len(boxes))
        l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, hud)
        parts.draw(lcd)
        if on == len(boxes):
            for k in range(40):
                t1 = time.ticks_ms()
                l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t + k, hud)
                for _ in range(10):
                    lcd.fill_rect(random.randint(0, W - 3), random.randint(16, H - 3), 3, 3,
                                  random.choice(CONFETTI))
                stext(lcd, "KLART!", 90, LIME, 4)
                ctext(lcd, "%d drag  %s" % (moves, l_time(frames)), 140, WHITE, 2)
                lcd.show()
                wait(t1)
            return moves, frames
        lcd.show()
        t += 1
        wait(t0)


def l_menu(lcd, keys, rows, walls, goals, boxes, p, face, ts, ox, oy, hist):
    """Paus-rutan: 0 ångra (flera gånger), 1 börja om, 2 fortsätt, 3 till banorna."""
    keys.wait_release()
    moves = None
    t = 0
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.repeat(K0, 10, 4) and hist:
            p, boxes, moves = hist.pop()
        if keys.pressed(K1):
            keys.wait_release()
            return "restart"
        if keys.pressed(K2):
            keys.wait_release()
            return (boxes, p, moves) if moves is not None else None
        if keys.pressed(K3):
            keys.wait_release()
            return "exit"
        l_draw(lcd, rows, walls, goals, boxes, p, face, ts, ox, oy, t, "PAUS")
        lcd.fill_rect(0, 0, W, 14, AMBER)
        lcd.text("0 angra  1 om  2 spela  3 banor", 6, 3, BG)
        lcd.show()
        t += 1
        wait(t0)
