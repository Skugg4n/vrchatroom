# Pico Arcade

Startsida med flera spel för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240, ST7789).

Spel: **Pong** (mot datorn eller 2 spelare), **Snake**, **Breakout**, **Flappy**, **Tetris**, **Dino** och **Simon**, plus **Knapptest**.
Rekord sparas på Picon i filen `rekord.json`.

## Kom igång med Thonny

1. Installera MicroPython för Pico 2: håll inne BOOTSEL, koppla in USB och välj i Thonny
   *Konfigurera tolk → Installera eller uppdatera MicroPython* (variant: Raspberry Pi Pico 2).
2. Välj tolken **MicroPython (Raspberry Pi Pico)** nere till höger.
3. Öppna `main.py` och tryck **F5** för att testa.
4. Spara den på Picon som `main.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
   Stäng Thonny och koppla in Picon igen så startar arcaden av sig själv.

## Knappar

Siffrorna är knapparnas nummer på kortet (KEY0–KEY3), samma som visas i Knapptest och på skärmen.

| Spel | KEY0 | KEY1 | KEY2 | KEY3 |
|------|------|------|------|------|
| Startsida | spela | | nästa | föregående |
| Pong, 1 spelare | upp | paus | ner | |
| Pong, 2 spelare | P1 upp | P2 upp | P1 ner | P2 ner |
| Snake | sväng vänster | sväng höger | paus | paus |
| Breakout | skjut iväg bollen | paus | höger | vänster |
| Flappy | flyg | paus | flyg | flyg |
| Tetris | vrid | snabbare (håll) | höger | vänster |
| Dino | hoppa (håll = högre) | paus | hoppa | hoppa |
| Simon | ruta 0 | ruta 1 | ruta 2 | ruta 3 |

**Håll in alla fyra knapparna samtidigt** en kort stund för att gå ur ett spel och tillbaka till startsidan.
I Knapptest håller du in alla fyra i en sekund.

Vill du flytta om knapparna ändrar du konstanterna högst upp i `main.py`
(`K_A`, `K_B`, `K_X`, `K_Y`, `PONG_P1`, `PONG_P2`, `SNAKE_LEFT`, `SNAKE_RIGHT`).

## Fart

- Picon körs i 250 MHz (`OVERCLOCK_HZ`). Sätt den till `None` om något beter sig konstigt.
- Skärmen skickas med 75 MHz SPI, och bakgrunder ritas en gång och kopieras sedan in.
- Thonnys skal visar `FPS: ...` ungefär var 5:e sekund. Målet är 30.

## Felsökning

- `test_knappar.py`: blinkar lampan och bakgrundsljuset och skriver ut knapptryck i Thonny.
- `test_lcd.py`: fyller skärmen med rött, grönt, blått och vitt.
- Om något kraschar blir skärmen röd med felmeddelandet, och felet syns i Thonnys skal.
- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
