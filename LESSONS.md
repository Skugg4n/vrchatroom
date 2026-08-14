# LESSONS – Pratrummet

Alla buggar från byggandet, med rotorsak och en regel att ta med sig.

### #1 – VR startade aldrig

**Problem:** Knappen STARTA I VR gjorde ingenting på Quest, utan bara ett felmeddelande.
**Orsak:** Koden gjorde `renderer.xr.setSession(session).then(...)`. I Three.js r128 returnerar `setSession` ingenting alls, så `.then` anropades på `undefined` och hela funktionen kastade ett fel innan sessionen hann kopplas in. I senare versioner av Three.js returnerar den ett promise, vilket gör felet lätt att missa.
**Lärdom:** API:er ändras mellan versioner, och r128 är låst av kravspecen. Anta aldrig att en metod returnerar ett promise utan att kontrollera just den versionen.
**Regel:** Kedja aldrig `.then` på ett Three.js-anrop i r128 utan att först ha verifierat returvärdet.

### #2 – Man gick åt fel håll efter att ha vridit sig

**Problem:** Så länge man tittade rakt fram funkade rörelsen, men efter en vridning gick man snett eller spegelvänt.
**Orsak:** Teckenfel i rotationsmatematiken. Rätt rotation av en riktningsvektor kring y är `x' = x·cos + z·sin` och `z' = z·cos - x·sin`. Koden hade tecknen omkastade, vilket speglar riktningen i stället för att rotera den. Felet syns inte vid vridning 0 grader, eftersom sinus då är noll.
**Lärdom:** Ett teckenfel som är osynligt i utgångsläget hittas bara om man testar efter att ha vridit sig, både i VR och platt läge.
**Regel:** Testa alltid rörelse efter minst 90 graders vridning, aldrig bara rakt fram.

### #3 – Alla avatarer var bakvända

**Problem:** Alla andra spelare visade ryggen även när de tittade rakt på en.
**Orsak:** Avatarens ansikte byggs i positiv z-riktning, medan en kamera i Three.js tittar i negativ z-riktning. Nätverkets yaw applicerades rakt av på avataren, vilket blev exakt 180 grader fel.
**Lärdom:** Modellens framåtriktning och kamerans framåtriktning är två olika konventioner som måste översättas explicit.
**Regel:** Lägg till `+ Math.PI` när nätverkets blickriktning appliceras på en modell byggd mot +z.

### #4 – Allt frös när man skapade ett rum

**Problem:** En kompis klickade på en värld på datorn och sedan hände ingenting alls: ingen rumskod, ingen bild, ingen rörelse.
**Orsak:** `enterWorld()` anropades inne i PeerJS `open`-callback. Svarade inte förmedlingstjänsten kom man aldrig in i världen, och eftersom startskärmen redan var gömd fanns varken HUD eller felmeddelande att titta på. Det såg ut som en total krasch fast spelet bara väntade.
**Lärdom:** Nätverk är opålitligt och får aldrig blockera det som fungerar utan nätverk. Ett väntläge utan synlig återkoppling är omöjligt att felsöka för användaren.
**Regel:** Släpp in spelaren i världen först, koppla upp nätverket i bakgrunden och skriv alltid ut nätverksstatus i klartext.

### #5 – VR-knappen fanns men syntes aldrig

**Problem:** Ovanpå bugg #1 visades knappen inte ens när VR fanns.
**Orsak:** Två saker. Knappen visas först inne i världen, och på grund av #4 kom värden aldrig dit. Dessutom styrdes synligheten av `navigator.xr.isSessionSupported()`, som är asynkron. Hann man in i världen innan svaret kom var flaggan fortfarande falsk och knappen förblev dold för alltid.
**Lärdom:** Ett asynkront svar som styr UI måste också uppdatera UI:t när det kommer, inte bara sätta en variabel.
**Regel:** Visa VR-knappen optimistiskt så snart `navigator.xr` finns, och dölj den först om kollen faktiskt svarar nej.

### #6 – Böckerna stod utanför bokhyllan

**Problem:** Bokhyllan i stökiga rummet hade böcker som svävade bredvid sig.
**Orsak:** Bredd och djup var förväxlade i geometrin, plus en meningslös rest av ett rotationsuttryck (`-Math.PI/2 ? 0 : 0`) som alltid blev noll. Hyllan stod alltså 90 grader fel mot böckerna.
**Lärdom:** Slarviga kvarlämnade uttryck döljer verkliga fel, och en villkorsoperator som alltid ger samma svar är alltid en bugg.
**Regel:** Rensa bort halvfärdiga uttryck direkt, skriv aldrig ett villkor med samma värde i båda grenarna.

