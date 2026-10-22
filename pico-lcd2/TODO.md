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
