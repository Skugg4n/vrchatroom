"""Skapar banor till LÅDOR (Sokoban) och kontrollerar dem med en lösare.

Banorna byggs baklänges: lådorna börjar på målen och gubben drar dem
slumpmässigt runt. Sedan räknar en bredden-först-lösare ut minsta antalet
knuffar, så att vi vet att banan går att klara och hur svår den är.
Kör: python3 gen_ladr.py > ladr_banor.txt
"""
import random, sys
from collections import deque

D = ((0, -1), (1, 0), (0, 1), (-1, 0))


def make_room(w, h, rnd):
    g = [[1] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            g[y][x] = 0
    for _ in range(rnd.randint(w * h // 12, w * h // 7)):
        x, y = rnd.randint(1, w - 2), rnd.randint(1, h - 2)
        g[y][x] = 1
    return g


def floor_cells(g):
    return [(x, y) for y in range(len(g)) for x in range(len(g[0])) if g[y][x] == 0]


def connected(g):
    cells = floor_cells(g)
    if not cells:
        return False
    s = {cells[0]}
    q = [cells[0]]
    while q:
        x, y = q.pop()
        for dx, dy in D:
            n = (x + dx, y + dy)
            if g[n[1]][n[0]] == 0 and n not in s:
                s.add(n)
                q.append(n)
    return len(s) == len(cells)


def reach(g, boxes, p):
    s = {p}
    q = [p]
    while q:
        x, y = q.pop()
        for dx, dy in D:
            n = (x + dx, y + dy)
            if g[n[1]][n[0]] == 0 and n not in boxes and n not in s:
                s.add(n)
                q.append(n)
    return s


def solve(g, goals, boxes, p, limit=200000):
    """Minsta antal knuffar (bredden först), eller None."""
    goals = frozenset(goals)
    # Döda hörn: rutor där en låda aldrig kan flyttas till ett mål
    dead = set()
    for (x, y) in floor_cells(g):
        if (x, y) in goals:
            continue
        wall = [g[y + dy][x + dx] == 1 for dx, dy in D]
        if (wall[0] or wall[2]) and (wall[1] or wall[3]):
            dead.add((x, y))
    start = (frozenset(boxes), min(reach(g, set(boxes), p)))
    seen = {start}
    q = deque([(frozenset(boxes), p, 0)])
    n = 0
    while q:
        bx, pp, d = q.popleft()
        n += 1
        if n > limit:
            return None
        if bx <= goals:
            return d
        r = reach(g, bx, pp)
        for b in bx:
            for dx, dy in D:
                stand = (b[0] - dx, b[1] - dy)
                to = (b[0] + dx, b[1] + dy)
                if stand in r and g[to[1]][to[0]] == 0 and to not in bx and to not in dead:
                    nb = (bx - {b}) | {to}
                    key = (nb, min(reach(g, set(nb), b)))
                    if key not in seen:
                        seen.add(key)
                        q.append((nb, b, d + 1))
    return None


def make_level(rnd, w, h, nbox, pulls):
    for _ in range(200):
        g = make_room(w, h, rnd)
        if not connected(g):
            continue
        cells = floor_cells(g)
        if len(cells) < nbox * 4 + 6:
            continue
        goals = rnd.sample(cells, nbox)
        boxes = set(goals)
        free = [c for c in cells if c not in boxes]
        p = rnd.choice(free)
        for _ in range(pulls):
            dx, dy = rnd.choice(D)
            nxt = (p[0] + dx, p[1] + dy)
            if g[nxt[1]][nxt[0]] == 1 or nxt in boxes:
                continue
            behind = (p[0] - dx, p[1] - dy)
            if behind in boxes and rnd.random() < 0.8:
                boxes.remove(behind)
                boxes.add(p)
            p = nxt
        if len(boxes & set(goals)) > 0:
            continue
        pushes = solve(g, goals, boxes, p)
        if pushes is None:
            continue
        return g, goals, boxes, p, pushes
    return None


def to_rows(g, goals, boxes, p):
    h, w = len(g), len(g[0])
    # Ta bort väggar som inte rör någon golvruta
    rows = []
    for y in range(h):
        r = ""
        for x in range(w):
            c = (x, y)
            if g[y][x] == 1:
                near = any(0 <= x + dx < w and 0 <= y + dy < h and g[y + dy][x + dx] == 0
                           for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                r += "#" if near else "-"
            elif c in boxes:
                r += "*" if c in goals else "$"
            elif c == p:
                r += "+" if c in goals else "@"
            else:
                r += "." if c in goals else " "
        rows.append(r)
    return rows


def main():
    rnd = random.Random(2026)
    plan = [(2, 7, 6, 4, 8)] * 5 + [(3, 8, 7, 8, 16)] * 7 + [(3, 9, 8, 14, 30)] * 5 + [(4, 9, 8, 16, 40)] * 3
    out = []
    for nbox, w, h, lo, hi in plan:
        while True:
            lvl = make_level(rnd, w, h, nbox, 300 + nbox * 150)
            if lvl and lo <= lvl[4] <= hi:
                break
        g, goals, boxes, p, pushes = lvl
        out.append((pushes, to_rows(g, goals, boxes, p)))
        print("bana", len(out), "lador", nbox, "knuffar", pushes, file=sys.stderr)
    print("LEVELS = (")
    for pushes, rows in out:
        print("    (%d, (%s)),  # minst %d knuffar" % (pushes, ", ".join(repr(r) for r in rows), pushes))
    print(")")


if __name__ == "__main__":
    main()
