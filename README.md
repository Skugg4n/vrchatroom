# PRATRUMMET

Ett socialt VR-chattrum där man gör sin egen karaktär och hänger med upp till fyra kompisar. Allt ligger i en enda HTML-fil (`pratrummet.html`, ca 1420 rader) utan byggsteg, server eller externa mediefiler.

Kräver https för att WebXR och peer-to-peer ska funka, till exempel GitHub Pages. Öppnad som lokal fil blir det bara platt läge utan multiplayer.

## Så här ser det ut

**Startskärmen** är lila och blå med titeln i spärrad versal och två knappar: SKAPA RUM och GÅ MED I RUM.

**Karaktärsskaparen** har en roterande 3D-figur i en ruta som man snurrar genom att dra. Under den ligger valen som färgprickar och pillerknappar, och längst ned ett namnfält.

**Världen** visas i förstaperson. Uppe till vänster ligger rumskod, spelarräknare och tangenthjälp. Uppe till höger har värden tre knappar för att byta värld. Nere till vänster ligger chattloggen med emote-raden och chattfältet. Nere till höger sitter VR-knappen.

**Avatarerna** är klossiga figurer i klara färger med rörliga armar och ben som andas och rör sig lite även när de står stilla, namnskylt ovanför huvudet och vita pratbubblor när de säger något. Emojis flyter upp och tonar bort när någon gör en emote.

## Karaktären

- 10 färger
- 3 huvudformer: rund, kub, ägg
- 4 ögontyper: prickar, stora, sömniga, solglasögon
- 5 hattar: ingen, keps, hög hatt, toppluva, krona
- 4 accessoarer: ingen, ryggsäck, slips, halsduk
- Namn på max 12 tecken

Figuren byggs procedurellt av lådor och sfärer i stället för en färdig 3D-modell, vilket gör att alla kombinationer funkar direkt och att filen förblir liten.

## Världarna

Värden väljer världen och kan byta när som helst. Alla byggs av `buildWorld(id, seed)` med en seedad slumpgenerator (mulberry32), så när värden skickar sitt frö får alla exakt samma värld.

| Värld | Innehåll |
|---|---|
| Vita rummet | Vitt med ljust rutnät, mjuk golvvinjett och dimma, 32x32 meter |
| Stökiga rummet | Trägolv och tapet (procedurella texturer), soffa med matta, bord med pizzakartong, TV-bänk, fönster med spröjs, bokhylla med slumpade böcker och 26 utspridda skräpföremål |
| Parken | Grästextur, 14 träd i två gröna nyanser, 75 blommor, damm med sandkant, två bänkar och staket, 36x36 meter |

Alla texturer ritas i koden på små canvas-element (max 256 pixlar), fortfarande utan externa filer.

## Kontroller

**Dator**: klicka i världen för att låsa musen, WASD eller piltangenter för att gå, Shift för att springa, T för chatt (Enter skickar, Escape avbryter), E för emotepanelen och sedan 1 till 5.

**Pekskärm**: vänstra halvan av skärmen är en virtuell spak, dra på högra halvan för att titta. Chattfältet och emote-knapparna ligger alltid framme.

**VR**: vänster spak går (relativt vart du tittar), höger spak snäppvrider 45 grader, greppknappen springer. Emotes ligger på A (👋), B (❤️), X (😂), Y (🎉) och vänster spak-klick (💃). Är du värd byter du värld med höger spak-klick. HUD:en sitter på vänster handled med rumskod, spelarantal, knappkarta och de fem senaste meddelandena.

## Vad andra ser av dig

Var 66:e millisekund (ca 15 Hz) skickas position, kroppsvridning, blickvinkel, rörelseflagga och i VR även handkontrollernas position relativt huvudet. Mottagarna interpolerar mjukt (lerp cirka 10 per sekund) mellan uppdateringarna, så det ser jämnt ut trots den låga frekvensen.

Det gör att alla ser vart du tittar (huvudet lutar), om du går (ben och armar pendlar) och, om du är i VR, ungefär var dina händer är eftersom armarna riktas mot kontrollerna.

## Multiplayer

PeerJS med deras gratis förmedlingstjänst, ingen egen server. Värden skapar ett peer-id byggt på en fyrteckenskod och är auktoritet: alla gäster pratar bara med värden, som vidarebefordrar till övriga. Max 5 spelare. Sena anslutningar släpps in så länge det finns plats.

Rumskoden skapas lokalt och visas alltid direkt, oavsett nätverk. Nätverksstatusen står i klartext i topplisten och på VR-handleden: online, kopplar upp, återansluter eller offline. Vid uppstart går värden in i världen direkt och nätverket kopplas upp i bakgrunden, så spelet fungerar även om förmedlingstjänsten är seg eller nere.

Tappade anslutningar läker sig själva: upptagen kod provas om automatiskt, värden återtar samma kod efter avbrott, och gäster återansluter i bakgrunden utan att kastas ut ur världen. När mobilen läggs ner och tas upp verifieras anslutningen med ping/pong (`visibilitychange`/`pageshow`/`online`) och kopplas upp igen vid behov. Värden städar bort döda anslutningar så att spöken inte upptar platser. Om PeerJS-biblioteket inte gick att ladda provas två alternativa CDN:er.

## Prestanda

Byggt för att klara Quest 2:

- Exakt tre ljuskällor hela tiden, aldrig fler eller färre, så shaders inte kompileras om mitt i spelet. Lampor och fönster är emissiva material i stället för ljus.
- Träd, blommor och staketstolpar är InstancedMesh, alltså ett anrop per grupp i stället för hundratals.
- `setFramebufferScaleFactor(0.9)` före sessionen och `fixedFoveation = 1` efter.
- Inga skuggkartor, antialias av, pixelRatio max 1,5.
- Ljud genereras med WebAudio, inga ljudfiler.

## Kända begränsningar

- Förmedlingstjänsten är gratis och delad, så anslutningen kan ibland ta några sekunder.
- Vissa strikta brandväggar och mobilnät blockerar peer-to-peer helt.
- Ingen röstchatt, bara text och emotes.
- Ingen kollision mellan spelare, man kan gå igenom varandra.
- Byter värden värld flyttas alla till mitten igen.
- Webbläsare vägrar låsa musen igen under drygt en sekund efter att låset släppts, så ibland behövs ett extra klick.

## Filer

| Fil | Innehåll |
|---|---|
| `pratrummet.html` | Hela spelet |
| `README.md` | Det här dokumentet |
| `LESSONS.md` | Buggarna vi hittade, orsak och regel |
| `CHANGELOG.md` | Versionshistorik |
| `TODO.md` | Avbockad arbetslista |
