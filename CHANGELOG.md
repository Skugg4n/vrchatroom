# CHANGELOG – Pratrummet

## v1.4 – 2026-08-14

### Buggfixar
- Rumskoden skapas lokalt och visas alltid direkt, den rensas aldrig av nätverksfel (TODO bugg 1, LESSONS #9)
- Nätverksstatus i klartext i topplisten och på handleds-HUD:en: online, kopplar upp, återansluter, offline
- VR: handleds-HUD:en ritas om vid alla ändringar och visar alltid aktuell kod, fästs på höger hand eller första kontrollen om vänster saknas (TODO bugg 2, LESSONS #10)
- Mobil: rummet överlever att mobilen läggs ner. Vid visibilitychange/pageshow/online verifieras anslutningen med ping/pong och återansluts automatiskt, gäster kastas aldrig ut till startskärmen (TODO bugg 3, LESSONS #11)
- Värden städar bort döda gästanslutningar (mobiler som somnat) så spöken inte blockerar platser
- PeerJS provas från två alternativa CDN:er om första laddningen misslyckades
- Kvarlämnat uttryck med lika grenar i bokhyllan borttaget (regeln från LESSONS #6)

### Funktioner och polish
- Idle-animation: andning, små huvudrörelser, mjuk framåtlutning vid gång
- Procedurella texturer utan externa filer: trägolv, tapet, matta och fönsterkarm i stökiga rummet, gräs och sandkant runt dammen i parken, mjuk vinjett i vita rummet
- Trädkronor i två gröna nyanser
- Emoji-skurar driver åt sidan och växer medan de tonar bort
- Versionsnumret syns diskret på startskärmen och i topplisten
- Mjuka övergångar mellan skärmar, hovringseffekter på knappar och världskort

## v1.3 – 2026-08-14

### Funktioner
- Muslås på dator, blicken styrs av `movementX/Y` i stället för att dra
- T öppnar chatten, Enter skickar och låser musen igen, Escape avbryter
- E öppnar emotepanelen, 1 till 5 skickar emote
- Chattfält och emote-rad är dolda på dator, alltid framme på pekskärm
- Tangenthjälp i topplisten
- Maxantalet spelare höjt från 3 till 5

## v1.2 – 2026-08-14

### Buggfixar
- Värden går in i världen direkt, nätverket kopplas upp i bakgrunden (löser total frysning vid rumsskapande, se LESSONS #4)
- VR-knappen visas så snart webbläsaren har WebXR i stället för att vänta på asynkron koll (LESSONS #5)
- Tydliga fel i klartext vid saknat nätverksbibliotek, seg förmedlingstjänst och nekad VR-session
- Automatiska omförsök vid upptagen rumskod, automatisk återanslutning vid tapp
- Global felfångare som visar fel som ruta i stället för tyst frysning

## v1.1 – 2026-08-14

### Funktioner
- Emotes: 👋 ❤️ 😂 🎉 💃 med emoji-skur och armanimationer
- Blickriktning skickas över nätverket, huvudet lutar på avatarerna
- VR-spelares handpositioner skickas, avatarens armar riktas mot kontrollerna
- Karaktären snurras genom att dra i stället för automatiskt

### Buggfixar
- VR-start fungerar (LESSONS #1)
- Gångriktning korrekt efter vridning, både VR och platt (LESSONS #2)
- Avatarerna vänds rätt håll (LESSONS #3)
- Bokhyllans mått rättade (LESSONS #6)
- Blickriktningen bevaras när man lämnar VR

## v1.0 – 2026-08-14

Första versionen: karaktärsskapare, tre världar, PeerJS-multiplayer med värden som auktoritet, textchatt med pratbubblor, VR med dolly-rigg och handleds-HUD, platt läge och pekskärmsstöd.
