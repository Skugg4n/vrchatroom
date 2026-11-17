# STAPLA (stående): tryck på valfri knapp för att släppa blocket.
# Det som sticker ut ramlar av. Perfekt träff = blocket växer. Fortare och fortare!
SB_H = 14
SB_BASE = 296
SB_SKY = ((20, 30, 70), (120, 160, 230), (250, 170, 120), (60, 20, 90), (4, 4, 20))


def play(lcd, keys):
    return v_play(lcd, keys, "STAPLA", CORAL, ("Bygg ett sa hogt", "torn som mojligt.", "Valfri knapp slapper", "blocket."), "stapla", sb_game)


def sb_col(i):
    a = i * 0.25
    return rgb(int(150 + 100 * math.sin(a)), int(150 + 100 * math.sin(a + 2.1)), int(150 + 100 * math.sin(a + 4.2)))


def sb_bg(h):
    k = min(len(SB_SKY) - 2, h // 15)
    f = min(1.0, (h - k * 15) / 15)
    top = lerp(SB_SKY[k + 1], SB_SKY[min(k + 2, len(SB_SKY) - 1)], f)
    bot = lerp(SB_SKY[k], SB_SKY[k + 1], f)
    return [mix(top, bot, y / (VH - 1)) for y in range(VH)]


def sb_game(lcd, fb, keys, L, R):
    stack = [[65.0, 110.0]]         # x, bredd för varje våning
    cur_w = 110.0
    x = 0.0
    dirx = 1
    speed = 3.0
    perfect = 0
    falling = []                    # bitar som ramlar: x, y, bredd, fart, färg
    cam = 0.0
    parts = Particles(60)
    pops = Popups()
    bg = sb_bg(0)
    t = 0
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return None
        n = len(stack)
        x += dirx * speed
        if x < -cur_w * 0.6 or x > VW - cur_w * 0.4:
            dirx = -dirx
        if any(keys.pressed(k) for k in (K0, K1, K2, K3)):
            px, pw = stack[-1]
            y = SB_BASE - n * SB_H
            if abs(x - px) <= 3:
                x = px
                perfect += 1
                parts.burst(x + cur_w / 2, y + cam, WHITE, 18, 3, 14)
                if perfect >= 3:
                    goal("stapla", 1)
                    cur_w = min(150.0, cur_w + 8)
                    pops.add(x + cur_w / 2, y + cam - 14, "PERFEKT x%d!" % perfect, YELLOW)
                else:
                    pops.add(x + cur_w / 2, y + cam - 14, "PERFEKT!", YELLOW)
                stack.append([x, cur_w])
            else:
                perfect = 0
                lo = max(x, px)
                hi = min(x + cur_w, px + pw)
                if hi <= lo:
                    falling.append([x, y, cur_w, 0.0, sb_col(n)])
                    for k in range(40):
                        t1 = time.ticks_ms()
                        for f in falling:
                            f[3] += 0.6
                            f[1] += f[3]
                        sb_draw(fb, bg, stack, falling, None, 0, cam, n, t)
                        stext(fb, "MISS!", 120, CORAL, 4, VW // 2)
                        lcd.show()
                        wait(t1)
                    return n - 1
                if x < lo:
                    falling.append([x, y, lo - x, 0.0, sb_col(n)])
                if x + cur_w > hi:
                    falling.append([hi, y, x + cur_w - hi, 0.0, sb_col(n)])
                cur_w = hi - lo
                stack.append([lo, cur_w])
            n = len(stack)
            if n - 1 >= 15:
                goal("stapla", 0)
            if n - 1 >= 40:
                goal("stapla", 2)
            speed = min(13.0, 3.0 + (n - 1) * 0.3)      # fortare för varje våning
            dirx = 1 if n % 2 else -1
            x = -cur_w * 0.6 if dirx > 0 else VW - cur_w * 0.4
            if (n - 1) % 3 == 0:
                bg = sb_bg(n - 1)
        target = max(0.0, (len(stack) - 12) * SB_H)
        cam += (target - cam) * 0.15
        for f in falling:
            f[3] += 0.6
            f[1] += f[3]
        falling = [f for f in falling if f[1] + cam < VH + 20]
        sb_draw(fb, bg, stack, falling, x, cur_w, cam, len(stack), t)
        parts.draw(fb)
        pops.draw(fb)
        lcd.show()
        t += 1
        wait(t0)


def sb_draw(fb, bg, stack, falling, x, cur_w, cam, n, t):
    gradient(fb, bg, 0, VH)
    c = int(cam)
    for i in range(12):                                  # moln, sedan stjärnor högt upp
        sx = (i * 83 + 7) % VW
        sy = (i * 47 + c // 2) % VH
        if n > 30:
            fb.fill_rect(sx, sy, 2, 2, WHITE)
        else:
            fb.ellipse(sx, sy, 14, 4, rgb(230, 235, 250), True)
    for i, (bx, bw) in enumerate(stack):
        y = SB_BASE - i * SB_H + c
        if y > VH or y < -SB_H:
            continue
        col = sb_col(i)
        fb.fill_rect(int(bx), y, int(bw), SB_H, col)
        fb.hline(int(bx), y, int(bw), WHITE)
        fb.hline(int(bx), y + SB_H - 1, int(bw), BLACK)
    if SB_BASE + SB_H + c < VH:
        fb.fill_rect(0, SB_BASE + SB_H + c, VW, VH, rgb(60, 50, 40))
    for f in falling:
        fb.fill_rect(int(f[0]), int(f[1]) + c, int(f[2]), SB_H, f[4])
    if x is not None:
        y = SB_BASE - n * SB_H + c
        fb.fill_rect(int(x), y, int(cur_w), SB_H, sb_col(n))
        fb.hline(int(x), y, int(cur_w), WHITE)
    s = str(n - 1)
    big(fb, s, VW // 2 - len(s) * 12, 10, WHITE, 3)
    fb.text("REKORD %d" % SCORES.get("stapla", 0), 4, 40, WHITE)
