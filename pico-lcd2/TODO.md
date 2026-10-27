# TODO: Pico Pong (Pico 2 + Waveshare Pico-LCD-2)

- [x] research: verify Pico-LCD-2 pinout (LCD: DC=GP8 CS=GP9 SCK=GP10 MOSI=GP11 RST=GP12 BL=GP13, keys: GP15 GP17 GP2 GP3)
- [x] driver: ST7789 init (320x240 landscape), RGB565 framebuffer, byte-swapped colors, show()
- [x] driver: PWM backlight with fade-in
- [x] input: Keys class with pull-ups, held()/pressed() edge detection, wait_release()
- [x] gfx: big_text() scaled font + center helper
- [x] ui: start screen (gradient, parallax stars, bobbing rainbow title, menu, footer hints)
- [x] game: pong 1P vs CPU (AI with reaction error)
- [x] game: pong 2P (A/B vs X/Y)
- [x] game: ball trail, angle by hit position, speed-up, serve countdown, score, first to 7
- [x] game: pause (B in 1P, both own keys in 2P) + win screen (play again / menu)
- [x] ui: key test screen to find physical button positions
- [x] test: smoke-run in CPython with mocked machine/framebuf
- [x] docs: README with Thonny instructions
- [x] git: commit + push to claude/cool-franklin-izolil

## Fix: black screen on hardware
- [x] debug: backlight started at 0 and only faded in from the menu -> any early stop/crash left screen black
- [x] fix: backlight on immediately in LCD init
- [x] fix: catch exceptions, print to Thonny shell + draw error on screen
- [x] add: test_lcd.py minimal color-fill test with progress prints
- [x] test: re-run mock scenarios
- [x] git: commit + push

## Diagnose: test_lcd.py runs but screen fully black (no backlight)
- [x] add: test_knappar.py (onboard LED blink, backlight blink, key prints) to verify Pico <-> LCD board contact
- [x] git: commit + push

## Feature: Pico Arcade launcher with several games
- [x] refactor: shared helpers (Stars, result_screen, choose, pause_screen, clip helpers)
- [x] save: high scores in rekord.json on the Pico
- [x] ui: carousel start page (title, game card with live animated preview, arrows, dots, slide + warp-stars transition)
- [x] game: Pong (mode chooser 1P/2P, reuse existing)
- [x] game: Snake (relative turns X/Y, speeds up, record)
- [x] game: Breakout (lives, levels, particles, record)
- [x] game: Flappy (sky, clouds, pipes, ground scroll, record)
- [x] keep: KNAPPTEST as last card
- [x] input: hold all 4 keys = exit any game to start page (key test: hold 1 s)
- [x] test: mock-run every game + menu, render screenshots
- [x] docs: update README controls
- [x] git: commit + push

## Round 4: keys, speed, more games
- [x] keys: swap roles of KEY2 and KEY3 (X=KEY3, Y=KEY2)
- [x] keys: pong 2P -> P1 = KEY0/KEY2, P2 = KEY1/KEY3 (phone held between players)
- [x] keys: snake steer with KEY0 (left) / KEY1 (right), pause KEY2/KEY3
- [x] keys: on-screen hints show key numbers, generated from constants
- [x] keys: exit = all 4 held ~0.25 s (avoid accidental exits in 2P)
- [x] perf: overclock 250 MHz + SPI 75 MHz request (was 62.5 -> rounded down to 37.5 MHz)
- [x] perf: cached glyph runs for big_text
- [x] perf: background buffer (draw once, memcpy each frame) for gradients/sky/fields
- [x] perf: micropython.native on hot draw functions (with CPython fallback)
- [x] perf: print FPS to Thonny shell
- [x] game: Tetris (7-bag, rotate w/ kicks, ghost, soft drop, levels)
- [x] game: Dino runner (variable jump, cacti, birds, night sky)
- [x] game: Simon (4-key memory game)
- [x] test: mock-run all games + menu, screenshots
- [x] docs: README controls table
- [x] git: commit + push

## Round 5: top keys for main actions, Simon fix, portrait games
- [x] keys: KEY0/KEY1 = left/right (most used), KEY2 = select/jump/rotate, KEY3 = back/pause
- [x] keys: pong 1P up/down on KEY0/KEY1; 2P unchanged (P1 0/2, P2 1/3)
- [x] fix: Simon pad layout KEY2 <-> KEY3 (KEY3 bottom-left, KEY2 bottom-right)
- [x] portrait: LCD portrait()/landscape() (MADCTL + window), 240x320 framebuffer view on same buffer
- [x] portrait: first-run calibration of left/right key, saved in rekord.json, re-calibrate with another key
- [x] portrait: shared start + result screens
- [x] game: RUNNER (pseudo-3D 3-lane runner, coins, barriers, sunset temple sky)
- [x] game: SPACE (vertical shooter, auto-fire, 2 enemy types, lives)
- [x] game: STACK (tower stacking, cut overhang, perfect combos)
- [x] ui: menu cards with STAENDE badge + previews
- [x] test: mock-run all, screenshots
- [x] docs + git push

## Clock (requested mid-round)
- [x] idle clock on start page after 45 s (dimmed backlight, any key returns)
- [x] boot: use RTC if Thonny already set it, else ask for time (skippable = no clock)
- [x] KLOCKA card to set time manually
- [x] fix: Stack falling-piece cleanup used wrong sign
- [x] chore: remove committed __pycache__, add .gitignore

