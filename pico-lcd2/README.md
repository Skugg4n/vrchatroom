# PICO SPEL

Tio spel i **en enda fil** (`main.py`) för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240).

## Kom igång

1. Installera MicroPython för Pico 2 i Thonny (*Konfigurera tolk → Installera eller uppdatera MicroPython*, variant Raspberry Pi Pico 2).
2. Öppna `main.py` i Thonny och spara den på Picon som `main.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
3. Klart! Spelen startar av sig själva när Picon får ström. Rekord, stjärnor och framsteg sparas i `spel.json`.

Filen måste heta `main.py` på Picon, eftersom spelen läses in från den när du väljer dem.

## Knapparna

```
KEY0 (uppe vänster)    KEY1 (uppe höger)
KEY3 (nere vänster)    KEY2 (nere höger)
```

- **Menyn:** 0/1 väljer spel, 2 startar, 3 visar stjärnor och teman.
- **I alla spel:** håll in alla fyra knapparna = paus (2 fortsätt, 3 till menyn).
- **Efter game over:** 2 spela igen, 3 till menyn.

## Spelen

| Spel | Vad | KEY0 | KEY1 | KEY3 | KEY2 |
|------|-----|------|------|------|------|
| **TETRIS** | Tre lägen: MARATON, SPRINT 40 (så snabbt som möjligt) och SKATT (gräv fram guld i skräprader som växer) | vänster | höger | släpp direkt | vrid |
| **LÅDOR** | Sokoban med 20 banor. Knuffa lådorna till prickarna på så få drag som möjligt | upp | höger | vänster | ner |
| **FLÖDE** | Koppla ihop prickar med samma färg och fyll rutnätet. 25 banor + TIDSJAKT | upp | höger | vänster | ner |
| **ÄVENTYR** | Plattformsspel med 8 banor: mynt, 3 ädelstenar per bana, kontrollpunkter, monster, is, lava, moln | vänster | höger | dash | hoppa |
| **STUDS** | Hoppa uppåt genom NATTEN, HIMLEN, RYMDEN och GALAXEN. Jetpack, fjäderskor, moln och fladdermöss | vänster | höger | | skjut |
| **SPÖKJAKT** | Pac-Man med tre labyrinter, fyra spöken med egna personligheter och bonusfrukt | upp | höger | vänster | ner |
| **2048** | Pusslet med glidande brickor | upp | höger | vänster | ner |
| **INVASION** | Space Invaders med skydd, UFO, power-ups och superlaser | vänster | höger | superlaser | skjut |
| **KROSS** | Breakout med 6 banor, sprängstenar och power-ups | vänster | höger | skjut iväg bollen | skjut iväg bollen / laser |
| **KURVAN** | Achtung die Kurve mot datorn, mot 2 datorer eller 2 spelare | P1 vänster | P2 vänster | P1 höger | P2 höger |

I spelen med fyra riktningar visar pilarna i skärmens hörn vilken knapp som är vilken riktning.

**LÅDOR:** håll alla fyra för pausrutan, där 0 ångrar drag (flera gånger), 1 börjar om och 3 går till banorna.

**FLÖDE:** gå in på en prick (eller slutet av en linje) så ritar du. Tryck två knappar samtidigt för att lyfta eller sänka pennan och gå fritt. Fyller du alla rutor blir det PERFEKT.

**ÄVENTYR:** håll in hopp för högre hopp. Dash (KEY3) krossar spruckna block och monster, och laddas om när du landar. Hoppa på monstren, men inte på igelkottarna!

## Stjärnor och belöningar

Varje spel har tre utmaningar. Klarar du en får du en stjärna (det syns direkt överst på skärmen). Tryck 3 i menyn för att se utmaningarna.

Stjärnorna låser upp:
- **Tetris SPRINT 40** (3 stjärnor) och **SKATT** (8 stjärnor)
- **Menyteman:** SOLNEDGÅNG (8), HAV (16), SKOG (22) och GULD (30). Byt tema med 2 på stjärnskärmen.

## Så funkar filen

För att allt ska rymmas i minnet ligger varje spels kod längst ner i `main.py` som kommentarer (`#@@ namn` följt av rader som börjar med `#|`). Bara menyn startar direkt, och när du väljer ett spel läses just det spelet in. När du går tillbaka till menyn släpps det ur minnet igen.

`main.py` byggs av källfilerna i `kalla/`:

```
kalla/core_base.py     skärm, knappar, text, effekter, rekord, utmaningar
kalla/core_menu.py     menyn, stjärnskärmen, teman, ikoner och delad grafik
kalla/spel/*.py        ett spel per fil
kalla/build.py         bygger ../main.py (kör: python3 build.py)
kalla/verktyg/         banverktyg: gen_ladr.py (Sokoban-banor med lösare),
                       gen_aventyr.py (bygger och kontrollerar ÄVENTYRs banor),
                       pac_check.py (kontrollerar SPÖKJAKTs labyrinter)
```

## Bra att veta

- Skärmbilden skapas som allra första sak och det finns bara en, så minnet räcker.
  Kör du filen flera gånger med F5 i Thonny rensas förra körningen bort först.
- Om något kraschar visas felet på skärmen (och i Thonnys skal). Tryck på en knapp för att komma tillbaka.
- Skärmens inbyggda typsnitt saknar å, ä och ö, så texten på skärmen skrivs utan dem.
- Gamla versioner av programmen ligger i mappen `gammalt/`.
