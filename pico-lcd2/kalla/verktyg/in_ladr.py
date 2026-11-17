"""För in banorna (ladr_banor.txt + ladr_mer.txt) i spel/ladr.py.  Kör: python3 in_ladr.py"""
import os
H = os.path.dirname(os.path.abspath(__file__))
first = [l.split("  # minst")[0].rstrip() + "\n" for l in open(os.path.join(H, "ladr_banor.txt")) if l.startswith("    (")]
mer = [l for l in open(os.path.join(H, "ladr_mer.txt")) if l.startswith("    (")]
lv = "LEVELS = (\n" + "".join(first + mer) + ")\n"
p = os.path.join(H, "..", "spel", "ladr.py")
s = open(p).read()
a = s.index("LEVELS = (")
b = s.index("\n)\n", a) + 3
open(p, "w").write(s[:a] + lv + s[b:])
print("banor:", len(first) + len(mer))
