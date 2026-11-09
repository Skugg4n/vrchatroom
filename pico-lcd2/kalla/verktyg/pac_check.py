"""Kontrollerar SPÖKJAKTs labyrinter: allt hänger ihop, inga återvändsgränder,
inga öppna 2x2-ytor, och spökhus/tunnel/start ligger rätt.  Kör: python3 pac_check.py"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "spel", "pac.py")).read()
block = src[src.index("P_HALVES = ("):src.index("\n)\n", src.index("P_HALVES = (")) + 3]
ns = {}
exec(block, ns)
MW, MH = 21, 21
ok_all = True
for n, half in enumerate(ns["P_HALVES"]):
    assert len(half) == MH, (n, len(half))
    for r in half:
        assert len(r) == 11, (n, r)
    maze = [h + "".join(h[9 - i] for i in range(10)) for h in half]
    walk = lambda x, y: 0 <= y < MH and maze[y][x % MW] in ".o"
    cells = [(x, y) for y in range(MH) for x in range(MW) if maze[y][x] in ".o"]
    errs = []
    # sammanhängande
    seen = {cells[0]}
    todo = [cells[0]]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = (x + dx) % MW, y + dy
            if walk(nx, ny) and (nx, ny) not in seen:
                seen.add((nx, ny))
                todo.append((nx, ny))
    if len(seen) != len(cells):
        errs.append("ej sammanhängande: %s" % sorted(set(cells) - seen)[:6])
    for x, y in cells:
        nb = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if walk((x + dx) % MW, y + dy))
        if nb < 2:
            errs.append("återvändsgränd %s" % ((x, y),))
        if x < MW - 1 and y < MH - 1 and walk(x + 1, y) and walk(x, y + 1) and walk(x + 1, y + 1):
            errs.append("2x2 %s" % ((x, y),))
    if maze[15][10] != ".":
        errs.append("start (10,15) är inte gång")
    if sum(r.count("o") for r in maze) != 4:
        errs.append("inte 4 kraftpiller")
    for y in range(6, 13):
        if half[y] != ns["P_HALVES"][0][y]:
            errs.append("rad %d skiljer sig från första labyrinten (spökhuset)" % y)
    print("labyrint", n + 1, "prickar", len(cells), "OK" if not errs else errs[:8])
    for r in maze:
        print("   ", r)
    ok_all = ok_all and not errs
print("ALLA OK" if ok_all else "FEL")
