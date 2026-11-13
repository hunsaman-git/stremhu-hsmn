# Forráskód-audit és fejlesztési terv

Kiinduló commit: `2eb834764da81fc52309c7b6e875d6fcfb3eaa34`.
Az audit a felhős fejlesztői példányban készül; az éles XPEnology gépet,
adatbázisát, konténereit és beállításait nem érinti. Ez nem tanúsított
penetrációs teszt, és nem igazolja a külső torrentoldalak működését.

## Hibajegyzék a javítások előtt

| ID | Súlyosság | Bizonyíték, kiváltó ok és hatás | Javítás / ellenőrzés |
| --- | --- | --- | --- |
| SEC-01 | Kritikus | `config.py`: nyilvános `stremhu-source` alapkulcs; a `main.py` SessionMiddleware ezzel ír alá. Ismert felhasználóazonosítóval hamisítható munkamenet; a stream tokenek kulcsa is ismert. | Telepítésenként véletlen, a meglévő data könyvtárban tartósított kulcs; explicit SESSION_SECRET megőrzése; párhuzamos indulás és újraindítás tesztje. |
| HTTP-01 | Magas | `StreamService._parse_range_header`: `bytes=abc`, `bytes=x-y` ValueError kivételt dob, amelyből HTTP 500 lesz. | Teljes szintaktikai ellenőrzés, determinisztikus 416 és `Content-Range: bytes */size`; paraméterezett negatív tesztek. |
| HTTP-02 | Közepes | `bytes=5-999`, 10 bájtos fájlon: 416, pedig a tartomány végét 9-re kell korlátozni. Üres fájl és suffix szélsőértékek nincsenek tesztelve. | RFC 9110 szerinti korlátozás; teljes/suffix/nyitott tartomány, üres fájl, GET/HEAD tesztek. Több tartomány továbbra sem támogatott. |
| RELAY-01 | Magas | `get_piece_data` shieldeli a közös feladatot, de az utolsó váró lemondása után sem szünteti meg. Hiányzó darabnál a task és future korlátlanul megmaradhat. | Várószámlálás, utolsó várónál lemondás; az egyik váró bontása továbbra se szakítsa meg a másikat. |
| RELAY-02 | Közepes | `_fetch_piece_once`: `have_piece/read_piece` a try/finally előtt fut; szinkron libtorrent hiba után a pending future bent marad. | A teljes regisztrált olvasást fedő finally és hibát dobó fake handle teszt. |
| RELAY-03 | Közepes | `Stream._stream_inner` külön taskra bízza a destroy-t; a stream még legalább 250 ms-ig aktívként látszik. `get_deadlines` a worker szálban élő dictet iterál. | Determinisztikus, azonnali takarítás és listás pillanatfelvétel; bontás, kivétel és nem darabhatáron kezdődő fájl tesztje. |
| SEC-02 | Magas | `authorize_pairing_code` LINKED állapotot is felülír, így egy másik bejelentkezett felhasználó ugyanazt az aktív kódot újra saját magához kapcsolhatja. | Egyszeri, feltételes SQL UPDATE PENDING állapotra; ismételt és párhuzamos jóváhagyás tesztje, séma-változtatás nélkül. |
| SEC-03 | Közepes | Párosító kód `random.choices` útján készül; a generátor nem kriptográfiai célra való. | `secrets.choice`; a négyjegyű protokoll megtartása. Rate limit külön tervezendő. |
| SEC-04 | Közepes | `main.py`: a cookie max_age ezerszerese a komment szerinti 30 napnak (másodperc helyett ezredmásodperc). | 30 nap másodpercben, a tényleges Set-Cookie ellenőrzésével. |
| DB-01 | Közepes | `TorrentFilesRepository.touch/find_list`: azonosítónként OR ág; 1100 azonosítóval SQLite expression tree limit túlléphető. | Összetett kulcsokra tuple IN és korlátozott méretű batch; 1100 rekordos teszt, meglévő throttle/lock tesztek megtartása. |
| DB-02 | Megfigyelés | A stream router sessionje a tracker hálózati várakozása alatt is él; több service ugyanazt a sessiont to_thread hívásokban használja. Nincs ebben az auditban reprodukált korrupció. | Külön későbbi tranzakció-élettartam refaktor, csatlakozásszám- és lockmérés után. Ne vezessünk be vaktában timeout/WAL/sémamódosítást. |
| SEC-05 | Tervezési kockázat | Login/pair init/verify nincs alkalmazásszintű rate limittel védve; négyjegyű kódterület kicsi. | Proxy- és alkalmazásszintű korlát tervezése, megosztott IP és Kodi polling kompatibilitásának mérésével. |
| SEC-06 | Tervezési kockázat | Tracker jelszó, cookie, TOTP és hálózati privát kulcs az SQLite-ban található. A helyi tanúsítvány publikus privát kulcsot használhat. | Titoktárolás és TLS modell külön migrációs tervvel; a meglévő mentések és helyi kliensek miatt ne cseréljük hallgatólagosan. |
| SEC-07 | Vizsgálandó | Első admin regisztráció count-then-create; párhuzamos első regisztráció versenyhelyzet lehet. Stream token nincs felhasználóhoz/lejárathoz kötve; lejátszási limit ellenőrzés és foglalás külön történik. | Több kéréses integrációs reprodukció szükséges; API- és tokenkompatibilitás miatt külön változáscsomag. |
| NET-01 | Bizonyított blokkoló műveletek | `ssl/service.py`: szinkron DNS resolver és ACME kliens async metódusokban. | Későbbi worker szálra szervezés mockolt ACME/DNS tesztekkel; valós DNS/ACME itt nincs meghívva. |
| CLI-01 | Alacsony | Négy felesleges TypeScript assertion a preferencia-űrlapokon; az ESLint hibával kilép. | Eltávolítás, build/tsc és ESLint újrafuttatása. |
| DOCKER-01 | Fejlesztési lehetőség | Node stage a teljes clientet másolja npm ci előtt, runtime apt upgrade változó eredményű; dev eszközök a runtime requirements-ben. | Build cache és runtime méret külön mérendő; ebben a javításban a Dockerfile, portok, data útvonal és CMD változatlan. |
| DOCKER-02 | Ellenőrzési igény | GHCR workflow amd64/arm64 buildet és push-t futtat mainen. | Csak helyi build/smoke, ha a helyi daemon elérhető; nincs image push, main merge vagy éles telepítés. arm64 ellenőrzés külön jelölendő. |

