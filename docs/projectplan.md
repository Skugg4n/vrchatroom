# Projektplan – Pratrummet

## Läge just nu

v1.4 är byggd: rumskodsbuggarna (dator, VR, mobil) är åtgärdade i koden, nätverket återansluter självt och världarna har fått texturer och animationer. Kvar är verifiering på riktig hårdvara (fas 3).

## Fas 1 – Rumskoden ska alltid funka

- [x] Utred varför koden ofta inte visas vid rumsskapande (nätverksberoende UI, se LESSONS #9)
- [x] Visa koden direkt när rummet skapas, oberoende av nätverksstatus
- [x] Se till att koden syns i VR-HUD:en under hela sessionen (LESSONS #10)
- [x] Överlev att mobilen läggs ner: visibilitychange/pageshow/online + ping/pong, automatisk återanslutning (LESSONS #11)
- [ ] Testa hela flödet på riktig hårdvara: skapa rum på dator, gå med från mobil, gå in och ur VR, lägg ner mobilen och ta upp den

## Fas 2 – Snyggare och skönare

- [x] Animationer: idle-andning, huvudrörelser, framåtlutning vid gång
- [x] Material och texturer i världarna, procedurellt utan externa filer
- [x] UI-polish: nätstatus, version, övergångar, hovringseffekter

## Fas 3 – Verifiering

- [ ] Testa på Quest (VR in och ut flera gånger)
- [ ] Testa på mobil (bakgrund och förgrund flera gånger)
- [ ] Testa på dator (muslås, chatt, emotes)
- [x] Uppdatera README, CHANGELOG, LESSONS
