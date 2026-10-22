# Pico Arcade

Startsida med flera spel för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240, ST7789).

Spel: **Pong** (mot datorn eller 2 spelare), **Snake**, **Breakout** och **Flappy**, plus **Knapptest**.
Rekord sparas på Picon i filen `rekord.json`.

## Kom igång med Thonny

1. Installera MicroPython för Pico 2: håll inne BOOTSEL, koppla in USB och välj i Thonny
   *Konfigurera tolk → Installera eller uppdatera MicroPython* (variant: Raspberry Pi Pico 2).
2. Välj tolken **MicroPython (Raspberry Pi Pico)** nere till höger.
3. Öppna `main.py` och tryck **F5** för att testa.
4. Spara den på Picon som `main.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
   Stäng Thonny och koppla in Picon igen så startar arcaden av sig själv.

## Knappar

| Knapp | Startsida | Pong (1 sp.) | Pong (2 sp.) | Snake | Breakout | Flappy |
|-------|-----------|--------------|--------------|-------|----------|--------|
| KEY0 (A), GP15 | spela | | P1 upp | | skjut iväg bollen | flyg |
| KEY1 (B), GP17 | | paus | P1 ner | paus | paus | paus |
| KEY2 (X), GP2 | föregående | upp | P2 upp | sväng vänster | vänster | flyg |
| KEY3 (Y), GP3 | nästa | ner | P2 ner | sväng höger | höger | flyg |

**Håll in alla fyra knapparna samtidigt** för att gå ur ett spel och tillbaka till startsidan.
I Knapptest håller du in alla fyra i en sekund.

Om knapparna känns bakvända, ändra `K_A`, `K_B`, `K_X` och `K_Y` högst upp i `main.py`.

## Felsökning

- `test_knappar.py`: blinkar lampan och bakgrundsljuset och skriver ut knapptryck i Thonny.
- `test_lcd.py`: fyller skärmen med rött, grönt, blått och vitt.
- Om något kraschar blir skärmen röd med felmeddelandet, och felet syns i Thonnys skal.
- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
