#!/usr/bin/env python3
"""Harvest Japanese doctoral-dissertation metadata with History signals.

Source: NDL Search (National Diet Library) SRU API, data provider ``irdb``
(JPCOAR's Institutional Repositories DataBase as re-served by NDL Search).
NDL Search's API terms allow non-commercial use without an application
(https://ndlsearch.ndl.go.jp/help/api, provider table /help/api/provider:
IRDB = search API yes, harvest API no). IRDB's own site (irdb.nii.ac.jp)
disallows all robots, and the JAIRO Cloud repositories disallow /oai and /api/,
so neither is used here.

The SRU interface returns at most 500 records per query (startRecord +
maximumRecords cannot reach record 501), so every query larger than 500 is
partitioned: first by publication-date ranges (bisection), then by degree
grantor (anywhere="<university>"), then by title terms (overlapping covers).
Coverage per base query (records found / numberOfRecords) is logged.

Politeness: one request at a time, >= 3 s between requests, Retry-After
honoured, stop on 403/429. Neutral user agent, no e-mail address anywhere.

Usage:
  python3 scripts/harvest_japan_dissertations.py harvest --out P
  python3 scripts/harvest_japan_dissertations.py counts --out P
Then scripts/classify_japan_dissertations.py builds records.jsonl.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA = "HistoriographyMetadataHarvest/1.0 (public dissertation metadata research)"
SRU = "https://ndlsearch.ndl.go.jp/api/sru"
MIN_DELAY = 3.0
CAP = 500

NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcndl": "http://ndl.go.jp/dcndl/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "srw": "http://www.loc.gov/zing/srw/",
}
RDF_ABOUT = "{%s}about" % NS["rdf"]
RDF_RES = "{%s}resource" % NS["rdf"]
RDFS_COMMENT = "{%s}comment" % NS["rdfs"]
RDFS_LABEL = "{%s}label" % NS["rdfs"]

DOCTORAL = 'anywhere="博士論文"'
BASE = 'dpid=irdb AND ' + DOCTORAL  # denominators: records labelled 博士論文
# Many IRDB doctoral records are typed 記事・論文 (resource-type mapping) but carry
# degreeName/dissertationNumber, so harvest queries use the looser "博士" and the
# classifier keeps only records with degree data.
SIG = 'anywhere="博士"'

# Base queries. "degree" queries keep every doctoral thesis with that degree
# name (classified locally); "signal" queries pick History signals from any
# degree. All are restricted to dpid=irdb and doctoral theses.
BASE_QUERIES = [
    ("deg-bungaku", 'anywhere="博士(文学)"'),
    ("deg-rekishigaku", 'anywhere="博士(歴史学)"'),
    ("deg-shigaku", 'anywhere="博士(史学)"'),
    ("deg-nihonshigaku", 'anywhere="博士(日本史学)"'),
    ("deg-jinbunkagaku", 'anywhere="博士(人文科学)"'),
    ("deg-jinbungaku", 'anywhere="博士(人文学)"'),
    ("deg-bunkakosho", 'anywhere="博士(文化交渉学)"'),
    ("sig-shigaku", SIG + ' AND anywhere="史学"'),
    ("sig-title-rekishi", SIG + ' AND title="歴史"'),
    ("sig-title-shi", SIG + ' AND title="史"'),
    ("sig-title-history", SIG + ' AND title="history"'),
    ("sig-title-historical", SIG + ' AND title="historical"'),
    ("sig-title-historiography", SIG + ' AND title="historiography"'),
    ("sig-title-century", SIG + ' AND title="century"'),
    ("sig-title-kinsei", SIG + ' AND title="近世"'),
    ("sig-title-chusei", SIG + ' AND title="中世"'),
    ("sig-title-kodai", SIG + ' AND title="古代"'),
    ("sig-title-edo", SIG + ' AND title="江戸"'),
    ("sig-title-meiji", SIG + ' AND title="明治"'),
    ("sig-title-bakufu", SIG + ' AND title="幕府"'),
    ("sig-title-shokuminchi", SIG + ' AND title="植民地"'),
    ("sig-title-teikoku", SIG + ' AND title="帝国"'),
    ("sig-title-seiki", SIG + ' AND title="世紀"'),
    ("sig-title-kindai", SIG + ' AND title="近代"'),
    ("sig-title-bakumatsu", SIG + ' AND title="幕末"'),
    ("sig-title-ishin", SIG + ' AND title="維新"'),
    ("sig-title-han", SIG + ' AND title="藩"'),
    ("sig-title-chotei", SIG + ' AND title="朝廷"'),
    ("sig-title-ocho", SIG + ' AND title="王朝"'),
    ("sig-title-shindai", SIG + ' AND title="清代"'),
    ("sig-title-minshin", SIG + ' AND title="明清"'),
    ("sig-title-mindai", SIG + ' AND title="明代"'),
    ("sig-title-todai", SIG + ' AND title="唐代"'),
    ("sig-title-sodai", SIG + ' AND title="宋代"'),
    ("sig-title-senji", SIG + ' AND title="戦時"'),
    ("sig-title-senryo", SIG + ' AND title="占領"'),
    ("sig-title-shiryo", SIG + ' AND title="史料"'),
    ("sig-title-monjo", SIG + ' AND title="文書"'),
    ("sig-title-empire", SIG + ' AND title="empire"'),
    ("sig-title-colonial", SIG + ' AND title="colonial"'),
    ("sig-title-medieval", SIG + ' AND title="medieval"'),
    ("sig-title-meiji-en", SIG + ' AND title="Meiji"'),
    ("sig-title-tokugawa", SIG + ' AND title="Tokugawa"'),
    ("sig-title-qing", SIG + ' AND title="Qing"'),
    ("sig-title-dynasty", SIG + ' AND title="dynasty"'),
    ("sig-title-imperial", SIG + ' AND title="imperial"'),
    ("sig-subject-rekishi", SIG + ' AND subject="歴史"'),
    ("sig-subject-history", SIG + ' AND subject="history"'),
]

# Title terms used to cover a query whose undated records exceed the cap.
TITLE_SPLIT = ["の", "研究", "における", "と", "に", "史", "論", "日本", "中国", "を",
               "的", "から", "について", "朝鮮", "近代", "文化", "社会", "思想", "形成",
               "the", "of", "and", "in", "a", "to", "Japan", "on", "study"]

DATE_RANGES = [("0001-01-01", "1999-12-31"), ("2000-01-01", "2012-12-31"),
               ("2013-01-01", "2016-12-31"), ("2017-01-01", "2020-12-31"),
               ("2021-01-01", "2027-12-31")]


class Stop(Exception):
    pass


class Client:
    def __init__(self, out: Path):
        self.out = out
        self.raw = out / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.log = open(out / "logs" / "harvest-requests.jsonl", "a", encoding="utf-8")
        self.last = 0.0
        self.requests = 0
        self.cache_hits = 0

    def sru(self, query: str, start: int = 1, maximum: int = CAP) -> str:
        key = hashlib.sha1(f"{query}|{start}|{maximum}".encode()).hexdigest()
        path = self.raw / f"{key}.xml.gz"
        if path.exists():
            self.cache_hits += 1
            return gzip.open(path, "rt", encoding="utf-8").read()
        params = {"operation": "searchRetrieve", "version": "1.2", "recordSchema": "dcndl",
                  "recordPacking": "xml", "startRecord": str(start),
                  "maximumRecords": str(maximum), "query": query}
        url = SRU + "?" + urllib.parse.urlencode(params)
        for attempt in range(5):
            wait = self.last + MIN_DELAY - time.time()
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            self.requests += 1
            status, text, err = None, None, None
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=180) as resp:
                    status = resp.status
                    text = resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                status = e.code
                err = str(e)
                if e.code in (403, 429):
                    ra = e.headers.get("Retry-After")
                    self._log(query, start, status, 0, err)
                    raise Stop(f"HTTP {e.code} (Retry-After={ra}) on {query}")
                if e.code >= 500:
                    ra = e.headers.get("Retry-After")
                    time.sleep(int(ra) if ra and ra.isdigit() else 30 * (attempt + 1))
                    self._log(query, start, status, 0, err)
                    continue
                self._log(query, start, status, 0, err)
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                err = str(e)
                self._log(query, start, status, 0, err)
                time.sleep(30 * (attempt + 1))
                continue
            if "<searchRetrieveResponse" not in text:
                self._log(query, start, status, len(text), "not an SRU response (challenge?)")
                raise Stop("unexpected non-SRU response: " + text[:200])
            self._log(query, start, status, len(text), None)
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                fh.write(text)
            return text
        raise Stop(f"gave up after retries: {query}")

    def _log(self, query, start, status, size, err):
        self.log.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "query": query,
                                   "start": start, "status": status, "bytes": size,
                                   "error": err}, ensure_ascii=False) + "\n")
        self.log.flush()


def number_of_records(text: str) -> int:
    m = re.search(r"<numberOfRecords>(\d+)</numberOfRecords>", text)
    if m:
        return int(m.group(1))
    if "Record does not exist" in text:
        return 0
    m = re.search(r"<message>(.*?)</message>", text)
    raise RuntimeError("SRU diagnostic: " + (m.group(1) if m else text[:300]))


def _text(el):
    return (el.text or "").strip() if el is not None else ""


def _agent_names(parent, tag):
    out = []
    for ag in parent.findall(tag, NS):
        for a in ag.findall("foaf:Agent", NS):
            name = _text(a.find("foaf:name", NS))
            tr = _text(a.find("dcndl:transcription", NS))
            if name:
                out.append({"name": name, "transcription": tr or None})
    return out


def parse_records(text: str) -> list[dict]:
    root = ET.fromstring(text)
    out = []
    for rec in root.iter("{%s}record" % NS["srw"]):
        rdf = rec.find(".//rdf:RDF", NS)
        if rdf is None:
            continue
        admin = rdf.find("dcndl:BibAdminResource", NS)
        ndl_uri = admin.get(RDF_ABOUT) if admin is not None else None
        category = _text(admin.find("dcndl:bibRecordCategory", NS)) if admin is not None else None
        subcats = [_text(x) for x in admin.findall("dcndl:bibRecordSubCategory", NS)] if admin is not None else []
        r = {"ndl_uri": ndl_uri, "ndl_id": ndl_uri.rsplit("/", 1)[-1] if ndl_uri else None,
             "category": category, "subcategories": subcats, "titles": [], "title_transcriptions": [],
             "alternatives": [], "creators": [], "issued": [], "dates": [], "date_granted": [],
             "dissertation_numbers": [], "degree_names": [], "grantors": [], "languages": [],
             "access_rights": [], "material_types": [], "subjects": [], "ndc": [], "descriptions": [],
             "see_also": [], "has_part": [], "identifiers": [], "linked_records": [], "formats": [],
             "publishers": [], "extent": []}
        item_see_also = []
        for br in rdf.findall("dcndl:BibResource", NS):
            for el in br.findall("dcterms:title", NS):
                if _text(el) and _text(el) not in r["titles"]:
                    r["titles"].append(_text(el))
            for d in br.findall("dc:title/rdf:Description", NS):
                v, tr = _text(d.find("rdf:value", NS)), _text(d.find("dcndl:transcription", NS))
                if v and v not in r["titles"]:
                    r["titles"].append(v)
                if tr:
                    r["title_transcriptions"].append(tr)
            for d in br.findall("dcndl:alternative", NS):
                desc = d.find("rdf:Description", NS)
                v = _text(desc.find("rdf:value", NS)) if desc is not None else _text(d)
                if v:
                    r["alternatives"].append(v)
            r["creators"] += _agent_names(br, "dcterms:creator")
            if not any(True for _ in br.findall("dcterms:creator", NS)):
                for c in br.findall("dc:creator", NS):
                    if _text(c):
                        r["creators"].append({"name": _text(c), "transcription": None})
            for tag, key in (("dcterms:issued", "issued"), ("dcterms:date", "dates"),
                             ("dcndl:dateGranted", "date_granted"),
                             ("dcndl:dissertationNumber", "dissertation_numbers"),
                             ("dcndl:degreeName", "degree_names"), ("dcterms:language", "languages"),
                             ("dcterms:accessRights", "access_rights"),
                             ("dcterms:description", "descriptions"), ("dcterms:extent", "extent"),
                             ("dcterms:identifier", "identifiers")):
                for el in br.findall(tag, NS):
                    v = _text(el)
                    if v and v not in r[key]:
                        r[key].append(v)
            r["grantors"] += [a["name"] for a in _agent_names(br, "dcndl:degreeGrantor")]
            r["publishers"] += [a["name"] for a in _agent_names(br, "dcterms:publisher")]
            for el in br.findall("dcndl:materialType", NS):
                r["material_types"].append(el.get(RDFS_LABEL) or el.get(RDF_RES))
            for el in br.findall("dcterms:subject", NS):
                res = el.get(RDF_RES)
                if res:
                    if "/ndc" in res.lower() or "ndc" in res.lower():
                        r["ndc"].append(res)
                    else:
                        r["subjects"].append(res)
                desc = el.find("rdf:Description", NS)
                if desc is not None and _text(desc.find("rdf:value", NS)):
                    r["subjects"].append(_text(desc.find("rdf:value", NS)))
            for el in br.findall("dc:subject", NS):
                if _text(el):
                    r["subjects"].append(_text(el))
            for el in br.findall("dcterms:format", NS):
                if _text(el):
                    r["formats"].append(_text(el))
            for el in br.findall("rdfs:seeAlso", NS):
                if el.get(RDF_RES) and el.get(RDF_RES) not in r["see_also"]:
                    r["see_also"].append(el.get(RDF_RES))
            for el in br.findall("dcterms:hasPart", NS):
                r["has_part"].append({"url": el.get(RDF_RES), "object_type": el.get(RDFS_COMMENT),
                                      "label": el.get(RDFS_LABEL)})
            for el in br.findall("dcndl:record", NS):
                res = el.get(RDF_RES)
                if res and res not in r["linked_records"]:
                    r["linked_records"].append(res)
        for it in rdf.findall("dcndl:Item", NS):
            for el in it.findall("rdfs:seeAlso", NS):
                res = el.get(RDF_RES)
                if res and res not in item_see_also:
                    item_see_also.append(res)
        r["item_see_also"] = item_see_also
        r["grantors"] = list(dict.fromkeys(r["grantors"]))
        r["degree_names"] = list(dict.fromkeys(r["degree_names"]))
        out.append(r)
    return out


class Harvester:
    def __init__(self, client: Client, out: Path):
        self.c = client
        self.out = out
        self.records: dict[str, dict] = {}
        self.matched: dict[str, set] = {}
        self.grantors: dict[str, int] = {}
        self.coverage = []
        # rewritten on every run; raw SRU responses are cached in raw/ so reruns are cheap
        self.store = open(out / "logs" / "harvest-raw-records.jsonl", "w", encoding="utf-8")

    def fetch(self, query: str) -> tuple[int, set]:
        text = self.c.sru(query)
        n = number_of_records(text)
        ids = set()
        if n == 0:
            return 0, ids
        for r in parse_records(text):
            rid = r["ndl_id"]
            if not rid:
                continue
            ids.add(rid)
            if rid not in self.records:
                self.records[rid] = r
                self.store.write(json.dumps(r, ensure_ascii=False) + "\n")
            for g in r["grantors"]:
                if re.search(r"[぀-ヿ一-鿿]", g):
                    self.grantors[g] = self.grantors.get(g, 0) + 1
        return n, ids

    def cover(self, q: str, used: frozenset, depth: int = 0) -> tuple[int, set]:
        n, found = self.fetch(q)
        if n <= CAP:
            return n, found
        # 1. date bisection (dated subset only)
        if "date" not in used:
            for lo, hi in DATE_RANGES:
                found |= self._date_cover(q, lo, hi, used | {"date"}, depth)
            if len(found) >= n:
                return n, found
        # 2. grantor partition (undated residue)
        if "grantor" not in used:
            local = {}
            for rid in found:
                for g in self.records[rid]["grantors"]:
                    local[g] = local.get(g, 0) + 1
            cands = sorted(local, key=lambda k: -local[k])
            cands += [u for u in COUNT_UNIVERSITIES if u not in local]
            for g in cands:
                if len(found) >= n:
                    break
                if len(g) < 3 or not re.search(r"[\u4e00-\u9fff]", g) or not g.endswith(
                        ("大学", "大學", "大学院", "大学校", "研究所", "機構")):
                    continue
                sub = f'{q} AND anywhere="{g}"'
                _, f2 = self.cover(sub, used | {"grantor", "date"}, depth + 1)
                found |= f2
            if len(found) >= n:
                return n, found
        # 3. title-term covers (overlapping), one level deep (two levels cost ~100 requests per large grantor)
        # Only inside a grantor slice: at base level a title slice is itself far over the cap.
        tdepth = sum(1 for u in used if u.startswith("title:"))
        if tdepth < 1 and "grantor" in used:
            for t in TITLE_SPLIT:
                if len(found) >= n:
                    break
                if f"title:{t}" in used:
                    continue
                sub = f'{q} AND title="{t}"'
                _, f2 = self.cover(sub, used | {f"title:{t}", "date", "grantor"}, depth + 1)
                found |= f2
        return n, found

    def _date_cover(self, q, lo, hi, used, depth):
        sub = f'{q} AND from="{lo}" AND until="{hi}"'
        n, found = self.fetch(sub)
        if n <= CAP:
            return found
        a = datetime.fromisoformat(lo)
        b = datetime.fromisoformat(hi)
        if (b - a).days < 1:
            # a single day over the cap: cover it with title terms
            _, f2 = self.cover(sub, used | {"grantor"}, depth + 1)
            return found | f2
        mid = a + (b - a) / 2
        m1 = mid.strftime("%Y-%m-%d")
        m2 = (mid + (datetime(2000, 1, 2) - datetime(2000, 1, 1))).strftime("%Y-%m-%d")
        found |= self._date_cover(q, lo, m1, used, depth)
        found |= self._date_cover(q, m2, hi, used, depth)
        return found

    def run(self, names=None):
        for name, clause in BASE_QUERIES:
            if names and name not in names:
                continue
            q = f"dpid=irdb AND {clause}"
            t0 = self.c.requests
            n, found = self.cover(q, frozenset())
            for rid in found:
                self.matched.setdefault(rid, set()).add(name)
            row = {"name": name, "query": q, "numberOfRecords": n, "found": len(found),
                   "coverage": round(len(found) / n, 4) if n else None,
                   "requests": self.c.requests - t0}
            self.coverage.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            self.save()

    def save(self):
        with open(self.out / "logs" / "harvest-matched.json", "w", encoding="utf-8") as fh:
            json.dump({k: sorted(v) for k, v in self.matched.items()}, fh, ensure_ascii=False)
        with open(self.out / "logs" / "harvest-coverage.json", "w", encoding="utf-8") as fh:
            json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                       "requests": self.c.requests, "cache_hits": self.c.cache_hits,
                       "records": len(self.records), "queries": self.coverage},
                      fh, ensure_ascii=False, indent=1)


COUNT_UNIVERSITIES = [
    "東京大学", "京都大学", "大阪大学", "東北大学", "名古屋大学", "九州大学", "北海道大学",
    "筑波大学", "広島大学", "神戸大学", "一橋大学", "お茶の水女子大学", "東京外国語大学",
    "東京都立大学", "首都大学東京", "大阪公立大学", "大阪市立大学", "千葉大学", "金沢大学", "岡山大学",
    "早稲田大学", "慶應義塾大学", "上智大学", "立教大学", "明治大学", "法政大学", "中央大学",
    "國學院大學", "國學院大学", "学習院大学", "日本大学", "東洋大学", "駒澤大学", "大正大学",
    "立正大学", "専修大学", "青山学院大学", "同志社大学", "立命館大学", "関西大学",
    "関西学院大学", "龍谷大学", "佛教大学", "大谷大学", "奈良女子大学", "総合研究大学院大学",
    "東北学院大学", "愛知大学", "南山大学", "西南学院大学", "国際基督教大学", "創価大学",
    "日本女子大学", "東京女子大学", "フェリス女学院大学", "二松学舎大学", "大東文化大学",
    "鹿児島大学", "熊本大学", "新潟大学", "信州大学", "静岡大学", "琉球大学", "島根大学",
    "茨城大学", "埼玉大学", "横浜国立大学", "東京学芸大学", "名古屋市立大学", "愛知県立大学",
]


def counts(client: Client, out: Path):
    """Denominators: all IRDB doctoral theses by issued year and by grantor."""
    res = {"generated_at": datetime.now(timezone.utc).isoformat(), "base": BASE}
    n = number_of_records(client.sru(BASE, maximum=1))
    res["all_doctoral"] = n
    res["dated_any"] = number_of_records(client.sru(f'{BASE} AND from="0001-01-01" AND until="2100-12-31"', maximum=1))
    res["by_issued_year"] = {}
    for y in range(2000, 2027):
        q = f'{BASE} AND from="{y}-01-01" AND until="{y}-12-31"'
        res["by_issued_year"][y] = number_of_records(client.sru(q, maximum=1))
        print(y, res["by_issued_year"][y], flush=True)
    res["by_grantor_anywhere"] = {}
    for u in COUNT_UNIVERSITIES:
        q = f'{BASE} AND anywhere="{u}"'
        res["by_grantor_anywhere"][u] = number_of_records(client.sru(q, maximum=1))
        print(u, res["by_grantor_anywhere"][u], flush=True)
    res["by_provider_category_note"] = ("numberOfRecords counts NDL Search records of every "
                                        "category returned under dpid=irdb (R000000025 IRDB, "
                                        "R100000039 NDL Digital Collections doctoral copies, etc.)")
    (out / "logs" / "denominators.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["harvest", "counts"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    out = Path(a.out)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    client = Client(out)
    try:
        if a.mode == "harvest":
            h = Harvester(client, out)
            # reload records already stored so the matched map stays complete across runs
            h.run(set(a.only) if a.only else None)
            h.save()
        else:
            counts(client, out)
    except Stop as e:
        print("STOPPED:", e, file=sys.stderr)
        sys.exit(2)
    print(f"requests={client.requests} cache_hits={client.cache_hits}", file=sys.stderr)


if __name__ == "__main__":
    main()
