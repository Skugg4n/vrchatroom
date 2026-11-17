# RUSA (stående): spring längs vägen. Vänster/höger byter fil,
# de andra två knapparna hoppar (över de låga hindren). Ta mynten!
HZ = 96                     # horisonten
FOC = 224.0                 # y = HZ + FOC / z  (z = avstånd)
LANE_DX = 74.0
RUN_PZ = 1.25               # spelarens avstånd
RUN_PY = int(HZ + FOC / RUN_PZ)
RUN_Z = [FOC / (y - HZ) for y in range(HZ + 1, VH)]
RUN_HW = [int(110 / z) for z in RUN_Z]
RUN_DIV = [int(LANE_DX / 2 / z) for z in RUN_Z]
RUN_LW = [max(1, int(3 / z)) for z in RUN_Z]
ROAD_A, ROAD_B = rgb(70, 62, 60), rgb(82, 74, 70)
GRASS = ((rgb(30, 100, 50), rgb(40, 120, 60)), (rgb(200, 170, 90), rgb(215, 185, 100)),
         (rgb(220, 230, 240), rgb(200, 215, 235)), (rgb(40, 30, 70), rgb(55, 40, 90)))
SKIES = (((40, 20, 90), (255, 150, 90)), ((90, 160, 240), (250, 220, 150)),
         ((120, 150, 200), (230, 240, 255)), ((5, 5, 25), (60, 30, 100)))
RUMBLE_A = CORAL
SKIN = rgb(255, 200, 150)


