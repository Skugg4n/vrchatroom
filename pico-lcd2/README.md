# Pico Pong

Startsida + Pong för **Raspberry Pi Pico 2** med **Waveshare Pico-LCD-2** (2", 320x240, ST7789).

## Kom igång med Thonny

1. Flasha MicroPython för Pico 2 (RP2350): håll inne BOOTSEL, koppla in USB och dra
   `.uf2`-filen från micropython.org till enheten `RP2350`. Det går också via Thonny:
   *Verktyg → Alternativ → Tolk → Installera eller uppdatera MicroPython*.
2. I Thonny: välj tolken **MicroPython (Raspberry Pi Pico)** nere till höger.
3. Öppna `main.py`, tryck **Kör** (F5) för att testa.
4. Spara den på Picon (*Arkiv → Spara som → Raspberry Pi Pico*) med namnet `main.py`,
   så startar spelet automatiskt varje gång Picon får ström.

## Knappar

| Knapp | Pinne | Meny | 1 spelare | 2 spelare |
|-------|-------|------|-----------|-----------|
| KEY0 (A) | GP15 | välj | (inget) | spelare 1 upp |
| KEY1 (B) | GP17 | | paus | spelare 1 ner |
| KEY2 (X) | GP2 | upp | paddel upp | spelare 2 upp |
| KEY3 (Y) | GP3 | ner | paddel ner | spelare 2 ner |

I 2-spelarläge pausar man genom att trycka båda sina knappar samtidigt.
Först till 7 vinner.

Använd **KNAPPTEST** i menyn för att se vilken fysisk knapp som är vilken. Om du vill
flytta om dem, ändra `K_A`, `K_B`, `K_X` och `K_Y` högst upp i `main.py`.

## Bra att veta

- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
- Färger skapas med `rgb(r, g, b)` (0–255), funktionen sköter byteordningen åt skärmen.
- `big_text()` skriver text i valfri storlek om du vill bygga fler skärmar.
