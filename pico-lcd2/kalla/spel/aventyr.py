# AVENTYR: plattformsspel med 8 banor.
#   0 vänster, 1 höger, 2 hoppa (håll = högre), 3 dash (krossar sprickor och monster)
#   Ta mynt och de 3 ädelstenarna på varje bana. Flaggor = kontrollpunkter.
#   Håll alla fyra: paus (2 fortsätt, 3 till banorna).
# Banorna byggs av verktyg/gen_aventyr.py, som också kollar att allt går att nå.

AV_LEVELS = (
    ('ANGEN', 0, '0/1 spring  2 hoppa', (
        '                                                                                                ',
        '                                                                                                ',
        '                                                                                                ',
        '                                                                                                ',
        '                                                                     G                          ',
        '                                                                  ======                        ',
        '                                                                                                ',
        '                                                                   oooo                 G       ',
        '                              ooo     G           oooooooo        ######                        ',
        '                                    =====                         ######        oooo    B       ',
        '     ooooo                w                 B               ############               BB       ',
        '  P                 ##########             BB  C    w    w  ############    w         BB     E  ',
        '##############################   ###############################################    ############',
        '##############################   ###############################################^^^^############',
        '##############################   ###############################################################',
    )),
    ('GROTTAN', 1, '3 = dash! Krossar sprickor', (
        '####################################################################################################',
        '####################################################################################################',
        '####################################################################################################',
        '            XX   #######                                                                   XX       ',
        '            XX   #######                                                         G         XX       ',
        '            XX   #######                                                                   XX       ',
        '            XX   #######                                                                   XX       ',
        '            XX   #######         G                               o                         XX       ',
        '            XX   #######      ======    XXXXX   ooooo        o       o                     XX       ',
        '            XX   #######       oooo     X   X                    B                         XX       ',
        '    ooooo   XX                ######    X   X                B   B   B                     XX       ',
        '  P         XX            C   ######  w X G X     k          B   B   B     C     S      k  XX   E   ',
        '##################^^^^####################################^^^^^^^^^^^^^^^###########################',
        '####################################################################################################',
        '####################################################################################################',
    )),
    ('MOLNEN', 2, 'Ramla inte ner!', (
        '                                                                                                    ',
        '                                                                                                    ',
        '                                                                                                    ',
        '                                     G                                                              ',
        '                                 ======                                                             ',
        '                                                     f                                              ',
        '                                          f   ooo                              G               G    ',
        '                 oooo                         ===                                                   ',
        '                 ====                                                         ccc           =====   ',
        '           oooo        ====             ====       ====                                  ooo        ',
        '  P        ====                C  w S                    ====            ccc       ccc            E ',
        '#########                    ########                           C    k                  ############',
        '#########                    ########                         #########                 ############',
        '#########                    ########                         #########                 ############',
        '#########                    ########                         #########                 ############',
    )),
    ('SKOGEN', 3, 'Hoppa pa monstren', (
        '                                                                                                              ',
        '                                                                                                              ',
        '                                                                                                              ',
        '                                                                                                              ',
        '                      G                                   G                                                   ',
        '                                                                                                              ',
        '                    =====                               =====                         BB      =====           ',
        '                      T                                   T                           XX        T             ',
        '      ooooo           T                           ooooo   T                           XX BBB    T             ',
        '      =====        =========== w      =====       ccccc=======                =====   XX     =======oooo      ',
        '        T             T       ####      T                 T                     T     XX        T             ',
        '  P     T     w   w   T       ####      T   C   k   w     T   w   w   k       C T     XX  G     T   w     E   ',
        '##################################    ##################################    ##################################',
        '##################################^^^^##################################^^^^##################################',
        '##############################################################################################################',
    )),
    ('ISEN', 4, 'Det ar halt!', (
        '                                                                                                    ',
        '                                                                                                    ',
        '                                                                                                    ',
        '                                                              XX                                    ',
        '                               G                              XX   G                  ooooGo        ',
        '                            =====                             XX  ====                ======        ',
        '                                                              XX                                    ',
        '                                                              XX                                    ',
        '                          IIII                       o        XX                                    ',
        '                          IIII                      BB        XX      IIII                          ',
        '     ooooooo          IIIIIIII                                XX   f  IIII                          ',
        '  P                   IIIIIIII      C   w    k            C   XX      IIII          S   k       E   ',
        'IIIIIIIIIIIIII    IIIIIIIIIIII    IIIIIIIIIIIIIIII      IIIIIIIIIIIIIIIIIIII    IIIIIIIIIIIIIIIIIIII',
        'IIIIIIIIIIIIII^^^^IIIIIIIIIIII^^^^IIIIIIIIIIIIIIII^^^^^^IIIIIIIIIIIIIIIIIIII^^^^IIIIIIIIIIIIIIIIIIII',
        'IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII',
    )),
    ('VULKANEN', 5, 'Akta lavan!', (
        '                                                                                                    ',
        '                                                                                                    ',
        '                                                          G                                         ',
        '                                                       =====                                        ',
        '                                                                                    XX              ',
        '                                         G                                          XX              ',
        '                                                               foooooooooooo        XX              ',
        '                                        cc                                          XX  G           ',
        '               oo          oooooo                                    cc             XX BBB          ',
        '               cc                   cc      cc            BBB   BBB      BBB        XX              ',
        '  P       BBB      BBB    C   k                   C  w S                        C   XX       k   E  ',
        '########                ##########              ########                      ########    ##########',
        '########                ##########              ########                      ########    ##########',
        '########LLLLLLLLLLLLLLLL##########LLLLLLLLLLLLLL########LLLLLLLLLLLLLLLLLLLLLL########LLLL##########',
        '########LLLLLLLLLLLLLLLL##########LLLLLLLLLLLLLL########LLLLLLLLLLLLLLLLLLLLLL########LLLL##########',
    )),
    ('BORGEN', 6, 'Dasha igelkottarna', (
        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        '        BB      XX                                                  BBBBBB      XX                            ',
        '        BB      XX                                                  BBBBBB      XX                            ',
        '        BB      XX                                                  BBBBBB      XX                            ',
        '        BB      XX                   G                              BBBBBB      XX                            ',
        '        BB      XX               f BBBB      f                      BBBBBB      XX        f                   ',
        '        BB      XX                         o   o   o                BBBBBB      XX       o     o    G         ',
        '        BB      XX                                                  BBBBBB      XX    o     o     BBBB        ',
        '                XX  oooooo    BBBB         B   B   B    oooooooooo  ^^^^^^      XX       c     c              ',
        '                XX                                                              XX    c     c                 ',
        '  P          k  XX          C                         C   k   w  k     G     C  XX                      k  E  ',
        'BBBBBBBBBBBBBBBBBBBBB^^^^BBBBBBBBBBBBBBB^^^^^^^^^^^^BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB^^^^^^^^^^^^BBBBBBBBBBBBBB',
        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
    )),
    ('TOPPEN', 7, 'Allt pa en gang!', (
        '                                                                                                                        ',
        '                                                                                                                        ',
        '                                                    XX                                                                  ',
        '         oooo                                       XX             G                                    XX              ',
        '        ======                                      XX          ======                                  XX              ',
        '                      f                             XX                           f                      XX              ',
        '                ccc                    G            XX                  oofoooooooooo                   XX    G         ',
        '                                                    XX                                                  XX  BBBB        ',
        '                     ===                            XX                       ===                        XX              ',
        '                                       B            XX   cccc                                           XX              ',
        '                            C  k    B     B     C   XX w          S  k  ===       ===   C   w k         XX      w   E   ',
        '  P     S                 IIIIIIII            ##########      ########                ##########    ####################',
        '##########                IIIIIIII            ##########      ########                ##########    ####################',
        '##########                IIIIIIIILLLLLLLLLLLL##########^^^^^^########LLLLLLLLLLLLLLLL##########^^^^####################',
        '##########                IIIIIIIILLLLLLLLLLLL########################LLLLLLLLLLLLLLLL##################################',
    )),
)

