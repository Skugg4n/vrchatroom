# SPOKJAKT: pilarna i hörnen, 0 upp, 1 höger, 2 ner, 3 vänster.
P_HALVES = (
    (
        "###########", "#o........#", "#.###.###.#", "#..........", "#.###.#.###",
        "#.....#...#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
        "#####.#.###", "    #.#....", "#####.#.###", "#.........#", "#.###.###.#",
        "#o..#......", "###.#.#.###", "#.....#...#", "#.#######.#", "#..........",
        "###########",
    ),
    (
        "###########", "#o..##.....", "#.#.##.###.", "#.#........", "#.#.#####.#",
        "#.........#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
        "#####.#.###", "    #.#....", "#####.#.###", "#..........", "#.##.###.#.",
        "#o.#.......", "##.#.#.###.", "#....#.....", "#.######.#.", "#..........",
        "###########",
    ),
    (
        "###########", "#.........#", "#.##.####.#", "#o##.......", "#.##.#.##.#",
        "#.........#", "#####.###.#", "    #.#....", "#####.#.##-", "......#.#GG",
        "#####.#.###", "    #.#....", "#####.#.###", "#.....#...#", "#o###.#.#.#",
        "#...#......", "###.#.###.#", "#.........#", "#.###.#####", "#..........",
        "###########",
    ),
)
P_MAZE = None


def p_set_maze(n):
    """Byter labyrint (spegla vänster halva)."""
    global P_MAZE
    h = P_HALVES[n % len(P_HALVES)]
    P_MAZE = tuple(r + "".join(r[9 - i] for i in range(10)) for r in h)


p_set_maze(0)
MW, MH = 21, 21
PT = 10
PX0, PY0 = (W - MW * PT) // 2, 26
P_WALL_D = rgb(14, 18, 70)
P_WALLS = (P_WALL, rgb(220, 50, 140), rgb(40, 180, 100))
FRIGHT_C = rgb(50, 70, 255)
SCATTER = ((19, -2), (1, -2), (19, 22), (1, 22))
HOUSE = (10, 9)
EXIT = (10, 7)


def p_walk(x, y):
    """0 vägg, 1 gång, 2 spökhus, 3 dörr."""
    if y < 0 or y >= MH:
        return 0
    ch = P_MAZE[y][x % MW]
    if ch == "." or ch == "o":
        return 1
    if ch == "G":
        return 2
    if ch == "-":
        return 3
    return 0


def p_wall_rects():
    """Förberäknar väggarnas rektanglar (fyllning + kantlinjer)."""
    fills = []
    edges = []
    for y in range(MH):
        x = 0
        while x < MW:
            if P_MAZE[y][x] == "#":
                s = x
                while x < MW and P_MAZE[y][x] == "#":
                    x += 1
                fills.append((PX0 + s * PT, PY0 + y * PT, (x - s) * PT, PT))
            else:
                x += 1
    for y in range(MH):
        for x in range(MW):
            if P_MAZE[y][x] != "#":
                continue
            px, py = PX0 + x * PT, PY0 + y * PT
            for d, (dx, dy) in enumerate(DIRS4):
                nx, ny = x + dx, y + dy
                if 0 <= nx < MW and 0 <= ny < MH and P_MAZE[ny][nx] not in "# ":
                    if d == 0:
                        edges.append((px, py, PT, 2))
                    elif d == 1:
                        edges.append((px + PT - 2, py, 2, PT))
                    elif d == 2:
                        edges.append((px, py + PT - 2, PT, 2))
                    else:
                        edges.append((px, py, 2, PT))
    return tuple(fills), tuple(edges)


@native
def p_draw_maze(fb, fills, edges, dots, blink, wall_c):
    for r in fills:
        fb.fill_rect(r[0], r[1], r[2], r[3], P_WALL_D)
    for r in edges:
        fb.fill_rect(r[0], r[1], r[2], r[3], wall_c)
    for y in range(MH):
        for x in range(MW):
            v = dots[y * MW + x]
            if v == 1:
                fb.fill_rect(PX0 + x * PT + 4, PY0 + y * PT + 4, 2, 2, P_DOT)
            elif v == 2 and blink:
                fb.ellipse(PX0 + x * PT + 5, PY0 + y * PT + 5, 3, 3, P_DOT, True)
    fb.fill_rect(PX0 + 10 * PT, PY0 + 8 * PT + 4, PT, 2, rgb(255, 150, 210))


