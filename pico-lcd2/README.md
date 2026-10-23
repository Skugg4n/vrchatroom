# Pico Klocka (`klocka.py`)

En minimalistisk klocka för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2**.
Spara `klocka.py` på Picon. För att klockan ska starta av sig själv när Picon får ström,
lägg en `main.py` på Picon som bara innehåller raden `import klocka`.

- Egna rundade siffror med svaga släckta segment, nästan svart bakgrund.
- Färgen följer dygnet: varm på morgonen, kall vit på dagen, orange på kvällen och dovt röd på natten
  (22–07, då dämpas även skärmen).
- Kolonet andas i takt med sekunderna och en liten prick vandrar längs en tunn linje.
- Veckodag och datum visas när Picon har fått tiden från datorn.

**Tiden:** Med Thonny inkopplat ställs klockan automatiskt. Startar Picon utan dator frågar den efter tiden:
KEY0 = timme +1, KEY1 = minut +1 (håll inne för att gå fort). Rör inget på 5 sekunder så sparas tiden.
Vill du ställa om tiden senare håller du in KEY0 och KEY1 i 3 sekunder. Annars behöver knapparna aldrig röras.

---

# Större spel (egna filer, bara KEY0 och KEY1)

Varje spel är en egen fil. Kör med F5 i Thonny, eller lägg en `main.py` på Picon med
`import labyrint` eller `import hoppa` så startar spelet av sig själv.

## LABYRINT 3D (`labyrint.py`)

Gå runt i en 3D-labyrint och hitta utgången (den lila portalen). Labyrinten blir större för varje nivå.

- Samla mynt. Från nivå 3 är utgången låst tills du har hittat **nyckeln**.
- Från nivå 4 vandrar **spöken** i gångarna. Du har 3 liv.
- Kartan uppe till höger ritas upp där du har varit.
- Snabbare klarad nivå ger mer bonus. Högsta nivån och rekordet sparas i `labyrint.json`.

| Knapp | Gör |
|-------|-----|
| håll 0 / håll 1 | sväng vänster / höger |
| 0+1 kort | börja gå / stanna |
| håll 0+1 | paus (fortsätt eller till menyn) |

## HOPPA! (`hoppa.py`)

Plattformsspel med 10 banor i 4 världar: Ängen, Öknen, Natten och Slottet. Gubben springer av sig själv.

- Hoppa över glapp, taggar och pelare. Röda studsmattor skjuter upp dig över höga murar.
- Håll inne knappen för högre hopp, tryck igen i luften för **dubbelhopp**.
- Varje bana har en **kontrollpunkt** (blå flagga) och **3 stora mynt**.
- Klarar du en bana öppnas nästa. Framsteg och mynt sparas i `hoppa.json`.

| Knapp | Gör |
|-------|-----|
| 0 eller 1 | hoppa (håll = högre, igen i luften = dubbelhopp) |
| håll 0+1 | paus (fortsätt eller tillbaka till banorna) |
| banväljaren | 0/1 bläddra, 0+1 starta |

---

# Pico Arcade (`main2.py`)

Startsida med flera spel för **Raspberry Pi Pico 2 (H)** med **Waveshare Pico-LCD-2** (2", 320x240, ST7789).

Liggande spel: **Pong** (mot datorn eller 2 spelare), **Snake**, **Breakout**, **Flappy**, **Tetris**, **Dino** och **Simon**.
Stående spel (vrid skärmen): **Runner**, **Space** och **Stack**.
Dessutom **Klocka** och **Knapptest**. Rekord sparas på Picon i filen `rekord.json`.

## Kom igång med Thonny

1. Installera MicroPython för Pico 2: håll inne BOOTSEL, koppla in USB och välj i Thonny
   *Konfigurera tolk → Installera eller uppdatera MicroPython* (variant: Raspberry Pi Pico 2).
2. Välj tolken **MicroPython (Raspberry Pi Pico)** nere till höger.
3. Öppna `main2.py` och tryck **F5** för att testa.
4. Spara den på Picon som `main2.py` (*Arkiv → Spara som → Raspberry Pi Pico*).
5. Picon startar bara `main.py` av sig själv. Vill du att arcaden startar direkt när Picon får ström,
   lägg en `main.py` på Picon som bara innehåller raden `import main2`.

## 2-knappsläge (bara KEY0 och KEY1)

Om KEY2 och KEY3 inte fungerar (till exempel om de har lossnat) är `TWO_KEYS = True` högst upp i `main2.py`.
Sätt den till `False` när alla fyra knapparna fungerar igen.

| Vad | Så gör du |
|-----|-----------|
| Bläddra i menyn | 0 = föregående, 1 = nästa |
| Välj / starta | tryck 0 och 1 samtidigt (kort) |
| Gå ur ett spel | håll in 0 och 1 i drygt en sekund |
| Spela igen / till menyn (efter game over) | 0 / 1 |
| Pong, 2 spelare | en knapp var: paddeln åker hela tiden, tryck för att vända |
| Breakout | 0/1 styr, bollen skjuts iväg av sig själv (eller 0+1) |
| Tetris | tryck 0/1 = flytta, håll in 0 eller 1 = fall snabbare, 0+1 = vrid |
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

Vill du flytta om knapparna ändrar du konstanterna högst upp i `main2.py`
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
