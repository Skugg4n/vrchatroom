# PICO SPEL

Sju spel i **en enda fil** (`main.py`) för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240).

## Kom igång

1. Installera MicroPython för Pico 2 i Thonny (*Konfigurera tolk → Installera eller uppdatera MicroPython*, variant Raspberry Pi Pico 2).
2. Öppna `main.py` i Thonny och spara den på Picon som `main.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
3. Klart! Spelen startar av sig själva när Picon får ström. Rekorden sparas i `spel.json`.

## Knapparna

```
KEY0 (uppe vänster)    KEY1 (uppe höger)
KEY3 (nere vänster)    KEY2 (nere höger)
```

- **Menyn:** 0/1 väljer spel, 2 startar.
- **I alla spel:** håll in alla fyra knapparna = paus (2 fortsätt, 3 till menyn).
- **Efter game over:** 2 spela igen, 3 till menyn.

## Spelen

| Spel | Vad | KEY0 | KEY1 | KEY3 | KEY2 |
|------|-----|------|------|------|------|
| **TETRIS** | Skuggbit, nästa 3 bitar, kombos, nivåer, "TETRIS!" vid 4 rader | vänster | höger | släpp direkt | vrid |
| **SPÖKJAKT** | Pac-Man med fyra spöken som har egna personligheter, kraftpiller och tunnel | upp | höger | vänster | ner |
| **INVASION** | Space Invaders med förstörbara skydd, UFO, power-ups (trippel, snabb, sköld) och superlaser | vänster | höger | superlaser (full mätare) | skjut |
| **KROSS** | Breakout med 6 banor, stenar som tål flera slag, metall, sprängstenar och power-ups (bred, multiboll, långsam, laser, liv) | vänster | höger | skjut iväg bollen | skjut iväg bollen / laser |
| **STUDS** | Doodle Jump: rörliga plattor, plattor som går sönder, studsmattor och monster | vänster | höger | | skjut uppåt |
| **2048** | Pusslet med glidande brickor | upp | höger | vänster | ner |
| **KURVAN** | Achtung die Kurve mot datorn, mot 2 datorer eller 2 spelare. Först till 5 | P1 vänster | P2 vänster | P1 höger | P2 höger |

I SPÖKJAKT och 2048 visar pilarna i skärmens hörn vilken knapp som är vilken riktning.

## Bra att veta

- Skärmbilden skapas som allra första sak och det finns bara en, så minnet räcker.
  Kör du filen flera gånger med F5 i Thonny rensas förra körningen bort först.
- Om något kraschar visas felet på skärmen (och i Thonnys skal). Tryck på en knapp för att komma tillbaka.
- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
- Gamla versioner av programmen ligger i mappen `gammalt/`.
