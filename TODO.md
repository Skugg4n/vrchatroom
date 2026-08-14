# TODO – Pratrummet

Arbetslista för nästa omgång. Buggarna först, sedan förbättringar.

## Buggar (prio 1)

- [x] **Rumskoden dyker ofta inte upp när man skapar rum.** Fixad i v1.4: koden skapas lokalt och visas alltid direkt, nätverksstatusen står i klartext i topplisten, och PeerJS provas från alternativa CDN:er om första laddningen misslyckas. Se LESSONS #9.
- [x] **VR: rumskoden försvinner när man går in i faktisk VR.** Fixad i v1.4: alla HUD-ytor ritas om ihop via `refreshHUD()`, handleds-HUD:en visar kod + nätstatus hela sessionen och fästs med fallback om vänster kontroll saknar handedness. Se LESSONS #10.
- [x] **Mobil: rumskoden försvinner när man lägger ner mobilen.** Fixad i v1.4: `visibilitychange`/`pageshow`/`online` verifierar anslutningen med ping/pong och återansluter automatiskt. Gäster stannar i världen i stället för att kastas ut, värden återtar samma rumskod. Se LESSONS #11.

## Förbättringar (prio 2)

- [x] Bättre animationer: idle-andning, huvudrörelser, framåtlutning vid gång (v1.4)
- [x] Bättre texturer och material: procedurella canvas-texturer i alla tre världar, fortfarande utan externa filer (v1.4)
- [x] Allmän polish: nätstatus i UI, versionsnummer, skärmövergångar, hovringseffekter, emoji-skurar med drift (v1.4)

## Kvar att göra

- [ ] Verifiera v1.4 på riktig hårdvara: Quest (VR in/ut flera gånger), mobil (lägg ner och ta upp), två spelare samtidigt
- [ ] Eventuellt: ljudpolish (ambient), fler emotes, röstchatt är fortfarande medvetet bortvald

## Regler

- Allt ska fortsatt ligga i en enda HTML-fil utan byggsteg
- Three.js r128 är låst av kravspecen, se LESSONS #1
- Prestandakraven för Quest 2 i README gäller (exakt tre ljuskällor, InstancedMesh, inga skuggkartor)
- Läs LESSONS.md innan felsökning, uppdatera den med nya lärdomar
- Logga alla ändringar i CHANGELOG.md och bumpa versionen som visas i UI:t
