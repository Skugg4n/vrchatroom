# Pico Arcade

Startsida med flera spel för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240, ST7789).

Liggande spel: **Pong** (mot datorn eller 2 spelare), **Snake**, **Breakout**, **Flappy**, **Tetris**, **Dino** och **Simon**.
Stående spel (vrid skärmen): **Runner**, **Space** och **Stack**.
Dessutom **Klocka** och **Knapptest**. Rekord sparas på Picon i filen `rekord.json`.

## Kom igång med Thonny

1. Installera MicroPython för Pico 2: håll inne BOOTSEL, koppla in USB och välj i Thonny
   *Konfigurera tolk → Installera eller uppdatera MicroPython* (variant: Raspberry Pi Pico 2).
2. Välj tolken **MicroPython (Raspberry Pi Pico)** nere till höger.
3. Öppna `main.py` och tryck **F5** för att testa.
4. Spara den på Picon som `main.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
   Stäng Thonny och koppla in Picon igen så startar arcaden av sig själv.

## 2-knappsläge (bara KEY0 och KEY1)

Om KEY2 och KEY3 inte fungerar (till exempel om de har lossnat) är `TWO_KEYS = True` högst upp i `main.py`.
Sätt den till `False` när alla fyra knapparna fungerar igen.

| Vad | Så gör du |
|-----|-----------|
| Bläddra i menyn | 0 = föregående, 1 = nästa |
| Välj / starta | tryck 0 och 1 samtidigt (kort) |
| Gå ur ett spel | håll in 0 och 1 i drygt en sekund |
| Spela igen / till menyn (efter game over) | 0 / 1 |
| Pong, 2 spelare | en knapp var: paddeln åker hela tiden, tryck för att vända |
| Breakout | 0/1 styr, bollen skjuts iväg av sig själv (eller 0+1) |
| Tetris | 0/1 flyttar, 0+1 vrider |
| Simon | två rutor i stället för fyra |
| Klockan | 0/1 minus/plus, 0+1 nästa/klar, håll 0+1 = hoppa över |

Paus finns inte i 2-knappsläget.

## Knappar (alla fyra fungerar)

Siffrorna är knapparnas nummer på kortet (KEY0–KEY3), samma som visas i Knapptest och på skärmen.
De översta knapparna, KEY0 och KEY1, används till det man gör mest.

| Spel | KEY0 | KEY1 | KEY2 | KEY3 |
|------|------|------|------|------|
| Startsida | föregående | nästa | spela | |
| Pong, 1 spelare | upp | ner | | paus |
| Pong, 2 spelare | P1 upp | P2 upp | P1 ner | P2 ner |
| Snake | sväng vänster | sväng höger | | paus |
| Breakout | vänster | höger | skjut iväg bollen | paus |
| Flappy | flyg | flyg | flyg | paus |
| Tetris | vänster | höger | vrid | snabbare (håll) |
| Dino | hoppa (håll = högre) | hoppa | hoppa | paus |
| Simon | ruta 0 (uppe till vänster) | ruta 1 (uppe till höger) | ruta 2 (nere till höger) | ruta 3 (nere till vänster) |

**Stående spel:** första gången frågar spelet vilken knapp som sitter till vänster och vilken som sitter till höger
när man håller skärmen på höjden. Valet sparas. Tryck på någon av de andra knapparna på startskärmen för att ställa in igen.

**Håll in alla fyra knapparna samtidigt** en kort stund för att gå ur ett spel och tillbaka till startsidan.
I Knapptest håller du in alla fyra i en sekund.

Vill du flytta om knapparna ändrar du konstanterna högst upp i `main.py`
(`K_X`, `K_Y`, `K_A`, `K_B`, `PONG_SOLO`, `PONG_P1`, `PONG_P2`, `SNAKE_LEFT`, `SNAKE_RIGHT`).

## Klocka

- Om ingen trycker på något på startsidan i 45 sekunder visas en klocka. Ett knapptryck tar dig tillbaka.
- När Picon är inkopplad till datorn med Thonny ställs klockan automatiskt.
- Startar Picon utan dator frågar den vad klockan är: 0/1 minus/plus, 2 nästa/klar, 3 hoppar över (då visas ingen klocka).
- Kortet **KLOCKA** i menyn låter dig ställa in tiden igen.

## Fart

- Picon körs i 250 MHz (`OVERCLOCK_HZ`). Sätt den till `None` om något beter sig konstigt.
- Skärmen skickas med 75 MHz SPI, och bakgrunder ritas en gång och kopieras sedan in.
- Thonnys skal visar `FPS: ...` ungefär var 5:e sekund. Målet är 30.

## Felsökning

- `test_knappar.py`: blinkar lampan och bakgrundsljuset och skriver ut knapptryck i Thonny.
- `test_lcd.py`: fyller skärmen med rött, grönt, blått och vitt.
- Om något kraschar blir skärmen röd med felmeddelandet, och felet syns i Thonnys skal.
- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
