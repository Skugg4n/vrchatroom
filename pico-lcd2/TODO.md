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
