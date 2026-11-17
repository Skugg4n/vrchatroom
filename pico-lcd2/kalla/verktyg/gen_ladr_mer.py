"""Fler LÅDOR-banor (21 och uppåt). Skriver varje bana direkt till ladr_mer.txt.
Kör: python3 gen_ladr_mer.py"""
import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_ladr import make_level, to_rows

PLAN = [(2, 8, 7, 8, 14)] * 6 + [(3, 9, 8, 12, 30)] * 10 + [(4, 9, 8, 14, 40)] * 10 \
    + [(4, 10, 9, 16, 50)] * 8 + [(5, 10, 9, 16, 60)] * 6


def main():
    rnd = random.Random(777)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladr_mer.txt")
    have = []
    if os.path.exists(out):
        have = [l for l in open(out) if l.startswith("    (")]
    seen = set(have)
    for i, (nbox, w, h, lo, hi) in enumerate(PLAN):
        if i < len(have):
            continue
        while True:
            lvl = make_level(rnd, w, h, nbox, 300 + nbox * 150)
            if lvl and lo <= lvl[4] <= hi:
                rows = to_rows(*lvl[:4])
                line = "    (%d, (%s)),\n" % (lvl[4], ", ".join(repr(r) for r in rows))
                if line not in seen:
                    break
        seen.add(line)
        with open(out, "a") as f:
            f.write(line)
        print("bana", 21 + i, "lador", nbox, "knuffar", lvl[4], flush=True)


if __name__ == "__main__":
    main()