TS = 16
PW, PH = 10, 14
AV_PAL = (   # himmel uppe, himmel nere, mark, mörk mark, gräs/topp, kullar, planka
    ((90, 160, 255), (200, 230, 255), (150, 95, 50), (105, 62, 32), (90, 200, 70), (120, 190, 130), (170, 120, 70)),
    ((16, 12, 26), (46, 34, 62), (92, 80, 104), (58, 48, 70), (140, 128, 160), (34, 26, 46), (150, 120, 90)),
    ((110, 165, 255), (250, 205, 225), (236, 236, 250), (190, 190, 216), (255, 255, 255), (255, 232, 244), (255, 255, 255)),
    ((40, 90, 60), (150, 200, 120), (110, 75, 40), (78, 50, 26), (70, 170, 60), (40, 110, 60), (60, 150, 60)),
    ((150, 200, 255), (232, 245, 255), (200, 222, 242), (150, 172, 202), (250, 255, 255), (184, 212, 240), (170, 120, 70)),
    ((60, 10, 12), (170, 64, 22), (84, 52, 50), (52, 30, 30), (130, 74, 60), (96, 30, 22), (110, 110, 120)),
    ((26, 26, 56), (92, 82, 124), (120, 120, 140), (80, 80, 100), (160, 160, 182), (50, 50, 82), (150, 120, 90)),
    ((10, 10, 40), (84, 40, 124), (100, 80, 140), (70, 50, 100), (200, 150, 255), (40, 30, 82), (200, 150, 255)),
)
# Vilka tecken som är fasta block
AV_SOLID = bytearray(128)
for _c in "#BXcI":
    AV_SOLID[ord(_c)] = 1
