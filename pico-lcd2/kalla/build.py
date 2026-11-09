"""Bygger ../main.py av grunden (core_*.py) och spelen (spel/*.py).

Spelens kod läggs längst ner i main.py som kommentarer:
    #@@ namn
    #|rad 1
    #|rad 2
så att Picon bara läser in det spel som väljs.

Kör:  python3 build.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "main.py")

# menynyckel -> fil i spel/
GAME_FILES = (
    ("tetris", "tetris.py"), ("ladr", "ladr.py"), ("flode", "flode.py"),
    ("aventyr", "aventyr.py"), ("studs", "studs.py"), ("pac", "pac.py"),
    ("2048", "g2048.py"), ("invasion", "invasion.py"), ("kross", "kross.py"),
    ("kurvan", "kurvan.py"),
)


def check_menu():
    """Menytexterna får vara högst 20 tecken (rutan är 160 px bred)."""
    import re
    src = open(os.path.join(HERE, "core_menu.py")).read()
    block = src[src.index("GAMES = ("):src.index("def menu(")]
    for desc in re.findall(r'\("[^"]*", "[^"]*", "[^"]*"\)', block):
        for line in re.findall(r'"([^"]*)"', desc):
            assert len(line) <= 20, "for lang menytext: %r" % line


def main():
    check_menu()
    parts = []
    for name in ("core_base.py", "core_menu.py"):
        parts.append(open(os.path.join(HERE, name)).read().rstrip("\n") + "\n\n")
    parts.append("\nmain()\n\n")
    parts.append("# " + "=" * 63 + "\n")
    parts.append("# SPELENS KOD (läses in av load_game när spelet väljs)\n")
    parts.append("# " + "=" * 63 + "\n")
    for key, fn in GAME_FILES:
        path = os.path.join(HERE, "spel", fn)
        src = open(path).read()
        parts.append("#@@ %s\n" % key)
        for line in src.rstrip("\n").split("\n"):
            parts.append("#|" + line + "\n")
    parts.append("#@@ slut\n")
    out = "".join(parts)
    with open(OUT, "w") as f:
        f.write(out)
    print("main.py: %d rader, %d byte" % (out.count("\n"), len(out)))


if __name__ == "__main__":
    main()