### #7 – Snurrande karaktär gick inte att granska

**Problem:** Figuren i karaktärsskaparen snurrade automatiskt, så man kunde inte titta på ryggen eller hatten i lugn och ro.
**Orsak:** Automatisk rotation valdes för att den ser levande ut, utan att tänka på att syftet med rutan är granskning, inte dekoration.
**Lärdom:** Rörelse som ser trevlig ut kan stå i vägen för funktionen.
**Regel:** Låt användaren styra kameran där syftet är att granska något.

### #8 – Muslås försvann efter varje meddelande

**Problem:** Efter att ha skickat ett chattmeddelande låstes musen inte alltid tillbaka.
**Orsak:** Webbläsare har en inbyggd spärr på drygt en sekund innan `requestPointerLock` får anropas igen efter att låset släppts. Anropet avvisas tyst, och utan `.catch` syns inget i konsolen heller.
**Lärdom:** Detta går inte att koda bort, bara att hantera.
**Regel:** Fånga alltid ett avvisat `requestPointerLock` och låt ett klick i världen låsa om.

### #9 – Rumskoden dök ofta inte upp

**Problem:** Rummet skapades men koden visades inte, så ingen kunde gå med. Kunde även försvinna efter att den visats.
**Orsak:** Två vägar. Om PeerJS-skriptet aldrig laddats (seg eller blockerad CDN) avbröt `createHostPeer` innan koden ens slumpats fram. Och vid nätverksfel innan `open` nollställdes `roomCode=''`, så en kod som redan stod på skärmen raderades. Koden är ett lokalt värde men var i praktiken styrd av nätverkshändelser.
**Lärdom:** Ett värde som kan skapas lokalt ska aldrig vänta på eller raderas av nätverket. Nätverket får bara påverka en separat statusrad.
**Regel:** Härled aldrig UI-state från nätverkshändelser när värdet kan skapas lokalt. Visa nätstatus separat i klartext.

### #10 – VR-HUD:en visade streck i stället för koden

**Problem:** Koden syntes i platt läge men handleds-HUD:en i VR visade `KOD: –`.
**Orsak:** HUD-canvasen ritades bara om i `peer.on('open')`. Var nätet segt hann man in i VR innan dess, och ingen ritade om. Topplisten och handleden uppdaterades från olika ställen och kunde visa olika saker. Dessutom fästes panelen bara om en kontroll rapporterade `handedness === 'left'`.
**Lärdom:** Samma data på två HUD-ytor måste ritas om från ett enda ställe, annars glider de isär.
**Regel:** En gemensam `refreshHUD()` för alla HUD-ytor, anropad vid varje ändring. Fäst VR-paneler med fallback om handedness saknas.

### #11 – Mobilen tappade rummet när den lades ner

**Problem:** Skärm av eller app i bakgrunden en stund, och när man kom tillbaka var koden borta och man stod på startskärmen.
**Orsak:** När sidan suspenderas dör WebSocket och WebRTC ofta tyst, ibland utan `close`-event. Gästens `close`-hanterare anropade `leaveToStart()` som nollställde allt och visade startskärmen. Ingen lyssnade på `visibilitychange`, och en anslutning som såg öppen ut kunde vara död.
**Lärdom:** Efter en suspendering går det inte att lita på att en "öppen" anslutning lever. Att kasta ut spelaren är det sämsta möjliga svaret på ett nätverkstapp.
**Regel:** Lyssna på `visibilitychange`, `pageshow` och `online`. Verifiera anslutningen med ping/pong efter uppvaknande. Stanna i världen och återanslut i bakgrunden, kasta aldrig ut spelaren.

## Regelchecklista

- [ ] Kedja aldrig `.then` på Three.js r128-anrop utan att verifiera returvärdet
- [ ] Testa rörelse efter minst 90 graders vridning
- [ ] Lägg till `+ Math.PI` när nätverkets yaw appliceras på en modell byggd mot +z
- [ ] Låt aldrig nätverket blockera inträdet i världen, skriv ut status i klartext
- [ ] Uppdatera UI när asynkrona funktionskollar svarar
- [ ] Rensa halvfärdiga uttryck, skriv aldrig villkor med lika grenar
- [ ] Låt användaren styra kameran vid granskning
- [ ] Fånga avvisat `requestPointerLock`
- [ ] Härled aldrig UI-state från nätverkshändelser när värdet kan skapas lokalt
- [ ] Rita om alla HUD-ytor från en gemensam refresh-funktion
- [ ] Verifiera anslutningar med ping/pong efter suspendering, kasta aldrig ut spelaren vid nätverkstapp