## Fejlesztési sorrend és elfogadási feltételek

1. Külön fejlesztési ág és az alapállapot tesztjei. A teljes backend/frontend
   fájllista, routerek jogosultságai, ORM/migrációk, tracker adapterek,
   kliens belépési és API útvonalak, Docker és CI áttekintése. A részletes
   kézi elemzés fókusza a fent nevezett kritikus végrehajtási útvonal.
2. Először regressziós tesztek HTTP-01/02, RELAY-01/02/03, SEC-01/02/04,
   DB-01 esetekre; igazolni, hogy a jelenlegi kódon hibáznak.
3. Kis, egymástól elkülönülő javítások. Nincs adatbázis-séma vagy Alembic
   revision változás; meglévő környezeti változók, útvonalak és torrent
   prioritási/seedelési beállítások megmaradnak.
4. Teljes pytest/snapshot, Ruff, Basedpyright, kliens build/tsc/lint;
   alkalmazás smoke és adatbázis-migráció külön ideiglenes adatbázison.
   Docker csak a felhő saját unix socketén, soha nem távoli daemonon.
5. PR a forkba, ellenőrzési eredményekkel és a fennmaradó kockázatokkal.
   Nincs automatikus merge, kiadás, környezet-publikálás vagy XPEnology művelet.

## Kompatibilitási döntések

- Explicit `SESSION_SECRET` változatlan; az automatikus kulcs a meglévő
  `data/system` tárolás része lesz. A korábbi nyilvános alapkulcs kiváltása
  szükségszerűen érvényteleníti az azzal aláírt cookie-kat és stream URL-eket;
  új bejelentkezés és új stream lista szükséges. A felhasználók, API-kulcsok,
  jelszavak, torrentek és adatbázisséma megmaradnak. A generált kulcsot a data
  könyvtárral együtt kell menteni. Hibás/hiányzó írási jogosultságnál nincs
  visszaesés ismert kulcsra.
- Nincs új kötelező env változó vagy Docker volume. Egy szándékosan beállított
  gyenge SESSION_SECRET továbbra is az üzemeltető által kezelt kockázat.
- A többes Range kezelésének bevezetése és a token formátum cseréje külön
  interoperabilitási munka. Hálózati teljesítményjavulást mérés nélkül nem állítunk.

## Ellenőrzési napló

A tényleges futtatási eredmények a javítások után kerülnek ebbe a szakaszba.
