"""Bygger banorna till ÄVENTYR och kontrollerar att de går att klara.

Tecken:  # mark   B sten   X spricka (krossas med dash)   c smular   = moln/planka
         I is   ^ spikar   L lava   S studsfjäder   o mynt   G ädelsten
         C kontrollpunkt   E mål   P start   w vandrare   k igelkott   f flygare

Kör:  python3 gen_aventyr.py   (skriver aventyr_banor.txt och aventyr_*.png)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = 15


class Lv:
    def __init__(self, w):
        self.w = w
        self.g = [[" "] * w for _ in range(ROWS)]

    def put(self, x, y, ch):
        self.g[y][x] = ch

    def fill(self, x0, x1, y0, y1, ch):
        """Fyll kolumn x0..x1-1, rad y0..y1-1."""
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.g[y][x] = ch

    def ground(self, x0, x1, top, ch="#"):
        self.fill(x0, x1, top, ROWS, ch)

    def row(self, x0, x1, y, ch):
        self.fill(x0, x1, y, y + 1, ch)

    def coins(self, x0, x1, y):
        for x in range(x0, x1):
            if self.g[y][x] == " ":
                self.g[y][x] = "o"

    def pit(self, x0, x1, ch="#", haz="^"):
        """Grop med spikar (eller lava) i botten."""
        self.fill(x0, x1, 0, ROWS, " ")
        self.fill(x0, x1, 14, 15, ch)
        self.fill(x0, x1, 13, 14, haz)

    def rows(self):
        return tuple("".join(r) for r in self.g)


def level1():
    L = Lv(96)
    L.ground(0, 20, 12)
    L.put(2, 11, "P")
    L.coins(5, 10, 10)
    L.ground(20, 30, 11)
    L.put(26, 10, "w")
    L.coins(30, 33, 8)
    L.ground(33, 45, 12)
    L.row(36, 41, 9, "=")
    L.put(38, 8, "G")
    L.put(43, 11, "B"); L.put(44, 11, "B"); L.put(44, 10, "B")
    L.ground(45, 60, 12)
    L.put(47, 11, "C")
    L.put(52, 11, "w"); L.put(57, 11, "w")
    L.coins(50, 58, 8)
    L.ground(60, 66, 10)
    L.ground(66, 72, 8)
    L.row(66, 72, 5, "=")
    L.put(69, 4, "G")
    L.coins(67, 71, 7)
    L.ground(72, 80, 12)
    L.put(76, 11, "w")
    L.ground(80, 84, 14)
    L.row(80, 84, 13, "^")
    L.ground(84, 96, 12)
    L.put(86, 11, "B"); L.put(87, 11, "B"); L.put(87, 10, "B"); L.put(88, 10, "B")
    L.put(88, 9, "B"); L.put(88, 7, "G")
    L.coins(80, 84, 9)
    L.put(93, 11, "E")
    return L


def level2():
    L = Lv(100)
    L.fill(0, 100, 0, 3, "#")
    L.ground(0, 100, 12)
    L.put(2, 11, "P")
    L.coins(4, 9, 10)
    L.fill(12, 14, 3, 12, "X")                  # vägg: dasha igenom
    L.fill(17, 24, 3, 10, "#")                  # lågt tak över spikarna
    L.ground(18, 22, 13)
    L.row(18, 22, 12, "^")
    L.fill(18, 22, 12, 13, "^")
    L.put(26, 11, "C")
    L.ground(30, 36, 10)
    L.row(30, 36, 8, "=")
    L.put(33, 7, "G")
    L.coins(31, 35, 9)
    L.put(38, 11, "w")
    L.fill(40, 45, 8, 12, "X")                  # skattrum
    L.fill(41, 44, 9, 12, " ")
    L.put(42, 11, "G")
    L.put(50, 11, "k")
    L.coins(48, 53, 8)
    L.fill(58, 73, 12, 13, "^")
    L.fill(58, 73, 13, 15, "#")
    L.fill(61, 62, 10, 12, "B")
    L.fill(65, 66, 9, 12, "B")
    L.fill(69, 70, 10, 12, "B")
    L.put(65, 7, "o"); L.put(61, 8, "o"); L.put(69, 8, "o")
    L.put(75, 11, "C")
    L.fill(79, 84, 3, 5, " ")                   # hål i taket
    L.put(81, 11, "S")
    L.put(81, 4, "G")
    L.put(88, 11, "k")
    L.fill(91, 93, 3, 12, "X")
    L.put(96, 11, "E")
    return L


def level3():
    L = Lv(100)
    L.ground(0, 9, 11)
    L.put(2, 10, "P")
    L.row(11, 15, 10, "="); L.coins(11, 15, 9)
    L.row(17, 21, 8, "="); L.coins(17, 21, 7)
    L.row(23, 27, 9, "=")
    L.ground(29, 37, 11)
    L.put(31, 10, "C")
    L.put(34, 10, "w")
    L.put(36, 10, "S")
    L.row(33, 39, 4, "=")
    L.put(37, 3, "G")
    L.row(40, 44, 9, "=")
    L.put(42, 6, "f")
    L.row(46, 49, 7, "=")
    L.row(51, 55, 9, "=")
    L.put(53, 5, "f")
    L.row(57, 61, 10, "=")
    L.coins(46, 49, 6)
    L.ground(62, 71, 12)
    L.put(64, 11, "C")
    L.put(69, 11, "k")
    L.row(73, 76, 10, "c")
    L.row(78, 81, 8, "c")
    L.put(79, 6, "G")
    L.row(83, 86, 10, "c")
    L.ground(88, 100, 11)
    L.row(92, 97, 8, "=")
    L.put(95, 6, "G")
    L.coins(89, 92, 9)
    L.put(98, 10, "E")
    return L


def level4():
    L = Lv(110)
    L.ground(0, 110, 12)
    L.put(2, 11, "P")
    for x, top in ((8, 9), (22, 6), (40, 9), (58, 6), (80, 9), (96, 6)):   # träd
        L.fill(x, x + 1, top, 12, "T")
        L.row(x - 2, x + 3, top, "=")
        if top < 9:
            L.row(x - 3, x + 4, 9, "=")
    L.coins(6, 11, 8)
    L.put(14, 11, "w"); L.put(18, 11, "w")
    L.put(22, 4, "G")
    L.row(26, 30, 9, "=")
    L.ground(30, 34, 10)
    L.put(31, 9, "w")
    L.pit(34, 38)
    L.put(44, 11, "C")
    L.put(48, 11, "k")
    L.put(52, 11, "w")
    L.row(50, 55, 9, "c")
    L.coins(50, 55, 8)
    L.put(58, 4, "G")
    L.put(62, 11, "w"); L.put(66, 11, "w"); L.put(70, 11, "k")
    L.pit(72, 76)
    L.put(78, 11, "C")
    L.fill(86, 88, 6, 12, "X")
    L.fill(86, 88, 6, 7, "B")
    L.put(90, 11, "G")
    L.fill(89, 92, 8, 9, "B")
    L.put(100, 11, "w")
    L.coins(98, 104, 9)
    L.put(106, 11, "E")
    return L


def level5():
    L = Lv(100)
    L.ground(0, 100, 12, "I")
    L.put(2, 11, "P")
    L.coins(5, 12, 10)
    L.pit(14, 18, "I")
    L.ground(22, 26, 10, "I")
    L.ground(26, 30, 8, "I")
    L.pit(30, 34, "I")
    L.row(28, 33, 5, "=")
    L.put(31, 4, "G")
    L.put(36, 11, "C")
    L.put(40, 11, "w"); L.put(45, 11, "k")
    L.pit(50, 56, "I")
    L.row(52, 54, 9, "B")
    L.put(53, 8, "o")
    L.put(58, 11, "C")
    L.fill(62, 64, 3, 12, "X")
    L.put(67, 10, "f")
    L.ground(70, 74, 9, "I")
    L.row(66, 70, 5, "=")
    L.put(67, 4, "G")
    L.pit(76, 80, "I")
    L.put(84, 11, "S")
    L.row(86, 92, 5, "=")
    L.put(90, 4, "G")
    L.put(88, 11, "k")
    L.coins(86, 92, 4)
    L.put(96, 11, "E")
    return L


def level6():
    L = Lv(100)
    L.fill(0, 100, 13, 15, "L")
    L.ground(0, 8, 11)
    L.put(2, 10, "P")
    L.fill(10, 13, 10, 11, "B")
    L.fill(15, 17, 9, 10, "c")
    L.fill(19, 22, 10, 11, "B")
    L.coins(15, 17, 8)
    L.ground(24, 34, 11)
    L.coins(27, 33, 8)
    L.put(26, 10, "C")
    L.put(30, 10, "k")
    L.row(36, 38, 9, "c"); L.row(40, 42, 7, "c")
    L.put(41, 5, "G")
    L.row(44, 46, 9, "c")
    L.ground(48, 56, 11)
    L.put(50, 10, "C")
    L.put(53, 10, "w")
    L.put(55, 10, "S")
    L.row(55, 60, 3, "=")
    L.put(58, 2, "G")
    L.row(58, 61, 9, "B")
    L.put(63, 6, "f")
    L.row(64, 67, 9, "B")
    L.row(69, 71, 8, "c")
    L.row(73, 76, 9, "B")
    L.coins(64, 76, 6)
    L.ground(78, 86, 11)
    L.put(80, 10, "C")
    L.fill(84, 86, 4, 11, "X")
    L.put(88, 7, "G")
    L.row(87, 90, 8, "B")
    L.ground(90, 100, 11)
    L.put(93, 10, "k")
    L.put(97, 10, "E")
    return L


def level7():
    L = Lv(110)
    L.fill(0, 110, 0, 2, "B")
    L.ground(0, 110, 12, "B")
    L.put(2, 11, "P")
    L.fill(8, 10, 2, 9, "B")                     # tak ner, lågt hopp
    L.put(13, 11, "k")
    L.fill(16, 18, 2, 12, "X")
    L.ground(21, 25, 13, "B"); L.fill(21, 25, 12, 13, "^")
    L.coins(20, 26, 9)
    L.put(28, 11, "C")
    L.row(30, 34, 9, "B"); L.row(35, 39, 6, "B")
    L.put(37, 5, "G")
    L.put(33, 6, "f")
    L.ground(40, 52, 13, "B"); L.fill(40, 52, 12, 13, "^")
    L.put(43, 9, "B"); L.put(47, 9, "B"); L.put(51, 9, "B")
    L.put(43, 7, "o"); L.put(47, 7, "o"); L.put(51, 7, "o")
    L.coins(56, 66, 9)
    L.put(45, 6, "f")
    L.put(54, 11, "C")
    L.put(58, 11, "k"); L.put(62, 11, "w"); L.put(65, 11, "k")
    L.fill(68, 74, 2, 10, "B")
    L.fill(68, 74, 9, 10, "^")
    L.put(71, 11, "G")
    L.put(77, 11, "C")
    L.fill(80, 82, 2, 12, "X")
    L.ground(84, 96, 13, "B"); L.fill(84, 96, 12, 13, "^")
    L.put(86, 10, "c"); L.put(89, 9, "c"); L.put(92, 10, "c"); L.put(95, 9, "c")
    L.put(86, 8, "o"); L.put(89, 7, "o"); L.put(92, 8, "o"); L.put(95, 7, "o")
    L.put(90, 6, "f")
    L.row(98, 102, 8, "B")
    L.put(100, 7, "G")
    L.put(104, 11, "k")
    L.put(107, 11, "E")
    return L


def level8():
    L = Lv(120)
    L.ground(0, 10, 12)
    L.put(2, 11, "P")
    L.put(8, 11, "S")
    L.row(8, 14, 4, "=")
    L.coins(9, 13, 3)
    L.row(16, 19, 6, "c")
    L.row(21, 24, 8, "=")
    L.put(22, 5, "f")
    L.ground(26, 34, 11, "I")
    L.put(28, 10, "C")
    L.put(31, 10, "k")
    L.fill(34, 46, 13, 15, "L")
    L.put(36, 10, "B"); L.put(39, 9, "B"); L.put(42, 10, "B")
    L.put(39, 6, "G")
    L.ground(46, 56, 11)
    L.put(48, 10, "C")
    L.fill(52, 54, 2, 11, "X")
    L.put(55, 10, "w")
    L.pit(56, 62)
    L.row(57, 61, 9, "c")
    L.ground(62, 70, 11)
    L.put(66, 10, "S")
    L.row(64, 70, 4, "=")
    L.put(67, 3, "G")
    L.put(69, 10, "k")
    L.fill(70, 86, 13, 15, "L")
    L.row(72, 75, 10, "="); L.row(77, 80, 8, "="); L.row(82, 85, 10, "=")
    L.put(74, 6, "f"); L.put(81, 5, "f")
    L.coins(72, 85, 6)
    L.ground(86, 96, 11)
    L.put(88, 10, "C")
    L.put(92, 10, "w"); L.put(94, 10, "k")
    L.pit(96, 100)
    L.ground(100, 120, 11)
    L.fill(104, 106, 3, 11, "X")
    L.row(108, 112, 7, "B")
    L.put(110, 6, "G")
    L.put(112, 10, "w")
    L.put(116, 10, "E")
    return L


LEVELS = (
    ("ANGEN", 0, "0/1 spring  2 hoppa", level1),
    ("GROTTAN", 1, "3 = dash! Krossar sprickor", level2),
    ("MOLNEN", 2, "Ramla inte ner!", level3),
    ("SKOGEN", 3, "Hoppa pa monstren", level4),
    ("ISEN", 4, "Det ar halt!", level5),
    ("VULKANEN", 5, "Akta lavan!", level6),
    ("BORGEN", 6, "Dasha igelkottarna", level7),
    ("TOPPEN", 7, "Allt pa en gang!", level8),
)

SOLID = set("#BXcI")              # T = trädstam (bara utseende)
STAND = SOLID | set("=S")
HAZ = set("^L")


def check(rows):
    """Grov kontroll: kan man nå målet, alla ädelstenar och mynt från start?"""
    w = len(rows[0])
    g = [list(r) for r in rows]

    def at(x, y):
        if x < 0 or x >= w:
            return "#"
        if y < 0:
            return " "
        if y >= ROWS:
            return " "
        return g[y][x]

    def air(x, y):
        c = at(x, y)
        return c not in SOLID or c == "X"

    def standable(x, y):
        return air(x, y) and at(x, y) not in HAZ and y + 1 < ROWS and at(x, y + 1) in STAND

    start = None
    for y in range(ROWS):
        for x in range(w):
            if g[y][x] == "P":
                start = (x, y)
    seen = {start}
    todo = [start]
    while todo:
        x, y = todo.pop()
        up = 7 if at(x, y + 1) == "S" else 3
        # hur högt kan man hoppa härifrån (tak?)
        h = 0
        while h < up and air(x, y - h - 1) and at(x, y - h - 1) not in HAZ:
            h += 1
        for x2 in range(x - 6, x + 7):
            for y2 in range(y - h, ROWS):
                if (x2, y2) in seen or not standable(x2, y2):
                    continue
                dx = abs(x2 - x)
                if y2 < y and dx > 4 and not (dx <= 6 and y - y2 <= 1):
                    continue
                if dx > 4 + (2 if y2 >= y - 1 else 0) + max(0, (y2 - y) // 2):
                    continue
                # fri väg (ungefär): kolla raden ovanför den högsta punkten
                top = min(y, y2) - (1 if y2 >= y else 0)
                ok = True
                step = 1 if x2 >= x else -1
                for xx in range(x, x2 + step, step):
                    if not air(xx, max(0, top)):
                        ok = False
                        break
                if ok:
                    seen.add((x2, y2))
                    todo.append((x2, y2))
    reach = set()
    for x, y in seen:
        hh = 7 if at(x, y + 1) == "S" else 3
        for yy in range(y - hh, y + 1):
            for xx in range(x - 3, x + 4):
                reach.add((xx, yy))
    missing = []
    for y in range(ROWS):
        for x in range(w):
            if g[y][x] in "GEoC" and (x, y) not in reach:
                missing.append((g[y][x], x, y))
    return missing


def render(rows, fn):
    try:
        from PIL import Image
    except ImportError:
        return
    col = {"#": (140, 90, 50), "B": (130, 130, 140), "X": (170, 120, 70), "c": (220, 200, 150),
           "=": (240, 240, 255), "I": (180, 220, 255), "^": (255, 60, 60), "L": (255, 120, 0),
           "S": (255, 0, 255), "o": (255, 220, 0), "G": (0, 255, 200), "C": (0, 200, 0),
           "E": (255, 255, 255), "P": (255, 0, 0), "w": (120, 60, 20), "k": (90, 40, 90),
           "f": (60, 60, 255), "T": (90, 60, 30)}
    w = len(rows[0])
    im = Image.new("RGB", (w * 4, ROWS * 4), (30, 40, 70))
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in col:
                for a in range(4):
                    for b in range(4):
                        px[x * 4 + a, y * 4 + b] = col[ch]
    im.save(fn)


def main():
    out = ["AV_LEVELS = ("]
    bad = False
    for i, (name, pal, hint, fn) in enumerate(LEVELS):
        rows = fn().rows()
        assert sum(r.count("G") for r in rows) == 3, name
        assert sum(r.count("E") for r in rows) == 1, name
        assert sum(r.count("P") for r in rows) == 1, name
        miss = check(rows)
        print(name, len(rows[0]), "mynt", sum(r.count("o") for r in rows), "saknas:", miss)
        bad = bad or bool(miss)
        render(rows, os.path.join(HERE, "aventyr_%d.png" % (i + 1)))
        out.append("    (%r, %d, %r, (" % (name, pal, hint))
        for r in rows:
            out.append("        %r," % r)
        out.append("    )),")
    out.append(")")
    txt = "\n".join(out) + "\n"
    open(os.path.join(HERE, "aventyr_banor.txt"), "w").write(txt)
    # byt in banorna i spelets källkod
    game = os.path.join(HERE, "..", "spel", "aventyr.py")
    src = open(game).read()
    a, b = src.index("AV_LEVELS = ("), src.index("\nTS = 16")
    open(game, "w").write(src[:a] + txt + src[b:])
    print("FEL" if bad else "alla banor ok")


if __name__ == "__main__":
    main()
