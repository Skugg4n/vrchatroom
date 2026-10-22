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