## 2-key mode (KEY2/KEY3 fell off)
- [x] keys: TWO_KEYS flag; virtual taps (on release, no chord), chord press/tap, long hold both = exit
- [x] ui: menu/choose/result/time setup/keytest use 0/1 + chord, hints adapt
- [x] game: Pong 2P one-button paddles (press = change direction)
- [x] game: Breakout auto-launch / chord launch
- [x] game: Tetris tap-move + repeat, chord = rotate
- [x] game: Simon with 2 pads
- [x] portrait: start screen hints adapt
- [x] test: mock-run with only KEY0/KEY1
- [x] docs + git push

## Rename
- [x] git mv main.py -> main2.py, update README + header comment (autostart via main.py: import main2)

## Clock-only program (protect the remaining buttons)
- [x] main.py = standalone clock (autostarts), arcade stays in main2.py
- [x] time from RTC (Thonny sets it); ask only if unknown: KEY0 = hour+, KEY1 = minute+, auto-save after 5 s idle
- [x] face: big time, blinking colon, seconds bar, Swedish weekday + date when known, stars
- [x] night dimming (22-07), low frame rate, no overclock
- [x] optional: hold KEY0+KEY1 3 s to set time again
- [x] test in mock, screenshot
- [x] docs + git push
- [x] redesign: minimalist look (custom rounded 7-segment digits, ghost segments, time-of-day colors, breathing colon, seconds dot)

## Rename clock
- [x] git mv main.py -> klocka.py, update header + README (autostart: main.py with `import klocka`)

## Tetris soft drop in 2-key mode
- [x] tap 0/1 = move one step, hold 0/1 (> TETRIS_HOLD frames) = soft drop; hint text updated

## Bigger games as standalone files (2 keys: KEY0/KEY1)
- [x] labyrint.py: raycasting 3D maze (80 rays, distance fog, tile edges), random mazes growing per level
- [x] labyrint: controls hold 0/1 = turn, 0+1 tap = walk/stop, hold 0+1 = menu
- [x] labyrint: coins, key + locked exit (lvl 3+), ghosts (lvl 4+), lives, fog-of-war minimap, score/time bonus, save
- [x] hoppa.py: auto-run platformer, jump/double jump/hold for higher, springs, spikes, gaps, coins
- [x] hoppa: 10 generated levels (seeded, difficulty ramp), 4 themes with parallax hills, checkpoints, 3 big coins
- [x] hoppa: level select with saved progress, level complete screen
- [x] test both in mock, screenshots
- [x] docs + git push
- [x] labyrint: widen corridors to 2 tiles (expand maze) so the 3D view shows real corridors
- [x] hoppa: taller, clearer spikes; replace random.sample (not in MicroPython)

## Launcher (main.py) so all programs are reachable without editing files
- [x] main.py: menu KLOCKA / LABYRINT 3D / HOPPA! / PICO ARCADE, 0/1 browse, 0+1 start, remembers last choice
- [x] auto-start last choice after 10 s idle (plug in = clock starts)
- [x] free launcher memory, then import the chosen module
- [x] back to launcher: hold 0+1 in labyrint title, hoppa level select, arcade start page -> machine.soft_reset()
- [x] klocka: hold 0+1 3 s -> choice screen (0 = set time, 1 = menu)
- [x] test in mock, docs, git push
- [x] fix: klocka WHITE constant missing (found by launcher test)

## Fix: MicroPython-only crashes reported from hardware
- [x] hoppa: `FLAG in bytearray` -> NotImplementedError on MicroPython; loop instead
- [x] labyrint: `bytearray([1]) * n` -> TypeError on MicroPython; use bytearray([1] * n)
- [x] test: stricter mock bytearray (no `in`, no `*`) reproduces both bugs; all programs pass with it
- [x] git push

## Round 6: 4 keys again, four polished games for Pico Arcade
- [x] main2: TWO_KEYS = False
- [x] picolib.py: shared LCD/Keys(4)/text/stars/scores/title/result/pause/back-to-arcade
- [x] launch flow: arcade card -> starta.txt + soft_reset -> main.py imports module; exit -> back to arcade on same card
- [x] game: METEORER (asteroids: inertia, wrap, splitting rocks, UFO, waves, extra lives, particles, shake, popups)
- [x] game: TURBO (pseudo-3D racer: curves, hills, traffic, roadside sprites, checkpoints, timer, speedo)
- [x] game: BUBBLOR (bubble shooter: hex grid, aim guide with bounce, pop 3+, falling orphans, ceiling drop, levels)
- [x] game: MINIGOLF (9 holes: walls, sand, water, slopes, windmills, power meter, par scoring)
- [x] arcade: cards with animated previews + records for the four games
- [x] test: strict MicroPython-like mock for all, screenshots
- [x] docs + git push
- [x] golf: shorter windmill blades, wider hole 6, hub is a tunnel (only blades block)
- [x] turbo: clip preview road inside the card; title road below key legend
- [x] launcher: KEY2 also starts; starta.txt for direct start/back

## One file for the four new games
- [x] build nyaspel.py = picolib + meteor + turbo + bubblor + minigolf (top-level names prefixed per game, comments kept)
- [x] dispatcher: SCORES["_spel"] picks game; arcade launch() writes it + starta.txt "nyaspel"
- [x] remove picolib/meteor/turbo/bubblor/minigolf .py from repo
- [x] test all four via the full launcher -> arcade -> game -> back flow (strict mock)
- [x] docs + git push
