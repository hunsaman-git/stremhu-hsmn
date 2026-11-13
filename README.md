<p align="center">
  <a href="https://stremhu.app">
    <img src="./docs/assets/logo.png" width="100" alt="StremHU Logo" />
  </a>
</p>

<h1 align="center">StremHU Source – Optimized Fork</h1>

<p align="center">
  <b>A StremHU Source nem hivatalos, optimalizált változatának fejlesztése.</b>
</p>

<p align="center">
  Self-hosted streaming szerver, amely közvetlen torrentalapú lejátszást biztosít, saját szerveren futtatva.
</p>

<p align="center">
  ⚡ Teljesítmény &nbsp;•&nbsp; 🔒 Biztonság &nbsp;•&nbsp; 🎬 Streaming &nbsp;•&nbsp; 🐳 Docker
</p>

---

> [!IMPORTANT]
>
> **Ez a projekt az eredeti [s4pp1/stremhu-source](https://github.com/s4pp1/stremhu-source) nem hivatalos forkja.**
>
> A továbbfejlesztés célja a teljesítmény, a stabilitás és a biztonság javítása a meglévő funkciók és adatok kompatibilitásának megőrzésével.
>
> 🚧 **Fejlesztés alatt:** az optimalizációk még nem tekinthetők befejezettnek vagy teljes körűen teszteltnek.

## 🚀 Fejlesztési célok

- ⚡ **Torrent streaming:** hatékonyabb adatkezelés, prioritáskezelés és kisebb erőforrás-igény.
- 🔒 **Biztonság:** munkamenet-kezelés, konfiguráció és hozzáférésvédelem fejlesztése.
- 🎬 **Lejátszás:** HTTP Range-kezelés, videótekerés és hibakezelés javítása.
- 🗄️ **Adatbázis:** SQLite-műveletek és háttérfolyamatok optimalizálása.
- 🐳 **Docker:** karcsúbb konténer, egyszerűbb telepítés és frissítés.
- 🧪 **Minőség:** automatizált tesztek és kompatibilitás-ellenőrzés.

## 📦 Docker

A cél az eredetivel kompatibilis, Dockerben futtatható változat biztosítása.

A saját Docker-image és a részletes telepítési útmutató a fejlesztés és tesztelés után kerül közzétételre.

## ❤️ Eredeti projekt és köszönetnyilvánítás

A projekt az **[s4pp1/stremhu-source](https://github.com/s4pp1/stremhu-source)** nyílt forráskódjára épül.

Köszönet az eredeti fejlesztőnek a StremHU Source létrehozásáért és karbantartásáért! Ez a fork független fejlesztés; nem hivatalos StremHU-kiadás.

<p align="center">
  <a href="https://github.com/s4pp1/stremhu-source">
    <img src="https://img.shields.io/badge/GitHub-Eredeti%20projekt-181717?logo=github&logoColor=white" alt="Eredeti StremHU Source projekt" />
  </a>&nbsp;
  <a href="https://discord.gg/jRSPPY5XaN">
    <img src="https://img.shields.io/badge/Discord-Eredeti%20közösség-5865F2?logo=discord&logoColor=white" alt="StremHU Discord" />
  </a>&nbsp;
  <a href="https://hub.docker.com/r/s4pp1/stremhu-source">
    <img src="https://img.shields.io/badge/Docker-Eredeti%20image-2496ED?logo=docker&logoColor=white" alt="Eredeti Docker-image" />
  </a>
</p>

<p align="center">
  Az eredeti fejlesztő támogatása: <a href="https://ko-fi.com/s4pp1">Ko-fi ☕</a>
</p>

## 🐳 Saját Docker-image (GHCR)

A [GitHub Actions publikálási munkafolyamat](.github/workflows/publish-docker-image.yaml) sikeres tesztek után a GitHub Container Registrybe (GHCR) tölti fel az image-et:

- A `main` ágra kerülő alkalmazás- vagy workflow-változásokat követően automatikusan: `ghcr.io/hunsaman-git/stremhu-hsmn:dev`
- Az **Actions → Publish Docker Image (GHCR) → Run workflow** menüből kézi kiadással: a megadott verziószámú tag, és opcionálisan `latest`

A GHCR a GitHub Actions `GITHUB_TOKEN` jogosultságát használja; külön Docker Hub-fiók vagy token nem szükséges. Az első feltöltés után a csomag láthatóságát a GitHub **Packages** beállításainál ellenőrizni kell (nyilvános letöltéshez a csomag is legyen publikus).

> [!WARNING]
>
> A fork jelenleg **fejlesztés alatt áll**. A saját Docker-image sikeres elkészítése önmagában még nem jelent tesztelt optimalizációt. Éles szerveren csak megfelelő mentés és külön tesztelés után érdemes használni.

## 📄 Licenc

A forráskód az eredeti projekttel összhangban **GNU GPL v3.0** licenc alatt érhető el. Lásd a [LICENSE](LICENSE) fájlt. Az eredeti szerzői jogi és licencmegjelöléseket megőrizzük.

---

<p align="center"><sub>Nem hivatalos, közösségi fork • Not affiliated with the official StremHU project</sub></p>