@native
def draw_road(fb, travel, ga, gb):
    n = len(RUN_Z)
    for i in range(n):
        y = HZ + 1 + i
        s = int((RUN_Z[i] + travel) * 1.4) & 1
        hw = RUN_HW[i]
        rw = hw // 7 + 1
        fb.hline(0, y, VW, ga if s else gb)
        fb.hline(120 - hw - rw, y, 2 * (hw + rw), RUMBLE_A if s else WHITE)
        fb.hline(120 - hw, y, 2 * hw, ROAD_A if s else ROAD_B)
        if s:
            d = RUN_DIV[i]
            lw = RUN_LW[i]
            fb.hline(120 - d - lw // 2, y, lw, WHITE)
            fb.hline(120 + d - lw // 2, y, lw, WHITE)


def draw_sky(fb, sky, world, t):
    gradient(fb, sky, 0, HZ + 1)
    if world == 3:
        for i in range(20):
            fb.pixel((i * 73 + 11) % VW, (i * 37 + 5) % HZ, WHITE)
        fb.ellipse(180, 40, 12, 12, rgb(250, 245, 210), True)
    else:
        fb.ellipse(120, HZ - 4, 26, 26, rgb(255, 230, 120), True)
    mcol = (rgb(70, 40, 90), rgb(160, 120, 70), rgb(240, 245, 255), rgb(30, 20, 50))[world]
    for x in range(0, VW, 4):
        h = int(16 + 9 * math.sin(x * 0.045 + world) + 6 * math.sin(x * 0.13 + 1))
        fb.fill_rect(x, HZ - h, 4, h + 1, mcol)


def draw_obj(fb, o, t):
    z = o[1]
    if z < 0.7:
        return
    s = 1 / z
    y = int(HZ + FOC / z)
    x = int(120 + o[0] * LANE_DX / z)
    if o[2] == 0:                       # hög spärr: byt fil
        w = max(2, int(62 * s))
        h = max(2, int(40 * s))
        fb.fill_rect(x - w // 2, y - h, w, h, RUMBLE_A)
        b = max(1, h // 5)
        fb.fill_rect(x - w // 2, y - h + b, w, b, WHITE)
        fb.fill_rect(x - w // 2, y - h + 3 * b, w, b, WHITE)
    elif o[2] == 2:                     # lågt hinder: hoppa
        w = max(2, int(62 * s))
        h = max(1, int(12 * s))
        fb.fill_rect(x - w // 2, y - h, w, h, AMBER)
        fb.fill_rect(x - w // 2, y - h, w, max(1, h // 3), YELLOW)
    else:                               # mynt
        r = max(1, int(11 * s))
        rx = max(1, int(r * abs(math.sin(t * 0.15 + z))))
        cy = y - int(26 * s)
        fb.ellipse(x, cy, rx, r, YELLOW, True)
        if rx > 2:
            fb.ellipse(x, cy, max(1, rx // 2), max(1, r // 2), AMBER, True)


def draw_runner(fb, x, t, jh):
    y = RUN_PY - jh
    fb.ellipse(x, RUN_PY, 14 - jh // 6, 4, rgb(30, 30, 30), True)
    leg = (t // 3) % 2 if jh == 0 else 2
    fb.fill_rect(x - 6, y - 14, 4, 12 if leg == 1 else 8, rgb(50, 80, 200))
    fb.fill_rect(x + 2, y - 14, 4, 8 if leg == 1 else 12, rgb(50, 80, 200))
    fb.fill_rect(x - 7, y - 32, 14, 19, TEAL)
    fb.fill_rect(x - 10, y - 30 + (3 if leg == 1 else 0), 3, 10, SKIN)
    fb.fill_rect(x + 7, y - 30 + (0 if leg == 1 else 3), 3, 10, SKIN)
    fb.ellipse(x, y - 39, 7, 7, SKIN, True)
    fb.fill_rect(x - 7, y - 47, 14, 4, rgb(120, 60, 30))


def play(lcd, keys):
    return v_play(lcd, keys, "RUSA", AMBER, ("Spring sa langt du kan!", "Vanster/hoger: byt fil.", "Andra knapparna: hoppa", "over de laga hindren."), "rusa", run_game)


def run_game(lcd, fb, keys, L, R):
    J = [k for k in (K0, K1, K2, K3) if k != L and k != R]
    lane = 0
    px = 120.0
    obs = []          # [fil, z, typ, passerad]  typ 0 spärr, 1 mynt, 2 lågt hinder
    dist = 0.0
    coins = 0
    jump = 0          # bildrutor kvar av hoppet
    next_row = 3.0
    world = -1
    t = 0
    parts = Particles(40)
    keys.wait_release()
    while True:
        t0 = time.ticks_ms()
        keys.update()
        if keys.pause():
            return None
        if keys.pressed(L):
            lane = max(-1, lane - 1)
        if keys.pressed(R):
            lane = min(1, lane + 1)
        if jump == 0 and any(keys.pressed(k) for k in J):
            jump = 18
        if jump:
            jump -= 1
        jh = int(46 * math.sin(math.pi * jump / 18)) if jump else 0
        px += (120 + lane * LANE_DX / RUN_PZ - px) * 0.45
        speed = min(0.13 + dist * 0.0008, 0.42)
        dist += speed
        w = int(dist * 10) // 800 % 4
        if w != world:
            world = w
            sky = [mix(SKIES[w][0], SKIES[w][1], y / HZ) for y in range(HZ + 1)]
        next_row -= speed
        if next_row <= 0:
            next_row = random.uniform(3.6, 6.0)
            lanes = [-1, 0, 1]
            for _ in range(random.choice((1, 1, 2))):
                kind = 2 if dist > 30 and random.random() < 0.4 else 0
                obs.append([lanes.pop(random.randint(0, len(lanes) - 1)), 22.0, kind, False])
            if random.random() < 0.75:
                ln = random.choice(lanes)
                for k in range(random.choice((1, 3, 4))):
                    obs.append([ln, 22.0 + k * 1.2, 1, False])
        crashed = False
        for o in obs:
            o[1] -= speed
            if not o[3] and o[1] <= RUN_PZ:
                o[3] = True
                if o[0] == lane:
                    if o[2] == 0 or (o[2] == 2 and jh < 12):
                        crashed = True
                    elif o[2] == 1:
                        coins += 1
                        o[1] = -1
                        parts.burst(px, RUN_PY - 30 - jh, YELLOW, 6, 2, 10)
                        if coins >= 30:
                            goal("rusa", 1)
        obs = [o for o in obs if o[1] > 0.6]
        score = int(dist * 10) + coins * 25
        if score >= 1000:
            goal("rusa", 0)
        if score >= 3000:
            goal("rusa", 2)
        draw_sky(fb, sky, world, t)
        draw_road(fb, dist, GRASS[world][0], GRASS[world][1])
        obs.sort(key=lambda o: -o[1])
        for o in obs:
            if o[1] > RUN_PZ:
                draw_obj(fb, o, t)
        draw_runner(fb, int(px), t, jh)
        for o in obs:
            if o[1] <= RUN_PZ:
                draw_obj(fb, o, t)
        parts.draw(fb)
        big(fb, str(score), 6, 6, WHITE, 2)
        fb.ellipse(VW - 40, 13, 6, 6, YELLOW, True)
        fb.text("%d" % coins, VW - 30, 9, WHITE)
        if t < 70 and (t // 10) % 2 == 0:
            ctext(fb, "%d <      > %d" % (L, R), 150, WHITE, 2, VW // 2)
            ctext(fb, "hoppa: %d / %d" % (J[0], J[1]), 176, YELLOW, 1, VW // 2)
        lcd.show()
        if crashed:
            for k in range(6):
                fb.rect(0, 0, VW, VH, CORAL if k % 2 == 0 else WHITE)
                fb.rect(1, 1, VW - 2, VH - 2, CORAL if k % 2 == 0 else WHITE)
                lcd.show()
                time.sleep_ms(80)
            return score
        t += 1
        wait(t0)