AV_TOP = bytearray(AV_SOLID)        # går att stå på
AV_TOP[ord("=")] = 1
AV_TOP[ord("S")] = 1
C_SP, C_X, C_CR, C_PL, C_ICE, C_SPK, C_LAVA, C_SPR = 32, 88, 99, 61, 73, 94, 76, 83
C_COIN, C_GEM, C_CHK, C_EXIT = 111, 71, 67, 69
STONE = (rgb(132, 132, 148), rgb(176, 176, 192), rgb(84, 84, 100))
CRACK = (rgb(156, 104, 62), rgb(96, 60, 32))
CRUMB = (rgb(226, 196, 136), rgb(170, 140, 90))
ICE = (rgb(190, 226, 255), rgb(240, 250, 255), rgb(140, 180, 220))
LAVA = (rgb(255, 110, 20), rgb(255, 220, 60))
SPIKE = rgb(220, 220, 236)
GEMC = rgb(60, 255, 210)
TRUNK = rgb(96, 62, 30)


def gem(fb, x, y, r, c):
    tri(fb, x - r, y, x + r, y, x, y - r, c)
    tri(fb, x - r, y, x + r, y, x, y + r + r // 2, c)
    fb.line(x - r // 2, y - r // 2, x, y - r + 1, WHITE)


class AvLevel:
    def __init__(self, n):
        name, pal, hint, rows = AV_LEVELS[n]
        self.name, self.hint = name, hint
        self.w = len(rows[0])
        self.g = [bytearray(r.encode()) for r in rows]
        self.enemies = []
        self.coins = 0
        for ty in range(len(rows)):
            row = self.g[ty]
            for tx in range(self.w):
                ch = row[tx]
                if ch == 80:                        # P
                    self.start = (tx * TS + 3, ty * TS + 2)
                    row[tx] = C_SP
                elif ch in (119, 107):              # w, k
                    self.enemies.append([tx * TS + 1.0, ty * TS + 4.0, -0.8 if ch == 119 else -0.6, ch, True, 0, 0])
                    row[tx] = C_SP
                elif ch == 102:                     # f
                    self.enemies.append([tx * TS + 1.0, ty * TS + 2.0, 0, ch, True, tx * TS, ty * TS])
                    row[tx] = C_SP
                elif ch == C_COIN:
                    self.coins += 1
        p = AV_PAL[pal]
        self.pal = pal
        self.bg = [mix(p[0], p[1], y / (H - 1)) for y in range(H)]
        self.dirt, self.dark, self.top = rgb(*p[2]), rgb(*p[3]), rgb(*p[4])
        self.hill, self.plank = rgb(*p[5]), rgb(*p[6])
        self.cache = av_cache(self)
        self.hills = bytearray(64)
        for i in range(64):
            a = i * 6.2832 / 64
            self.hills[i] = 50 + int(22 * math.sin(a * 2 + pal) + 14 * math.sin(a * 5 + 1))

    def at(self, tx, ty):
        if tx < 0 or tx >= self.w:
            return 66
        if ty < 0 or ty >= 15:
            return C_SP
        return self.g[ty][tx]


KEY = rgb(255, 0, 255)                  # genomskinlig färg i förritade brickor


def av_cache(lv):
    """Förritar brickorna (16x16) en gång per bana, så blir det en blit per bricka."""
    out = []
    for i in range(13):
        buf = bytearray(TS * TS * 2)
        f = framebuf.FrameBuffer(buf, TS, TS, framebuf.RGB565)
        f.fill(KEY)
        if i <= 2:                                          # mark: topp, mitt, mitt 2
            f.fill(lv.dirt)
            if i == 0:
                f.fill_rect(0, 0, TS, 4, lv.top)
                f.fill_rect(0, 4, TS, 1, lv.dark)
            if i != 2:
                f.fill_rect(5, 8, 2, 2, lv.dark)
            f.fill_rect(11, 12, 2, 2, lv.dark)
        elif i <= 4:                                        # sten (två mönster)
            f.fill(STONE[0])
            f.hline(0, 0, TS, STONE[1])
            f.vline(0, 0, TS, STONE[1])
            f.hline(0, 15, TS, STONE[2])
            f.vline(15, 0, TS, STONE[2])
            f.hline(1, 8, 14, STONE[2])
            f.vline(4 if i == 3 else 11, 1, 7, STONE[2])
        elif i == 5:                                        # spricka
            f.fill(CRACK[0])
            f.rect(0, 0, TS, TS, CRACK[1])
            f.line(3, 3, 8, 9, CRACK[1])
            f.line(8, 9, 12, 5, CRACK[1])
            f.line(8, 9, 7, 14, CRACK[1])
        elif i == 6:                                        # smular
            f.fill_rect(0, 0, TS, 9, CRUMB[0])
            f.hline(0, 8, TS, CRUMB[1])
            f.fill_rect(3, 3, 2, 2, CRUMB[1])
            f.fill_rect(10, 5, 2, 2, CRUMB[1])
        elif i == 7:                                        # planka / moln
            if lv.pal == 2:
                f.ellipse(8, 4, 9, 5, WHITE, True)
            else:
                f.fill_rect(0, 0, TS, 5, lv.plank)
                f.hline(0, 5, TS, lv.dark)
        elif i <= 9:                                        # is: topp, mitt
            f.fill(ICE[0])
            if i == 8:
                f.fill_rect(0, 0, TS, 3, ICE[1])
            f.line(3, 12, 9, 6, ICE[2])
        elif i == 10:                                       # spikar
            for k in range(3):
                tri(f, k * 5, 15, k * 5 + 5, 15, k * 5 + 2, 6, SPIKE)
        elif i == 11:                                       # lava
            f.fill(LAVA[0])
        else:                                               # trädstam
            f.fill_rect(5, 0, 6, TS, TRUNK)
        out.append(f)
    return out


@native
def av_tiles(lcd, lv, cam, t, crum, flags):
    c0 = cam // TS
    g = lv.g
    w = lv.w
    cc = lv.cache
    for ty in range(15):
        row = g[ty]
        up = g[ty - 1] if ty else None
        y = ty * TS
        for tx in range(c0, c0 + 21):
            if tx >= w:
                break
            ch = row[tx]
            if ch == 32:
                continue
            x = tx * TS - cam
            if ch == 35:                                    # mark
                if ty == 0 or not AV_SOLID[up[tx]]:
                    lcd.blit(cc[0], x, y)
                else:
                    lcd.blit(cc[1 if (tx * 7 + ty * 3) % 4 == 0 else 2], x, y)
            elif ch == 66:                                  # sten
                lcd.blit(cc[3 + ty % 2], x, y)
            elif ch == 88:                                  # spricka
                lcd.blit(cc[5], x, y)
            elif ch == 99:                                  # smular
                k = crum.get(tx + ty * 1000, 0)
                lcd.blit(cc[6], x + ((t % 3) - 1 if k else 0), y, KEY)
            elif ch == 61:                                  # planka / moln
                lcd.blit(cc[7], x, y, KEY)
            elif ch == 73:                                  # is
                lcd.blit(cc[8 if ty == 0 or not AV_SOLID[up[tx]] else 9], x, y)
            elif ch == 94:                                  # spikar
                lcd.blit(cc[10], x, y, KEY)
            elif ch == 76:                                  # lava
                lcd.blit(cc[11], x, y)
                if ty == 0 or up[tx] != 76:
                    lcd.fill_rect(x + ((t // 3 + tx * 5) % 12), y, 5, 2, LAVA[1])
            elif ch == 84:                                  # trädstam
                lcd.blit(cc[12], x, y, KEY)
            elif ch == 83:                                  # fjäder
                lcd.fill_rect(x + 2, y + 13, 12, 3, STONE[2])
                lcd.line(x + 4, y + 13, x + 12, y + 10, GRAY)
                lcd.line(x + 12, y + 10, x + 4, y + 7, GRAY)
                lcd.fill_rect(x + 1, y + 4, 14, 3, CORAL)
            elif ch == 111:                                 # mynt
                r = int(5 * abs(math.sin(t * 0.12 + tx)))
                lcd.ellipse(x + 8, y + 8, r + 1, 6, YELLOW, True)
                if r > 2:
                    lcd.ellipse(x + 8, y + 8, r - 2, 3, AMBER, True)
            elif ch == 71:                                  # ädelsten
                gem(lcd, x + 8, y + 7 + int(2 * math.sin(t * 0.15)), 6, GEMC)
            elif ch == 67:                                  # flagga
                lcd.vline(x + 3, y - 6, 22, GRAY)
                c = LIME if (tx + ty * 1000) in flags else CORAL
                wv = 1 if (t // 6) % 2 else 0
                tri(lcd, x + 4, y - 6, x + 4, y + 3, x + 13, y - 2 + wv, c)
            elif ch == 69:                                  # dörr
                lcd.fill_rect(x, y - 12, TS, 28, rgb(120, 70, 30))
                lcd.ellipse(x + 8, y - 12, 8, 6, rgb(120, 70, 30), True)
                lcd.fill_rect(x + 3, y - 10, 10, 26, rgb(60, 30, 10))
                lcd.fill_rect(x + 10, y + 4, 2, 2, YELLOW)
                if (t // 8) % 2:
                    lcd.pixel(x + 8 + (t % 7) - 3, y - 18, YELLOW)


def av_enemy(lcd, e, cam, t):
    x, y = int(e[0]) - cam, int(e[1])
    if x < -20 or x > W + 4:
        return
    k = e[3]
    if k == 119:                                            # vandrare (svamp)
        lcd.ellipse(x + 7, y + 5, 8, 5, CORAL, True)
        lcd.fill_rect(x + 3, y + 1, 3, 2, WHITE)
        lcd.fill_rect(x + 3, y + 6, 8, 5, rgb(250, 220, 180))
        lcd.fill_rect(x + 4, y + 7, 2, 2, BLACK)
        lcd.fill_rect(x + 9, y + 7, 2, 2, BLACK)
        s = (t // 5) % 2
        lcd.fill_rect(x + 2 + s, y + 11, 4, 2, rgb(80, 50, 30))
        lcd.fill_rect(x + 9 - s, y + 11, 4, 2, rgb(80, 50, 30))
    elif k == 107:                                          # igelkott
        for i in range(4):
            tri(lcd, x + i * 3, y + 5, x + i * 3 + 5, y + 5, x + i * 3 + 2, y - 1 - (i % 2) * 2, rgb(200, 200, 220))
        lcd.ellipse(x + 7, y + 7, 7, 5, VIOLET, True)
        ex = x + (3 if e[2] < 0 else 10)
        lcd.fill_rect(ex, y + 6, 2, 2, WHITE)
        lcd.fill_rect(x + 3, y + 11, 3, 2, BLACK)
        lcd.fill_rect(x + 9, y + 11, 3, 2, BLACK)
    else:                                                   # fladdermus
        fl = 4 if (t // 4) % 2 else -3
        tri(lcd, x + 6, y + 6, x - 4, y + 2 + fl, x + 2, y + 9, rgb(70, 40, 110))
        tri(lcd, x + 8, y + 6, x + 18, y + 2 + fl, x + 12, y + 9, rgb(70, 40, 110))
        lcd.ellipse(x + 7, y + 7, 5, 5, rgb(110, 60, 160), True)
        lcd.fill_rect(x + 4, y + 5, 2, 2, YELLOW)
        lcd.fill_rect(x + 9, y + 5, 2, 2, YELLOW)


def av_time(f):
    s = f // 30
    return "%d:%02d" % (s // 60, s % 60)


def play(lcd, keys):
    n = len(AV_LEVELS)
    best = SCORES.get("av_time", [0] * n)
    gems = SCORES.get("av_gem", [0] * n)
    best = (best + [0] * n)[:n]
    gems = (gems + [0] * n)[:n]
    sel = 0
    while sel < n - 1 and best[sel]:
        sel += 1
    while True:
        sel = av_select(lcd, keys, best, gems, sel)
        if sel is None:
            return None
        res = av_run(lcd, keys, sel)
        if res:
            frames, gotgems = res
            if not best[sel] or frames < best[sel]:
                best[sel] = frames
            gems[sel] |= gotgems
            SCORES["av_time"] = best
            SCORES["av_gem"] = gems
            save_scores()
            if sel >= 1:
                goal("aventyr", 0)
            if gotgems == 7:
                goal("aventyr", 1)
            if all(best):
                goal("aventyr", 2)
            if sel < n - 1:
                sel += 1


def av_select(lcd, keys, best, gems, sel):
    n = len(AV_LEVELS)
    stars = Stars(30)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        unlocked = 0
        while unlocked < n and best[unlocked]:
            unlocked += 1
        if keys.repeat(K0, 10, 4):
            sel = (sel - 1) % n
        if keys.repeat(K1, 10, 4):
            sel = (sel + 1) % n
        if keys.pressed(K2) and sel <= unlocked:
            keys.wait_release()
            return sel
        if keys.pressed(K3):
            return None
        gradient(lcd, theme_bg())
        stars.draw(lcd)
        big(lcd, "AVENTYR", 12, 10, SHADOW, 3)
        big(lcd, "AVENTYR", 10, 8, LIME, 3)
        rtext(lcd, "0/1 valj", W - 8, 10, GRAY)
        rtext(lcd, "2 spela 3 ut", W - 8, 22, GRAY)
        for i in range(n):
            x = 8 + (i % 4) * 78
            y = 42 + (i // 4) * 84
            p = AV_PAL[AV_LEVELS[i][1]]
            open_ = i <= unlocked
            if i == sel:
                lcd.fill_rect(x - 3, y - 3, 76, 80, WHITE)
            for yy in range(0, 74, 4):
                lcd.fill_rect(x, y + yy, 70, 4, mix(p[0], p[1], yy / 74) if open_ else LINE)
            if open_:
                lcd.fill_rect(x, y + 56, 70, 18, rgb(*p[2]))
                lcd.fill_rect(x, y + 56, 70, 3, rgb(*p[4]))
            ctext(lcd, str(i + 1), y + 6, BG if open_ else DIM, 3, x + 35)
            ctext(lcd, AV_LEVELS[i][0], y + 34, WHITE if open_ else DIM, 1, x + 35)
            for k in range(3):
                c = GEMC if gems[i] & (1 << k) else (SHADOW if open_ else LINE)
                gem(lcd, x + 21 + k * 14, y + 64, 4, c)
        lcd.fill_rect(8, 214, 304, 22, PANEL)
        if sel > unlocked:
            ctext(lcd, "Klara banan innan forst", 221, AMBER)
        elif best[sel]:
            ctext(lcd, "%s   Basta tid %s" % (AV_LEVELS[sel][0], av_time(best[sel])), 221, WHITE)
        else:
            ctext(lcd, "%s   Ny bana!" % AV_LEVELS[sel][0], 221, WHITE)
        lcd.show()
        t += 1
        wait(t0)


class NoFx:
    """Tomma effekter (används när spelet räknas utan skärm, t.ex. i tester)."""
    def burst(self, *a):
        pass

    def add(self, *a):
        pass

    def hit(self, *a):
        pass


class Av:
    """Allt som händer i en bana, utan att rita något."""
    def __init__(self, lv, fx=None):
        self.lv = lv
        self.px, self.py = float(lv.start[0]), float(lv.start[1])
        self.spawn = (self.px, self.py)
        self.vx = self.vy = 0.0
        self.face = self.ddir = 1
        self.ground = False
        self.spring_up = False
        self.can_dash = True
        self.gtile = self.coy = self.jbuf = self.dash = 0
        self.coins = self.gotgems = self.deaths = self.dead = self.frames = self.t = 0
        self.won = False
        self.crum = {}          # smulande block: nyckel -> nedräkning
        self.gone = {}          # smulade block som kommer tillbaka
        self.flags = set()
        self.trail = []
        self.parts = self.pops = self.shake = fx or NoFx()
        self.gempos = []
        for ty in range(15):
            for tx in range(lv.w):
                if lv.g[ty][tx] == C_GEM:
                    self.gempos.append(tx + ty * 1000)

    def step(self, L, R, J, Jp, D):
        """En bildruta. L/R/J = knappar nere, Jp/D = nyss tryckta (hopp, dash)."""
        lv = self.lv
        parts, pops, shake = self.parts, self.pops, self.shake
        self.t += 1
        t = self.t
        if self.dead:
            self.dead -= 1
            if self.dead == 0:
                self.px, self.py = self.spawn
                self.vx = self.vy = 0.0
                self.dash = 0
            self.crumble()
            return
        self.frames += 1
        px, py, vx, vy = self.px, self.py, self.vx, self.vy
        ground = self.ground
        if Jp:
            self.jbuf = 6
        if D and self.can_dash and not self.dash:
            self.dash = 9
            self.ddir = -1 if L and not R else 1 if R and not L else self.face
            self.can_dash = False
            shake.hit(2)
        ice = ground and self.gtile == C_ICE
        if self.dash:
            vx = 6.6 * self.ddir
            vy = 0.0
            self.dash -= 1
            self.trail.append((int(px), int(py)))
            if self.dash == 0:
                vx = 3.0 * self.ddir
        else:
            acc = 0.16 if ice else 0.7 if ground else 0.45
            top = 3.6 if ice else 3.1
            if L and not R:
                vx -= acc
                self.face = -1
            elif R and not L:
                vx += acc
                self.face = 1
            else:
                vx *= 0.97 if ice else 0.6 if ground else 0.9
            if vx > top:
                vx = top
            if vx < -top:
                vx = -top
            vy += 0.55
            if vy > 7.5:
                vy = 7.5
            if not J and vy < -3.0 and not self.spring_up:
                vy = -3.0
        if len(self.trail) > 5 or (self.trail and not self.dash):
            self.trail.pop(0)
        self.coy = 6 if ground else self.coy - 1
        if self.jbuf:
            self.jbuf -= 1
            if self.coy > 0:
                vy = -7.4
                self.jbuf = self.coy = 0
                ground = False
                self.spring_up = False
                parts.burst(px + 5, py + PH, WHITE, 5, 1.5, 8)
        # --- flytta i x ---
        nx = px + vx
        if vx:
            tx = int(nx + PW - 1) // TS if vx > 0 else int(nx) // TS
            for ty in range(int(py) // TS, int(py + PH - 1) // TS + 1):
                c = lv.at(tx, ty)
                if c == C_X and self.dash:
                    lv.g[ty][tx] = C_SP
                    parts.burst(tx * TS + 8, ty * TS + 8, CRACK[0], 14, 3, 18, 0.2)
                    shake.hit(4)
                elif AV_SOLID[c]:
                    nx = tx * TS - PW if vx > 0 else (tx + 1) * TS
                    vx = 0.0
                    self.dash = 0
        px = nx
        # --- flytta i y ---
        ny = py + vy
        was_ground = ground
        ground = False
        tx0, tx1 = int(px) // TS, int(px + PW - 1) // TS
        if vy >= 0:
            ty = int(ny + PH) // TS             # rutan precis under fötterna
            for tx in range(tx0, tx1 + 1):
                c = lv.at(tx, ty)
                if AV_SOLID[c] or (AV_TOP[c] and py + PH <= ty * TS + 0.5):
                    ny = ty * TS - PH
                    self.gtile = c
                    if c == C_SPR:
                        vy = -11.6
                        self.spring_up = True
                        parts.burst(px + 5, ny + PH, CORAL, 8, 2, 10)
                    else:
                        vy = 0.0
                        ground = True
                        self.spring_up = False
                        self.can_dash = True
                        if not was_ground:
                            parts.burst(px + 5, ny + PH, WHITE, 4, 1.2, 6)
                    if c == C_CR and (tx + ty * 1000) not in self.crum:
                        self.crum[tx + ty * 1000] = 22
                    break
        else:
            ty = int(ny) // TS
            for tx in range(tx0, tx1 + 1):
                c = lv.at(tx, ty)
                if AV_SOLID[c]:
                    if c == C_X:
                        lv.g[ty][tx] = C_SP
                        parts.burst(tx * TS + 8, ty * TS + 8, CRACK[0], 12, 3, 16, 0.2)
                    ny = (ty + 1) * TS
                    vy = 0.0
                    break
        py = ny
        self.px, self.py, self.vx, self.vy, self.ground = px, py, vx, vy, ground
        # --- saker och faror ---
        hurt = py > H + 8
        for ty in range(int(py + 3) // TS, int(py + PH - 1) // TS + 1):
            for tx in range(int(px + 1) // TS, int(px + PW - 2) // TS + 1):
                c = lv.at(tx, ty)
                k = tx + ty * 1000
                if c == C_COIN:
                    lv.g[ty][tx] = C_SP
                    self.coins += 1
                    parts.burst(tx * TS + 8, ty * TS + 8, YELLOW, 6, 1.6, 10)
                elif c == C_GEM:
                    lv.g[ty][tx] = C_SP
                    if k in self.gempos:
                        self.gotgems |= 1 << self.gempos.index(k)
                    parts.burst(tx * TS + 8, ty * TS + 8, GEMC, 18, 2.5, 20)
                    pops.add(tx * TS + 8, ty * TS - 4, "STEN!", GEMC)
                elif c == C_CHK and k not in self.flags:
                    self.flags.add(k)
                    self.spawn = (float(tx * TS + 3), float(ty * TS + 2))
                    pops.add(tx * TS + 8, ty * TS - 10, "SPARAT", LIME)
                elif c == C_EXIT:
                    self.won = True
                elif c == C_SPK or c == C_LAVA:
                    hurt = True
        # --- monster ---
        for e in lv.enemies:
            if not e[4]:
                continue
            if e[3] == 102:
                e[0] = e[5] + 40 * math.sin(t * 0.025 + e[5])
                e[1] = e[6] + 12 * math.sin(t * 0.08 + e[5])
            elif abs(e[0] - px) < 400:
                nx = e[0] + e[2]
                ax = int(nx if e[2] < 0 else nx + 13) // TS
                if AV_SOLID[lv.at(ax, int(e[1] + 6) // TS)] or not AV_TOP[lv.at(ax, int(e[1] + 13) // TS)]:
                    e[2] = -e[2]
                else:
                    e[0] = nx
            if px + PW > e[0] + 1 and px < e[0] + 13 and py + PH > e[1] + 1 and py < e[1] + 12:
                if self.dash or (e[3] != 107 and self.vy > 0 and py + PH - e[1] < 10):
                    e[4] = False
                    parts.burst(e[0] + 7, e[1] + 6, CORAL if e[3] == 119 else VIOLET, 14, 2.5, 16)
                    pops.add(e[0] + 7, e[1] - 6, "POFF!", WHITE)
                    if not self.dash:
                        self.vy = -9.0 if J else -6.5
                        self.spring_up = J
                    self.can_dash = True
                    shake.hit(3)
                else:
                    hurt = True
        if hurt and not self.won:
            self.dead = 26
            self.deaths += 1
            shake.hit(6)
            parts.burst(px + 5, min(py, H - 10) + 7, rgb(255, 90, 90), 24, 3.5, 24, 0.15)
        self.crumble()

    def crumble(self):
        lv = self.lv
        for k in list(self.crum.keys()):
            self.crum[k] -= 1
            if self.crum[k] <= 0:
                del self.crum[k]
                lv.g[k // 1000][k % 1000] = C_SP
                self.gone[k] = 150
                self.parts.burst((k % 1000) * TS + 8, (k // 1000) * TS + 4, CRUMB[0], 8, 1.5, 12, 0.3)
        for k in list(self.gone.keys()):
            self.gone[k] -= 1
            if self.gone[k] <= 0:
                kx, ky = (k % 1000) * TS, (k // 1000) * TS
                if self.px + PW > kx and self.px < kx + TS and self.py + PH > ky and self.py < ky + TS:
                    self.gone[k] = 10
                else:
                    del self.gone[k]
                    lv.g[k // 1000][k % 1000] = C_CR


class AvFx:
    def __init__(self):
        self.p = Particles(70)
        self.q = Popups()
        self.s = Shake()

    def burst(self, *a):
        self.p.burst(*a)

    def add(self, *a):
        self.q.add(*a)

    def hit(self, a):
        self.s.hit(a)


def av_run(lcd, keys, n):
    lv = AvLevel(n)
    gc.collect()
    fx = AvFx()
    a = Av(lv, fx)
    cam = 0.0
    t = 0
    keys.wait_release()
    # Bannamn
    for f in range(40):
        t0 = time.ticks_ms()
        keys.update()
        gradient(lcd, lv.bg)
        av_tiles(lcd, lv, 0, t, a.crum, a.flags)
        lcd.fill_rect(0, 76, W, 74, BG)
        stext(lcd, "BANA %d: %s" % (n + 1, lv.name), 88, LIME, 2)
        ctext(lcd, lv.hint, 120, WHITE)
        lcd.show()
        t += 1
        if f > 8 and any(keys.now):
            break
        wait(t0)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            if pause(lcd, keys):
                return None
        now, prev = keys.now, keys.prev
        L, R = now[K0], now[K1]
        a.step(L, R, now[K2], now[K2] and not prev[K2], now[K3] and not prev[K3])
        if a.won:
            return av_win(lcd, lv, cam, t, a, n)
        # kamera
        cam += (a.px - 140 - cam) * 0.25
        mx = lv.w * TS - W
        if cam < 0:
            cam = 0.0
        if cam > mx:
            cam = float(mx)
        ox, oy = fx.s.offset()
        c = int(cam) - ox
        # --- rita ---
        gradient(lcd, lv.bg)
        hs = lv.hills
        sc = c // 3
        for i in range(0, W, 8):
            h = hs[((i + sc) // 8) % 64]
            lcd.fill_rect(i, H - h, 8, h, lv.hill)
        av_tiles(lcd, lv, c, t, a.crum, a.flags)
        for e in lv.enemies:
            if e[4]:
                av_enemy(lcd, e, c, t)
        for i, (tx_, ty_) in enumerate(a.trail):
            hero(lcd, tx_ + 5 - c, ty_ + 7, a.ddir, t, SKY if i % 2 else VIOLET)
        if not a.dead:
            hx, hy = int(a.px) + 5 - c, int(a.py) + 7
            if a.dash:
                hero(lcd, hx, hy, a.ddir, t, SKY)
            else:
                hero(lcd, hx, hy, a.face, t if (L or R) and a.ground else 0)
        fx.p.draw(lcd, -c, 0)
        fx.q.draw(lcd, -c, 0)
        lcd.fill_rect(0, 0, W, 14, BG)
        lcd.text("%d %s" % (n + 1, lv.name), 4, 3, LIME)
        lcd.ellipse(124, 6, 4, 5, YELLOW, True)
        lcd.text("%d/%d" % (a.coins, lv.coins), 132, 3, WHITE)
        for k in range(3):
            gem(lcd, 210 + k * 12, 7, 4, GEMC if a.gotgems & (1 << k) else DIM)
        rtext(lcd, av_time(a.frames), W - 4, 3, WHITE)
        lcd.show()
        t += 1
        wait(t0)


def av_win(lcd, lv, cam, t, a, n):
    c = int(cam)
    frames, coins, gotgems, deaths, crum, flags = a.frames, a.coins, a.gotgems, a.deaths, a.crum, a.flags
    for f in range(75):
        t0 = time.ticks_ms()
        gradient(lcd, lv.bg)
        av_tiles(lcd, lv, c, t + f, crum, flags)
        for _ in range(8):
            lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3), 3, 3, random.choice(CONFETTI))
        lcd.fill_rect(40, 50, 240, 140, PANEL)
        lcd.rect(40, 50, 240, 140, LIME)
        stext(lcd, "BANAN KLAR!", 62, LIME, 2)
        ctext(lcd, "Tid: " + av_time(frames), 96, WHITE, 2)
        ctext(lcd, "Mynt: %d/%d" % (coins, lv.coins), 124, YELLOW)
        for k in range(3):
            gem(lcd, 136 + k * 24, 150, 7, GEMC if gotgems & (1 << k) else DIM)
        ctext(lcd, "Missar: %d" % deaths, 172, GRAY)
        lcd.show()
        wait(t0)
    return frames, gotgems