def turn_back(e):
    """Vänd mitt i en ruta utan att hoppa."""
    if e.d < 0:
        return
    dx, dy = DIRS4[e.d]
    if e.p > 0:
        e.x = (e.x + dx) % MW
        e.y += dy
        e.p = 1 - e.p
    e.d = (e.d + 2) % 4


class Ent:
    def __init__(self, x, y, d, speed):
        self.x, self.y, self.d, self.p, self.speed = x, y, d, 0.0, speed

    def pos(self):
        if self.d < 0:
            return self.x, self.y
        dx, dy = DIRS4[self.d]
        return self.x + dx * self.p, self.y + dy * self.p


def g_decide(g, ghosts, pac, face, chase):
    """Spöket står mitt i en ruta och väljer nästa riktning."""
    if g.state == "leave":
        tx, ty = EXIT
    elif g.state == "eyes":
        tx, ty = HOUSE
    elif not chase:
        tx, ty = SCATTER[g.i]
    else:
        pdx, pdy = DIRS4[face]
        if g.i == 0:                                  # röd: jagar Pac direkt
            tx, ty = pac.x, pac.y
        elif g.i == 1:                                # rosa: siktar framför Pac
            tx, ty = pac.x + 4 * pdx, pac.y + 4 * pdy
        elif g.i == 2:                                # blå: knipa tillsammans med röd
            b = ghosts[0]
            tx, ty = 2 * (pac.x + 2 * pdx) - b.x, 2 * (pac.y + 2 * pdy) - b.y
        else:                                         # orange: blyg när den är nära
            if (g.x - pac.x) ** 2 + (g.y - pac.y) ** 2 > 36:
                tx, ty = pac.x, pac.y
            else:
                tx, ty = SCATTER[3]
    inside = g.state in ("leave", "eyes")
    opts = []
    for d in (0, 3, 2, 1):
        if d == (g.d + 2) % 4:
            continue
        ddx, ddy = DIRS4[d]
        w = p_walk(g.x + ddx, g.y + ddy)
        if w == 1 or (inside and w in (2, 3)):
            opts.append(d)
    if not opts:
        opts = [(g.d + 2) % 4]
    if g.fright and g.state == "normal":
        g.d = random.choice(opts)
        return
    best = None
    for d in opts:
        ddx, ddy = DIRS4[d]
        dist = (g.x + ddx - tx) ** 2 + (g.y + ddy - ty) ** 2
        if best is None or dist < best:
            best = dist
            g.d = d


def p_cherry(fb, x, y):
    fb.line(x, y - 6, x - 3, y, LIME)
    fb.line(x, y - 6, x + 3, y + 1, LIME)
    fb.ellipse(x - 3, y + 1, 3, 3, CORAL, True)
    fb.ellipse(x + 3, y + 2, 3, 3, CORAL, True)
    fb.pixel(x - 4, y, WHITE)


