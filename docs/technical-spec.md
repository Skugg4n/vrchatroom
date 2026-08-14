# Teknisk spec – Pratrummet

## Arkitektur

- En enda fil: `pratrummet.html` (ca 1420 rader). Ingen byggkedja, ingen server, inga externa mediefiler.
- Three.js **r128** (låst version, se LESSONS #1) och PeerJS via CDN.
- Kräver https för WebXR och peer-to-peer. Publiceras via Netlify: https://vrchatroom.netlify.app/ (Jacks konto). Koden ligger på GitHub: https://github.com/Skugg4n/vrchatroom
- `index.html` är bara en omdirigering till `pratrummet.html`.

## Nyckeldelar i koden

- `buildWorld(id, seed)` bygger världarna med seedad slump (mulberry32) så alla spelare får identisk värld.
- Avatarer byggs procedurellt av lådor och sfärer. Ansiktet pekar mot +z, kameran mot -z, därav `+ Math.PI` vid nätverks-yaw (LESSONS #3).
- Nätverk: värden är auktoritet, gäster pratar bara med värden som vidarebefordrar. Peer-id byggs på en fyrteckenskod. Max 5 spelare.
- Positionsuppdateringar var 66:e ms (ca 15 Hz), mottagare interpolerar med lerp.
- Ljud genereras med WebAudio, inga ljudfiler.

## Prestandakrav (Quest 2)

- Exakt tre ljuskällor hela tiden, aldrig fler eller färre (undviker shaderomkompilering)
- InstancedMesh för träd, blommor och staketstolpar
- `setFramebufferScaleFactor(0.9)` före sessionen, `fixedFoveation = 1` efter
- Inga skuggkartor, antialias av, pixelRatio max 1,5

## Arbetsregler

- Läs LESSONS.md innan felsökning, regelchecklistan där gäller alltid
- Logga ändringar i CHANGELOG.md med version, datum och varför
- Versionsnumret ska synas diskret i UI:t och bumpas vid varje ändring
- Kommentera komplex logik på engelska i koden, UI-texter på svenska med å ä ö
