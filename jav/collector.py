import re
from asyncio import gather
from dataclasses import dataclass
from typing import Dict, NoReturn
from bs4 import BeautifulSoup
from enlighten import get_manager

from . import Database, Table
from .helper.sesion import AsyncNetRequests

manager = get_manager()


@dataclass(frozen=True)
class regex:
    title = re.compile(r"Title:;([^;]+)")
    genre = re.compile(r"Genre\(s\):;([^;]+)")
    series = re.compile(r"Series:;([^;]+)")
    studio = re.compile(r"Studio:;([^;]+)")
    label = re.compile(r"Label:;([^;]+)")
    director = re.compile(r"Director:;([^;]+)")
    dvd = re.compile(r"DVD ID:;([^;]+)")
    content = re.compile(r"Content ID:;([^;]+)")
    release = re.compile(r"Release Date:;([^;]+)")
    duration = re.compile(r"Runtime:;([^;]+)")


def inclas(name: str) -> dict:
    return {"class": name}


class Collector(Database):
    def __init__(self, dbpath: str, wal: bool = False) -> None:
        super().__init__(dbpath, wal=wal)
        self.net = AsyncNetRequests()
        self.actres = Table("actres", self.db)
        self.video = Table("video", self.db)
        self.studio = Table("studio", self.db)
        self.label = Table("label", self.db)
        self.genre = Table("genre", self.db)
        self.series = Table("series", self.db)
        self.director = Table("director", self.db)
        self.actres_r = Table("rf_actres", self.db)
        self.genre_r = Table("rf_genre", self.db)
        self.re = regex()

    async def soup(self, url) -> None | BeautifulSoup:
        try:
            resp = await self.net.get(url)
        except Exception:
            # return None
            raise Exception(f"{url} error")

        return BeautifulSoup(resp.content, "lxml")

    async def analize(self, url) -> Dict:
        soup = await self.soup(url)

        data = soup.find("div", inclas("movietable")).find_all("td")
        text = ";".join([d.text.strip() for d in data])
        actres = soup.find_all("div", {"class", "flex-item-idol"})
        thumb = soup.find("td", {"class": "moviepostermobile"})

        return {
            "title": title.group(1) if (title := self.re.title.search(text)) else None,
            "genre": [a.strip() for a in genre.group(1).split(",")]
            if (genre := self.re.genre.search(text))
            else None,
            "series": series.group(1)
            if (series := self.re.series.search(text))
            else None,
            "studio": studio.group(1)
            if (studio := self.re.studio.search(text))
            else None,
            "label": label.group(1) if (label := self.re.label.search(text)) else None,
            "director": direc.group(1)
            if (direc := self.re.director.search(text))
            else None,
            "dvd_id": dvd.group(1) if (dvd := self.re.dvd.search(text)) else None,
            "content_id": cont.group(1)
            if (cont := self.re.content.search(text))
            else None,
            "release": real.group(1)
            if (real := self.re.release.search(text))
            else None,
            "duration": dur.group(1)
            if (dur := self.re.duration.search(text))
            else None,
            "actres": [
                (a.find("div", {"class": "idol-name"}).text.strip(), a.img.get("src"))
                for a in actres
            ]
            if actres
            else None,
            "thumbnail": thumb.img["src"] if thumb else None,
        }

    async def record(self, data: dict) -> NoReturn:
        if "studio" in data:
            data["studio"] = (
                ids.id
                if (ids := self.studio.get_one(["id"], name=data["studio"]))
                else self.studio.insert(name=data["studio"])
            )
        if "series" in data:
            data["series"] = (
                ids.id
                if (ids := self.series.get_one(["id"], name=data["series"]))
                else self.series.insert(name=data["series"])
            )
        if "label" in data:
            data["label"] = (
                ids.id
                if (ids := self.label.get_one(["id"], name=data["label"]))
                else self.label.insert(name=data["label"])
            )
        if "director" in data:
            data["director"] = (
                ids.id
                if (ids := self.director.get_one(["id"], name=data["director"]))
                else self.director.insert(name=data["director"])
            )

        if genres := data.pop("genre", None):
            for idx, genre in enumerate(genres):
                genres[idx] = (
                    ids.id
                    if (ids := self.genre.get_one(["id"], name=genre))
                    else self.genre.insert(name=genre)
                )
        if actreses := data.pop("actres", None):
            for idx, ac in enumerate(actreses):
                actreses[idx] = (
                    ids.id
                    if (ids := self.actres.get_one(["id"], name=ac[0]))
                    else self.actres.insert(name=ac[0], thumbnail=ac[1])
                )

        idVideo = self.video.insert(data)

        if genres:
            for genre in genres:
                self.genre_r.insert(vid=idVideo, gid=genre)

        if actreses:
            for actres in actreses:
                self.actres_r.insert(vid=idVideo, aid=actres)

        print(f"[SUCESS][{data['dvd_id']}] {data['title'][0:20]}...")

    async def insert_furl(self, url: str) -> NoReturn:
        data = await self.analize(url)
        for k, v in list(data.items()):
            if not v:
                del data[k]

        if "dvd_id" not in data and "content_id" in data:
            c = re.search(r"([a-zA-Z]+)([0-9]+)", data["content_id"])
            c1 = c.group(0)
            c2 = c.group(1)
            if c2.startswith("0"):
                if len(c2) < 3:
                    c2 = f"{0 * (3-len(c2))}{c2}"
                elif len(c2) > 3:
                    c2 = str(int(c2))
            data["dvd_id"] = f"{c1.upper()}-{c2}"

        elif "content_id" not in data and "dvd_id" in data:
            data["content_id"] = "".join(data["dvd_id"].split("-"))

        if "dvd_id" not in data:
            data["dvd_id"] = "-no code-"

        if "title" not in data:
            data["title"] = "-no title-"

        cont_orcode = (
            {"content_id": data["content_id"]}
            if data.get("content_id")
            else {"dvd_id": data.get("dvd_id")}
        )
        if self.video.get_one(["id"], **cont_orcode):
            print(f"[DATA EXIST][{data['dvd_id']}] {data['title'][0:20]}...")

            return None

        await self.record(data)

    async def run_scraper(self, fetch_worker=30) -> NoReturn:
        base = "https://www.javdatabase.com/movies/"
        soup = await self.soup(base)
        count = [0]
        pages = int(
            soup.find_all("a", {"class": "page-numbers"})[-2].text.replace(",", "")
        )

        status = manager.status_bar(
            status_format="{program}{fill}{stage}{fill}",
            color="bold_slategray",
            program="JAVData Scraper",
            stage="Loading",
        )

        for page in range(1, pages + 1, 1):
            soup = await self.soup(f"{base}page/{page}/")
            links = [
                vid.a["href"] for vid in soup.find_all("div", {"class": "movieheader"})
            ]
            tasks = [
                links[idx : idx + fetch_worker]
                for idx in range(0, len(links), fetch_worker)
            ]

            for task in tasks:
                cdata = await gather(*[self.insert_furl(u) for u in task])
                count[0] += len([c for c in cdata if c])
                status.update(stage=f"[ {page}/{pages} pages ]")

        print(f"[RECORD] {count[0]} data")
        manager.stop()
