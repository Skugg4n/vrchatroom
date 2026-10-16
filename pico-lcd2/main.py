# Pico Pong
# Raspberry Pi Pico 2 + Waveshare Pico-LCD-2 (ST7789, 320x240)
#
# Spara som main.py på Picon i Thonny så startar den automatiskt.
# OBS: Skärmens inbyggda typsnitt saknar å, ä och ö, därför skrivs
# texten på skärmen utan dem.

from machine import Pin, SPI, PWM
import framebuf
import time
import random
import math

W, H = 320, 240

# ---------------------------------------------------------------
# Knappar. Byt plats på siffrorna om knapparna känns "fel" i
# förhållande till var de sitter på kortet (kolla med KNAPPTEST).
#   KEY0 = GP15, KEY1 = GP17, KEY2 = GP2, KEY3 = GP3
# ---------------------------------------------------------------
KEY_PINS = (15, 17, 2, 3)
KEY_NAMES = ("KEY0", "KEY1", "KEY2", "KEY3")
K_A = 0   # välj / spelare 1 upp
K_B = 1   # tillbaka / paus / spelare 1 ner
K_X = 2   # menyn upp / spelare 2 upp (i 1-spelarläge: din paddel upp)
K_Y = 3   # menyn ner / spelare 2 ner (i 1-spelarläge: din paddel ner)

WIN_SCORE = 7
FRAME_MS = 33          # ca 30 bilder per sekund


def rgb(r, g, b):
    """RGB888 -> RGB565 med bytebyte (skärmen vill ha big endian)."""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


BLACK = rgb(0, 0, 0)
WHITE = rgb(255, 255, 255)
BG = rgb(6, 6, 22)
DIM = rgb(50, 50, 90)
GRAY = rgb(140, 140, 170)
CYAN = rgb(0, 230, 255)
MAGENTA = rgb(255, 40, 200)
YELLOW = rgb(255, 220, 40)
SHADOW = rgb(40, 0, 70)


# ---------------------------------------------------------------
# Skärmdrivrutin
# ---------------------------------------------------------------
class LCD(framebuf.FrameBuffer):
    def __init__(self):
        self.buffer = bytearray(W * H * 2)
        super().__init__(self.buffer, W, H, framebuf.RGB565)
        self.cs = Pin(9, Pin.OUT, value=1)
        self.rst = Pin(12, Pin.OUT, value=1)
        self.dc = Pin(8, Pin.OUT, value=1)
        self.spi = SPI(1, baudrate=62_500_000, polarity=0, phase=0,
                       sck=Pin(10), mosi=Pin(11), miso=None)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.backlight(100)
        self._init_display()

    def backlight(self, percent):
        percent = max(0, min(100, percent))
        self.bl.duty_u16(int(percent * 655.35))

    def cmd(self, c, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([c]))
        if data:
            self.dc(1)
            self.spi.write(bytearray(data))
        self.cs(1)

    def _init_display(self):
        self.rst(1)
        time.sleep_ms(5)
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(120)
        self.cmd(0x36, [0x70])                      # liggande läge
        self.cmd(0x3A, [0x05])                      # 16 bitar/pixel
        self.cmd(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33])
        self.cmd(0xB7, [0x35])
        self.cmd(0xBB, [0x19])
        self.cmd(0xC0, [0x2C])
        self.cmd(0xC2, [0x01])
        self.cmd(0xC3, [0x12])
        self.cmd(0xC4, [0x20])
        self.cmd(0xC6, [0x0F])
        self.cmd(0xD0, [0xA4, 0xA1])
        self.cmd(0xE0, [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F,
                        0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23])
        self.cmd(0xE1, [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F,
                        0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23])
        self.cmd(0x21)                              # inverterade färger (krävs)
        self.cmd(0x11)                              # vakna
        time.sleep_ms(120)
        self.cmd(0x29)                              # skärm på

    def show(self):
        self.cmd(0x2A, [0x00, 0x00, (W - 1) >> 8, (W - 1) & 0xFF])
        self.cmd(0x2B, [0x00, 0x00, (H - 1) >> 8, (H - 1) & 0xFF])
        self.cmd(0x2C)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)


# ---------------------------------------------------------------
# Knappar med "nyss nedtryckt"-detektering
# ---------------------------------------------------------------
class Keys:
    def __init__(self):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p in KEY_PINS]
        self.now = [False] * 4
        self.prev = [False] * 4

    def update(self):
        self.prev = self.now
        self.now = [p.value() == 0 for p in self.pins]

    def held(self, k):
        return self.now[k]

    def pressed(self, k):
        return self.now[k] and not self.prev[k]

    def any_held(self):
        return any(self.now)

    def wait_release(self):
        self.update()
        while self.any_held():
            time.sleep_ms(10)
            self.update()
        self.update()


