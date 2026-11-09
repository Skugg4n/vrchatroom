# FLODE: koppla ihop prickarna med samma färg och fyll hela rutnätet.
#   0 upp, 1 höger, 2 ner, 3 vänster (pilarna i hörnen)
#   Gå in på en prick (eller slutet av en linje) så ritar du.
#   Tryck två knappar samtidigt för att lyfta/sänka pennan och gå fritt.
#   Håll alla fyra: 0 börja om, 2 fortsätt, 3 till banorna.
# Banorna skapas av en generator: en slingrande väg genom hela rutnätet
# klipps i bitar, och bitarnas ändar blir prickarna. Alltså går varje bana
# att lösa med alla rutor fyllda.

F_RAW = ((235, 60, 60), (60, 120, 255), (60, 200, 80), (250, 220, 50), (255, 140, 30),
         (60, 220, 230), (240, 90, 200), (150, 80, 230), (225, 225, 225))
F_COL = [rgb(*c) for c in F_RAW]
F_DIM = [rgb(c[0] // 4, c[1] // 4, c[2] // 4) for c in F_RAW]
F_BG = [mix((10, 14, 30), (26, 12, 40), y / (H - 1)) for y in range(H)]
F_GRID = rgb(50, 56, 90)
NLEV = 25
F_SOL = [None]                  # senaste lösningen (används av testerna)


class Rng:
    """Egen enkel slump så att banorna blir likadana på Picon och datorn."""
    def __init__(self, s):
        self.s = (s * 7919 + 17) & 0xFFFFFF

    def n(self, m):
        self.s = (self.s * 1103 + 12345) & 0xFFFFFF
        return (self.s >> 4) % m


def f_size(i):
    """Storlek och antal färger för bana i."""
    if i < 5:
        return 5, 4 + i % 2
    if i < 12:
        return 6, 5 + i % 2
    if i < 19:
        return 7, 6 + i % 2
    return 8, 7 + i % 2


def f_gen(w, k, rng):
    n = w * w
    while True:
        path = []
        for y in range(w):
            for x in range(w):
                path.append(y * w + (x if y % 2 == 0 else w - 1 - x))
        for _ in range(n * 10):
            if rng.n(2):
                path.reverse()
            e = path[0]
            dx, dy = DIRS4[rng.n(4)]
            nx, ny = e % w + dx, e // w + dy
            if 0 <= nx < w and 0 <= ny < w:
                i = path.index(ny * w + nx)
                if i > 1:
                    head = path[:i]
                    head.reverse()
                    path = head + path[i:]
        lens = [3] * k
        wt = [1 + rng.n(4) for _ in range(k)]
        for _ in range(n - 3 * k):
            r = rng.n(sum(wt))
            j = 0
            while r >= wt[j]:
                r -= wt[j]
                j += 1
            lens[j] += 1
        dots = []
        a = 0
        ok = True
        for L in lens:
            p, q = path[a], path[a + L - 1]
            if abs(p % w - q % w) + abs(p // w - q // w) <= 1:
                ok = False
            dots.append((p, q))
            a += L
        if ok:
            F_SOL[0] = (path, lens)
            return dots


def f_level(i):
    w, k = f_size(i)
    return w, f_gen(w, k, Rng(i * 31 + 5))


def play(lcd, keys):
    mode = choose(lcd, keys, "FLODE", ("BANOR", "TIDSJAKT"), PINK, "Koppla ihop lika farger")
    if mode is None:
        return None
    if mode == 1:
        return f_rush(lcd, keys)
    done = SCORES.get("flode_done", [0] * NLEV)
    done = (done + [0] * NLEV)[:NLEV]
    sel = 0
    while sel < NLEV - 1 and done[sel]:
        sel += 1
    while True:
        sel = f_select(lcd, keys, done, sel)
        if sel is None:
            return None
        while True:
            w, dots = f_level(sel)
            r = f_play(lcd, keys, w, dots, "BANA %d" % (sel + 1), None)
            if not r:
                break
            done[sel] = max(done[sel], r)
            SCORES["flode_done"] = done
            save_scores()
            c = sum(1 for d in done if d)
            if c >= 5:
                goal("flode", 0)
            if c >= 15:
                goal("flode", 1)
            if sel >= NLEV - 1:
                break
            sel += 1


def f_rush(lcd, keys):
    """TIDSJAKT: lös så många banor du hinner. Varje lösning ger mer tid."""
    rng = Rng(time.ticks_ms() & 0xFFFF)
    clock = [60 * 30]
    solved = 0
    while True:
        w = 5 if solved < 2 else 6 if solved < 5 else 7 if solved < 8 else 8
        k = w - 1 + rng.n(2)
        dots = f_gen(w, k, rng)
        r = f_play(lcd, keys, w, dots, "TIDSJAKT  %d LOSTA" % solved, clock)
        if r is None:
            return None
        if r == -1:
            return ("TIDEN UT!", solved, "flode_tid", "Losta banor:", False, str)
        solved += 1
        clock[0] += (12 if r == 2 else 8) * 30
        if solved >= 5:
            goal("flode", 2)


def f_select(lcd, keys, done, sel):
    stars = Stars(30)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        unlocked = 0
        while unlocked < NLEV and done[unlocked]:
            unlocked += 1
        if keys.repeat(K0, 10, 4):
            sel = (sel - 1) % NLEV
        if keys.repeat(K1, 10, 4):
            sel = (sel + 1) % NLEV
        if keys.pressed(K2) and sel <= unlocked:
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            return None
        gradient(lcd, F_BG)
        stars.draw(lcd)
        big(lcd, "FLODE", 12, 10, SHADOW, 3)
        big(lcd, "FLODE", 10, 8, PINK, 3)
        rtext(lcd, "%d/%d klara" % (sum(1 for d in done if d), NLEV), W - 8, 12, GRAY)
        rtext(lcd, "0/1 valj 2 spela 3 ut", W - 8, 24, DIM)
        for i in range(NLEV):
            x = 14 + (i % 5) * 60
            y = 40 + (i // 5) * 33
            if i == sel:
                lcd.fill_rect(x - 3, y - 3, 58, 30, WHITE)
            c = YELLOW if done[i] == 2 else rgb(90, 200, 110) if done[i] else PINK if i <= unlocked else LINE
            lcd.fill_rect(x, y, 52, 24, c)
            ctext(lcd, str(i + 1), y + 4, BG, 2, x + 26)
        w, k = f_size(sel)
        lcd.fill_rect(10, 208, 300, 26, PANEL)
        if sel > unlocked:
            ctext(lcd, "Klara banan innan forst", 217, AMBER)
        else:
            txt = "%dx%d  %d farger" % (w, w, k)
            if done[sel] == 2:
                txt += "  PERFEKT"
            elif done[sel]:
                txt += "  klar"
            ctext(lcd, txt, 217, WHITE)
        lcd.show()
        wait(t0)


def f_draw(lcd, w, dots, paths, occ, cur, pen, ox, oy, s, t, hud):
    gradient(lcd, F_BG)
    for c in range(w * w):
        k = occ[c]
        x, y = ox + (c % w) * s, oy + (c // w) * s
        if k >= 0:
            lcd.fill_rect(x + 1, y + 1, s - 1, s - 1, F_DIM[k])
    for i in range(w + 1):
        lcd.hline(ox, oy + i * s, w * s, F_GRID)
        lcd.vline(ox + i * s, oy, w * s, F_GRID)
    lw = max(4, s // 3)
    h2 = s // 2
    for k, p in enumerate(paths):
        col = F_COL[k]
        for j in range(1, len(p)):
            a, b = p[j - 1], p[j]
            ax, ay = ox + (a % w) * s + h2, oy + (a // w) * s + h2
            bx, by = ox + (b % w) * s + h2, oy + (b // w) * s + h2
            lcd.fill_rect(min(ax, bx) - lw // 2, min(ay, by) - lw // 2,
                          abs(ax - bx) + lw, abs(ay - by) + lw, col)
    r = s * 3 // 10
    for k, (a, b) in enumerate(dots):
        for c in (a, b):
            lcd.ellipse(ox + (c % w) * s + h2, oy + (c // w) * s + h2, r, r, F_COL[k], True)
    cx, cy = ox + (cur % w) * s, oy + (cur // w) * s
    if pen >= 0:
        cc = F_COL[pen]
        lcd.rect(cx - 1, cy - 1, s + 3, s + 3, cc)
        lcd.rect(cx, cy, s + 1, s + 1, WHITE if (t // 4) % 2 else cc)
    else:
        lcd.rect(cx, cy, s + 1, s + 1, WHITE)
        lcd.rect(cx + 1, cy + 1, s - 1, s - 1, WHITE)
    lcd.fill_rect(0, 0, W, 14, BG)
    lcd.text(hud, 4, 3, WHITE)
    for d, (x, y) in enumerate(((10, 24), (W - 10, 24), (W - 10, H - 10), (10, H - 10))):
        arrow(lcd, x, y, d, DIM, 4)
    ctext(lcd, "2 knappar samtidigt = lyft pennan", 231, DIM)


def f_play(lcd, keys, w, dots, title, clock):
    """Spelar en bana. Svar: 1 klar, 2 perfekt, None avbruten, -1 tiden slut."""
    n = w * w
    s = min(38, (H - 34) // w)
    ox = (W - w * s) // 2
    oy = 16 + (H - 16 - w * s) // 2
    dot_at = {}
    for k, (a, b) in enumerate(dots):
        dot_at[a] = k
        dot_at[b] = k
    paths = [[] for _ in dots]
    occ = [-1] * n
    cur = dots[0][0]
    pen = -1
    snap = None
    snap_t = -99
    parts = Particles(60)
    t = 0
    keys.wait_release()

    def complete(k):
        p = paths[k]
        return len(p) > 1 and p[0] in dot_at and p[-1] in dot_at and p[0] != p[-1]

    def engage(c):
        # Gå in på en prick eller ett linjeslut: pennan tar den färgen.
        for k, p in enumerate(paths):
            if len(p) > 1 and p[-1] == c:
                return k
        k = dot_at.get(c, -1)
        if k >= 0 and (not paths[k] or len(paths[k]) == 1):
            paths[k] = [c]
            return k
        return -1

    pen = engage(cur)

    def pos(c):
        return ox + (c % w) * s + s // 2, oy + (c // w) * s + s // 2

    while True:
        t0 = time.ticks_ms()
        keys.update()
        if clock is not None:
            clock[0] -= 1
            if clock[0] <= 0:
                for _ in range(45):
                    t1 = time.ticks_ms()
                    f_draw(lcd, w, dots, paths, occ, cur, -1, ox, oy, s, t, title)
                    stext(lcd, "TIDEN UT!", 100, CORAL, 4)
                    lcd.show()
                    wait(t1)
                return -1
        if keys.pause():
            r = f_pause(lcd, keys)
            if r == "exit":
                return None
            if r == "restart":
                paths = [[] for _ in dots]
                pen = -1
        held = sum(keys.now)
        if held == 2 and sum(keys.prev) < 2:
            # två knappar samtidigt: lyft/sänk pennan (ångra steget den första gav)
            if snap and t - snap_t <= 5:
                cur, pen, paths = snap
            pen = -1 if pen >= 0 else engage(cur)
            snap = None
        for d in (K0, K1, K2, K3):
            if held != 1 or not keys.repeat(d, 7, 3):
                continue
            dx, dy = DIRS4[d]
            x, y = cur % w + dx, cur // w + dy
            if not (0 <= x < w and 0 <= y < w):
                break
            nc = y * w + x
            snap = (cur, pen, [list(q) for q in paths])
            snap_t = t
            if pen >= 0:
                p = paths[pen]
                if len(p) >= 2 and nc == p[-2]:
                    p.pop()
                    cur = nc
                elif nc in p:
                    paths[pen] = p[:p.index(nc) + 1]
                    cur = nc
                elif dot_at.get(nc, pen) != pen or complete(pen):
                    pen = -1                    # annan prick / klar linje: lyft pennan
                    cur = nc
                    pen = engage(nc)
                else:
                    j = occ[nc]
                    if j >= 0 and j != pen:     # skär av en annan linje
                        q = paths[j]
                        paths[j] = q[:q.index(nc)]
                    p.append(nc)
                    cur = nc
                    if dot_at.get(nc) == pen:
                        x2, y2 = pos(nc)
                        parts.burst(x2, y2, F_COL[pen], 12, 2.5, 14)
                        pen = -1
            else:
                cur = nc
                pen = engage(nc)
            break
        occ = [-1] * n
        for k, p in enumerate(paths):
            for c in p:
                occ[c] = k
        fills = sum(1 for c in occ if c >= 0)
        hud = "%s  %d%%" % (title, fills * 100 // n)
        f_draw(lcd, w, dots, paths, occ, cur, pen, ox, oy, s, t, hud)
        if clock is not None:
            sec = clock[0] // 30
            rtext(lcd, "%d:%02d" % (sec // 60, sec % 60), W - 4, 3, CORAL if sec < 10 else WHITE)
        parts.draw(lcd)
        if all(complete(k) for k in range(len(dots))):
            perfect = fills == n
            for f in range(30 if clock is not None else 45):
                t1 = time.ticks_ms()
                f_draw(lcd, w, dots, paths, occ, cur, -1, ox, oy, s, t + f, hud)
                if perfect:
                    for _ in range(8):
                        lcd.fill_rect(random.randint(0, W - 3), random.randint(16, H - 3), 3, 3,
                                      random.choice(CONFETTI))
                stext(lcd, "PERFEKT!" if perfect else "KLART!", 92, LIME if perfect else SKY, 4)
                if not perfect:
                    ctext(lcd, "Fyll alla rutor for PERFEKT", 136, WHITE)
                lcd.show()
                wait(t1)
            return 2 if perfect else 1
        lcd.show()
        t += 1
        wait(t0)


def f_pause(lcd, keys):
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K0):
            keys.wait_release()
            return "restart"
        if keys.pressed(K2):
            keys.wait_release()
            return None
        if keys.pressed(K3):
            keys.wait_release()
            return "exit"
        lcd.fill_rect(40, 70, 240, 100, PANEL)
        lcd.rect(40, 70, 240, 100, PINK)
        ctext(lcd, "PAUS", 82, PINK, 2)
        ctext(lcd, "0 borja om", 110, WHITE)
        ctext(lcd, "2 fortsatt", 126, WHITE)
        ctext(lcd, "3 till banorna", 142, WHITE)
        lcd.show()
        wait(t0)