def play(lcd, keys):
    p_set_maze(0)
    fills, edges = p_wall_rects()
    wall = P_WALLS[0]
    score = 0
    lives = 3
    level = 1
    pops = Popups()
    parts = Particles(60)

    def new_dots():
        d = bytearray(MW * MH)
        for y in range(MH):
            for x in range(MW):
                ch = P_MAZE[y][x]
                if ch == ".":
                    d[y * MW + x] = 1
                elif ch == "o":
                    d[y * MW + x] = 2
        d[15 * MW + 10] = 0                                  # där Pac börjar
        return d

    dots = new_dots()
    left = sum(1 for v in dots if v)
    total = left
    fruit_t = 0
    fruits = 0

    while True:                                              # ett liv
        pac = Ent(10, 15, -1, min(0.13 + level * 0.006, 0.17))
        face = 3
        want = -1
        ghosts = []
        for i, (x, y) in enumerate(((10, 7), (10, 9), (9, 9), (11, 9))):
            g = Ent(x, y, 3 if i == 0 else 0, 0.12)
            g.i = i
            g.state = "normal" if i == 0 else "house"
            g.release = (0, 60, 160, 260)[i]
            g.fright = 0
            ghosts.append(g)
        mode_t = 0
        fright_t = 0
        eat_n = 0
        ready = 60
        t = 0
        dead = 0
        keys.wait_release()
        while True:
            t0 = time.ticks_ms()
            keys.update()
            if keys.pause() and pause(lcd, keys):
                return score
            for k, d in ((K0, 0), (K1, 1), (K2, 2), (K3, 3)):
                if keys.pressed(k):
                    want = d
            if ready > 0:
                ready -= 1
            elif dead == 0:
                # --- Pac ---
                if pac.d >= 0 and want == (pac.d + 2) % 4:          # vänd direkt
                    dx, dy = DIRS4[pac.d]
                    pac.x = (pac.x + dx) % MW
                    pac.y += dy
                    pac.p = 1 - pac.p
                    pac.d = want
                if pac.d < 0 and want >= 0:
                    dx, dy = DIRS4[want]
                    if p_walk(pac.x + dx, pac.y + dy) == 1:
                        pac.d = want
                if pac.d >= 0:
                    face = pac.d
                    pac.p += pac.speed
                    while pac.p >= 1:
                        pac.p -= 1
                        dx, dy = DIRS4[pac.d]
                        pac.x = (pac.x + dx) % MW
                        pac.y += dy
                        k = pac.y * MW + pac.x
                        if dots[k]:
                            if dots[k] == 2:
                                score += 50
                                fright_t = max(60, 200 - level * 20)
                                eat_n = 0
                                for g in ghosts:
                                    if g.state == "normal":
                                        g.fright = 1
                                        turn_back(g)
                            else:
                                score += 10
                            dots[k] = 0
                            left -= 1
                            if (total - left in (70, 160)) and fruits < 2:
                                fruits += 1
                                fruit_t = 300
                        if fruit_t and (pac.x, pac.y) == (10, 11):
                            pts = min(100 * level, 1000)
                            score += pts
                            fruit_t = 0
                            pops.add(PX0 + 105, PY0 + 108, str(pts), CORAL)
                            parts.burst(PX0 + 105, PY0 + 115, CORAL, 14, 2.5, 16)
                        if want >= 0:
                            dx, dy = DIRS4[want]
                            if p_walk(pac.x + dx, pac.y + dy) == 1:
                                pac.d = want
                        dx, dy = DIRS4[pac.d]
                        if p_walk(pac.x + dx, pac.y + dy) != 1:
                            pac.d = -1
                            pac.p = 0.0
                            break
                # --- Läge: spridning eller jakt ---
                mode_t += 1
                cycle = mode_t % 900
                chase = cycle >= 210
                if mode_t % 900 in (0, 210) and mode_t > 1:
                    for g in ghosts:
                        if g.state == "normal" and not g.fright:
                            turn_back(g)
                if fright_t > 0:
                    fright_t -= 1
                    if fright_t == 0:
                        for g in ghosts:
                            g.fright = 0
                # --- Spöken ---
                for g in ghosts:
                    if g.state == "house":
                        if t >= g.release:
                            g.state = "leave"
                            g.p = 0.0
                            g.d = 0
                            g_decide(g, ghosts, pac, face, chase)
                        continue
                    if g.state == "eyes":
                        sp = 0.3
                    elif g.fright:
                        sp = 0.08
                    else:
                        sp = min(0.12 + level * 0.007, 0.16)
                    if g.y == 9 and (g.x < 4 or g.x > 16):
                        sp *= 0.6                                    # långsamt i tunneln
                    if g.d < 0:
                        g.d = 0
                    g.p += sp
                    while g.p >= 1:
                        g.p -= 1
                        dx, dy = DIRS4[g.d]
                        g.x = (g.x + dx) % MW
                        g.y += dy
                        if g.state == "leave" and (g.x, g.y) == EXIT:
                            g.state = "normal"
                        if g.state == "eyes" and (g.x, g.y) == HOUSE:
                            g.state = "leave"
                            g.fright = 0
                        g_decide(g, ghosts, pac, face, chase)
                # --- Krockar ---
                ppx, ppy = pac.pos()
                for g in ghosts:
                    if g.state in ("house", "eyes", "leave"):
                        continue
                    gx, gy = g.pos()
                    if (gx - ppx) ** 2 + (gy - ppy) ** 2 < 0.5:
                        if g.fright:
                            g.state = "eyes"
                            g.fright = 0
                            pts = 200 << min(eat_n, 3)
                            eat_n += 1
                            if eat_n >= 4:
                                goal("pac", 1)
                            score += pts
                            sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
                            pops.add(sx, sy - 8, str(pts), TEAL)
                            parts.burst(sx, sy, FRIGHT_C, 12, 2.5, 14)
                        else:
                            dead = 1
                if left == 0:
                    goal("pac", 0)
                    for k in range(8):
                        lcd.fill(P_BGC)
                        p_draw_maze(lcd, fills, edges, dots, False, WHITE if k % 2 == 0 else wall)
                        lcd.show()
                        time.sleep_ms(160)
                    level += 1
                    p_set_maze(level - 1)
                    fills, edges = p_wall_rects()
                    wall = P_WALLS[(level - 1) % len(P_WALLS)]
                    dots = new_dots()
                    left = total = sum(1 for v in dots if v)
                    fruits = fruit_t = 0
                    pops.add(W // 2, 120, "NIVA %d" % level, LIME, 2)
                    break
            else:
                dead += 1
                if dead > 50:
                    lives -= 1
                    if lives <= 0:
                        return score
                    break
            # --- Rita ---
            lcd.fill(P_BGC)
            p_draw_maze(lcd, fills, edges, dots, (t // 8) % 2 == 0, wall)
            if fruit_t:
                fruit_t -= 1
                if fruit_t > 60 or (t // 4) % 2:
                    p_cherry(lcd, PX0 + 105, PY0 + 115)
            for g in ghosts:
                gx, gy = g.pos()
                sx, sy = PX0 + int(gx * PT) + 5, PY0 + int(gy * PT) + 5
                if g.state == "house":
                    sy += int(2 * math.sin(t * 0.2 + g.i))
                if dead and dead > 10:
                    continue
                if g.state == "eyes":
                    draw_ghost(lcd, sx, sy, 0, g.d, t, True)
                elif g.fright:
                    flash = fright_t < 50 and (t // 5) % 2
                    draw_ghost(lcd, sx, sy, WHITE if flash else FRIGHT_C, g.d, t, False, True)
                else:
                    draw_ghost(lcd, sx, sy, GHOST_C[g.i], g.d, t)
            ppx, ppy = pac.pos()
            sx, sy = PX0 + int(ppx * PT) + 5, PY0 + int(ppy * PT) + 5
            if dead:
                m = min(3.1, 0.5 + dead * 0.07)
                if m < 3.0:
                    draw_pac(lcd, sx, sy, 0, m)
            else:
                mouth = abs(math.sin(t * 0.5)) if pac.d >= 0 else 0.4
                draw_pac(lcd, sx, sy, face, mouth)
            parts.draw(lcd)
            pops.draw(lcd)
            # Poäng och liv
            if score >= 5000:
                goal("pac", 2)
            big(lcd, str(score), PX0, 6, WHITE, 2)
            rtext(lcd, "NIVA %d" % level, PX0 + MW * PT, 10, LIME)
            for i in range(lives - 1):
                draw_pac(lcd, 140 + i * 14, 13, 1, 0.6, P_YEL, 4)
            if ready > 0:
                ctext(lcd, "REDO!", PY0 + 13 * PT + 1, P_YEL, 1)
            arrow(lcd, 14, 14, 0, DIM)
            arrow(lcd, W - 14, 14, 1, DIM)
            arrow(lcd, W - 14, H - 14, 2, DIM)
            arrow(lcd, 14, H - 14, 3, DIM)
            lcd.show()
            t += 1
            wait(t0)