# ---------------------------------------------------------------
# Grafikhjälp
# ---------------------------------------------------------------
_glyph = bytearray(8)
_gfb = framebuf.FrameBuffer(_glyph, 8, 8, framebuf.MONO_HLSB)


def big_text(fb, s, x, y, c, scale=2):
    """Skriver text i valfri storlek (det inbyggda typsnittet är 8x8)."""
    if scale == 1:
        fb.text(s, x, y, c)
        return
    for ch in s:
        _gfb.fill(0)
        _gfb.text(ch, 0, 0, 1)
        for row in range(8):
            bits = _glyph[row]
            col = 0
            while bits and col < 8:
                if bits & (0x80 >> col):
                    start = col
                    while col < 8 and bits & (0x80 >> col):
                        col += 1
                    fb.fill_rect(x + start * scale, y + row * scale,
                                 (col - start) * scale, scale, c)
                else:
                    col += 1
        x += 8 * scale


def text_w(s, scale=1):
    return len(s) * 8 * scale


def center_text(fb, s, y, c, scale=1, cx=W // 2):
    big_text(fb, s, cx - text_w(s, scale) // 2, y, c, scale)


def lerp_col(c1, c2, t):
    return rgb(int(c1[0] + (c2[0] - c1[0]) * t),
               int(c1[1] + (c2[1] - c1[1]) * t),
               int(c1[2] + (c2[2] - c1[2]) * t))


GRADIENT = [lerp_col((8, 8, 40), (45, 0, 60), y / (H - 1)) for y in range(H)]
STAR_COLS = (rgb(70, 70, 110), rgb(150, 150, 200), rgb(255, 255, 255))
TITLE_COLS = [lerp_col((0, 230, 255), (255, 40, 200), i / 8) for i in range(9)]


def draw_gradient(fb):
    for y in range(H):
        fb.hline(0, y, W, GRADIENT[y])


def frame_wait(t0):
    used = time.ticks_diff(time.ticks_ms(), t0)
    if used < FRAME_MS:
        time.sleep_ms(FRAME_MS - used)


# ---------------------------------------------------------------
# Startsida
# ---------------------------------------------------------------
MENU_ITEMS = ("1 SPELARE", "2 SPELARE", "KNAPPTEST")


def run_menu(lcd, keys, sel=0):
    stars = [[random.randint(0, W - 1), random.randint(0, H - 1),
              random.randint(1, 3)] for _ in range(50)]
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K_X):
            sel = (sel - 1) % len(MENU_ITEMS)
        if keys.pressed(K_Y):
            sel = (sel + 1) % len(MENU_ITEMS)
        if keys.pressed(K_A):
            return sel

        # Bakgrund + stjärnor i parallax
        draw_gradient(lcd)
        for s in stars:
            s[0] -= s[2]
            if s[0] < 0:
                s[0] = W - 1
                s[1] = random.randint(0, H - 1)
            if s[2] == 3:
                lcd.hline(s[0], s[1], 2, STAR_COLS[2])
            else:
                lcd.pixel(s[0], s[1], STAR_COLS[s[2] - 1])

        # Titel som gungar bokstav för bokstav
        title = "PICO PONG"
        x = (W - text_w(title, 4)) // 2
        for i, ch in enumerate(title):
            dy = int(4 * math.sin(t * 0.15 + i * 0.7))
            big_text(lcd, ch, x + 3, 22 + dy + 3, SHADOW, 4)
            big_text(lcd, ch, x, 22 + dy, TITLE_COLS[i], 4)
            x += 32
        center_text(lcd, "for Raspberry Pi Pico 2", 66, GRAY)

        # Meny
        bx, by, bw, bh = 50, 88, 220, 112
        lcd.fill_rect(bx, by, bw, bh, BG)
        lcd.rect(bx, by, bw, bh, DIM)
        lcd.rect(bx + 2, by + 2, bw - 4, bh - 4, SHADOW)
        pulse = (math.sin(t * 0.2) + 1) / 2
        hi = lerp_col((0, 180, 220), (120, 255, 255), pulse)
        for i, item in enumerate(MENU_ITEMS):
            iy = by + 12 + i * 32
            if i == sel:
                lcd.fill_rect(bx + 10, iy - 4, bw - 20, 24, hi)
                big_text(lcd, ">", bx + 16, iy, BG, 2)
                center_text(lcd, item, iy, BG, 2, cx=W // 2 + 8)
            else:
                center_text(lcd, item, iy, WHITE, 2, cx=W // 2 + 8)

        center_text(lcd, "X/Y: valj    A: starta", 220, GRAY)
        lcd.show()

        t += 1
        frame_wait(t0)


# ---------------------------------------------------------------
# Knapptest: visar vilken knapp som är vilken
# ---------------------------------------------------------------
def key_test(lcd, keys):
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.held(K_A) and keys.held(K_Y):
            return
        lcd.fill(BG)
        center_text(lcd, "KNAPPTEST", 14, YELLOW, 3)
        center_text(lcd, "Tryck pa knapparna", 48, GRAY)
        roles = ("A  valj/P1 upp", "B  paus/P1 ner",
                 "X  upp/P2 upp", "Y  ner/P2 ner")
        for i in range(4):
            y = 70 + i * 34
            on = keys.held(i)
            lcd.fill_rect(20, y, 280, 28, CYAN if on else rgb(20, 20, 50))
            col = BG if on else WHITE
            big_text(lcd, KEY_NAMES[i], 30, y + 6, col, 2)
            lcd.text("GP%d" % KEY_PINS[i], 106, y + 10, col)
            lcd.text(roles[i], 150, y + 10, col)
        center_text(lcd, "A + Y samtidigt: tillbaka", 222, GRAY)
        lcd.show()
        frame_wait(t0)


# ---------------------------------------------------------------
# Pong
# ---------------------------------------------------------------
PW, PH = 6, 44          # paddel
BS = 6                  # boll
P_SPEED = 6
MAX_SPEED = 9.0
TRAIL_COLS = [lerp_col((6, 6, 22), (255, 255, 255), i / 5) for i in range(1, 5)]


def pause_screen(lcd, keys):
    """Returnerar True om man vill tillbaka till menyn."""
    lcd.fill_rect(70, 80, 180, 80, BG)
    lcd.rect(70, 80, 180, 80, YELLOW)
    center_text(lcd, "PAUS", 92, YELLOW, 3)
    center_text(lcd, "A: fortsatt", 126, WHITE)
    center_text(lcd, "B: till menyn", 140, WHITE)
    lcd.show()
    keys.wait_release()
    while True:
        keys.update()
        if keys.pressed(K_A):
            keys.wait_release()
            return False
        if keys.pressed(K_B):
            return True
        time.sleep_ms(20)


def win_screen(lcd, keys, text, s1, s2, col):
    """Returnerar 'again' eller 'menu'."""
    keys.wait_release()
    t = 0
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pressed(K_A):
            return "again"
        if keys.pressed(K_B):
            return "menu"
        draw_gradient(lcd)
        # Konfetti
        for _ in range(40):
            lcd.fill_rect(random.randint(0, W - 3), random.randint(0, H - 3),
                          3, 3, random.choice(TITLE_COLS))
        dy = int(5 * math.sin(t * 0.2))
        center_text(lcd, text, 50 + dy + 3, SHADOW, 3)
        center_text(lcd, text, 50 + dy, col, 3)
        center_text(lcd, "%d - %d" % (s1, s2), 105, WHITE, 5)
        center_text(lcd, "A: spela igen    B: meny", 200, GRAY)
        lcd.show()
        t += 1
        frame_wait(t0)


def play_pong(lcd, keys, two_players):
    lx, rx = 12, W - 12 - PW
    ly = ry = (H - PH) / 2
    s1 = s2 = 0
    bx = by = vx = vy = 0.0
    speed = 4.0
    trail = []
    countdown = 45           # bilder kvar innan bollen serveras
    serve_dir = random.choice((-1, 1))
    cpu_err = 0
    cpu_speed = 3.6

    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()

        # --- Paus ---
        if two_players:
            want_pause = ((keys.held(K_A) and keys.held(K_B)) or
                          (keys.held(K_X) and keys.held(K_Y)))
        else:
            want_pause = keys.pressed(K_B)
        if want_pause:
            if pause_screen(lcd, keys):
                return "menu"

        # --- Paddlar ---
        if two_players:
            if keys.held(K_A):
                ly -= P_SPEED
            if keys.held(K_B):
                ly += P_SPEED
            if keys.held(K_X):
                ry -= P_SPEED
            if keys.held(K_Y):
                ry += P_SPEED
        else:
            if keys.held(K_X):
                ly -= P_SPEED
            if keys.held(K_Y):
                ly += P_SPEED
            # Datorn följer bollen när den är på väg mot den
            if vx > 0:
                target = by + BS / 2 - PH / 2 + cpu_err
            else:
                target = (H - PH) / 2
            diff = target - ry
            ry += max(-cpu_speed, min(cpu_speed, diff))
        ly = max(0, min(H - PH, ly))
        ry = max(0, min(H - PH, ry))

        # --- Boll ---
        if countdown > 0:
            countdown -= 1
            bx, by = W / 2 - BS / 2, H / 2 - BS / 2
            trail = []
            if countdown == 0:
                speed = 4.0
                ang = random.uniform(-0.5, 0.5)
                vx = speed * math.cos(ang) * serve_dir
                vy = speed * math.sin(ang)
        else:
            trail.append((int(bx), int(by)))
            if len(trail) > 4:
                trail.pop(0)
            bx += vx
            by += vy
            if by < 0:
                by = 0
                vy = -vy
            elif by > H - BS:
                by = H - BS
                vy = -vy

            # Studs mot vänster paddel
            if vx < 0 and bx <= lx + PW and bx + BS >= lx \
                    and by + BS >= ly and by <= ly + PH:
                bx = lx + PW
                rel = ((by + BS / 2) - (ly + PH / 2)) / (PH / 2)
                ang = max(-1.0, min(1.0, rel)) * 1.0
                speed = min(speed * 1.07, MAX_SPEED)
                vx = speed * math.cos(ang)
                vy = speed * math.sin(ang)
                cpu_err = random.randint(-18, 18)
            # Studs mot höger paddel
            elif vx > 0 and bx + BS >= rx and bx <= rx + PW \
                    and by + BS >= ry and by <= ry + PH:
                bx = rx - BS
                rel = ((by + BS / 2) - (ry + PH / 2)) / (PH / 2)
                ang = max(-1.0, min(1.0, rel)) * 1.0
                speed = min(speed * 1.07, MAX_SPEED)
                vx = -speed * math.cos(ang)
                vy = speed * math.sin(ang)

            # Poäng
            if bx < -BS:
                s2 += 1
                serve_dir = -1
                countdown = 40
            elif bx > W:
                s1 += 1
                serve_dir = 1
                countdown = 40
            if s1 >= WIN_SCORE or s2 >= WIN_SCORE:
                if two_players:
                    text = "SPELARE %d VANN!" % (1 if s1 > s2 else 2)
                    col = CYAN if s1 > s2 else MAGENTA
                else:
                    text = "DU VANN!" if s1 > s2 else "DATORN VANN"
                    col = CYAN if s1 > s2 else MAGENTA
                return win_screen(lcd, keys, text, s1, s2, col)

        # --- Rita ---
        lcd.fill(BG)
        for y in range(4, H, 16):
            lcd.fill_rect(W // 2 - 1, y, 2, 8, DIM)
        center_text(lcd, str(s1), 10, DIM, 5, cx=W // 2 - 50)
        center_text(lcd, str(s2), 10, DIM, 5, cx=W // 2 + 50)

        lcd.fill_rect(lx, int(ly), PW, PH, CYAN)
        lcd.vline(lx + 1, int(ly) + 2, PH - 4, WHITE)
        lcd.fill_rect(rx, int(ry), PW, PH, MAGENTA)
        lcd.vline(rx + PW - 2, int(ry) + 2, PH - 4, WHITE)

        if countdown > 0:
            if (countdown // 6) % 2 == 0:
                lcd.fill_rect(int(bx), int(by), BS, BS, YELLOW)
        else:
            for i, (tx, ty) in enumerate(trail):
                lcd.fill_rect(tx + 1, ty + 1, BS - 2, BS - 2, TRAIL_COLS[i])
            lcd.fill_rect(int(bx), int(by), BS, BS, WHITE)

        if not two_players:
            lcd.text("DU", lx + 12, H - 12, DIM)
            lcd.text("CPU", rx - 30, H - 12, DIM)
        lcd.show()
        frame_wait(t0)


# ---------------------------------------------------------------
# Huvudprogram
# ---------------------------------------------------------------
def show_error(lcd, e):
    """Visar felet på skärmen så man ser vad som gick snett."""
    import sys
    import io
    sys.print_exception(e)
    if lcd is None:
        return
    buf = io.StringIO()
    sys.print_exception(e, buf)
    lcd.backlight(100)
    lcd.fill(rgb(120, 0, 0))
    lcd.text("FEL! Se Thonny-skalet", 4, 4, WHITE)
    y = 20
    for line in buf.getvalue().split("\n"):
        while line and y < H - 8:
            lcd.text(line[:39], 4, y, WHITE)
            line = line[39:]
            y += 10
    lcd.show()


def main():
    print("Pico Pong startar...")
    lcd = None
    try:
        lcd = LCD()
        print("Skarm OK")
        keys = Keys()
        sel = 0
        while True:
            sel = game_loop(lcd, keys, sel)
    except KeyboardInterrupt:
        print("Stoppad")
    except Exception as e:
        show_error(lcd, e)


def game_loop(lcd, keys, sel):
    sel = run_menu(lcd, keys, sel)
    if sel in (0, 1):
        while play_pong(lcd, keys, two_players=(sel == 1)) == "again":
            pass
    else:
        key_test(lcd, keys)
    return sel


main()
