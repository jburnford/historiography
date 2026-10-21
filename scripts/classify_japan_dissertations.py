#!/usr/bin/env python3
"""Build records.jsonl for Japanese doctoral dissertations with History signals.

Input (written by harvest_japan_dissertations.py into P/logs/):
  harvest-raw-records.jsonl  parsed NDL Search (dpid=irdb) records
  harvest-matched.json       record id -> base queries that returned it

Steps: keep doctoral records (degree name, dissertation number or material
type 博士論文); cluster duplicates (IRDB record + NDL Digital Collections copy,
or the same thesis in two repositories); classify each cluster
history / possible / other with explicit, logged rules; describe the files
the metadata declares (full text 本文 vs abstract 要旨 / summary 要約 /
examination report 審査結果の要旨); write records.jsonl (same core shape as
the US tier-2 records, plus Japanese fields) and summary.json.

Usage: python3 scripts/classify_japan_dissertations.py --out P
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

CJK = re.compile(r"[぀-ヿ㐀-鿿]")

# ---------------------------------------------------------------- degrees
HIST_DEGREES = {"歴史学", "史学", "日本史学", "東洋史学", "西洋史学"}
SCI_DEGREE = re.compile(
    r"医|歯|薬|理学|理工|工学|農|獣医|看護|保健|情報|水産|生命|体育|スポーツ|栄養|海洋|"
    r"技術|医療|リハビリ|心理|数理|物質|生物|化学|地球|環境科学|生活科学|健康|福祉|"
    r"デザイン|芸術工学|感性|システム|知識科学|材料|エネルギー|食|Medic|Engineer|Science")

# ---------------------------------------------------------------- title signals
STRONG_JA = [r"歴史", r"史料", r"史学", r"史的", r"史論", r"通史", r"古文書", r"史観", r"歴史学"]
STRONG_EN = [r"\bhistor(y|ies|ical|iography|iographical)\b"]
# "X史" where X is a kanji: generic history-of-X (political, social, economic ...)
GENERIC_SHI = re.compile(r"[一-鿿]史")
NON_HIST_SHI = {"女史", "歴史", "通史", "青史"}
ART_SHI = re.compile(r"美術史|文学史|建築史|音楽史|演劇史|芸能史|科学史|技術史|国語史|語史|"
                     r"学説史|研究史|受容史|文体史|美学史|映画史|写真史|デザイン史|服飾史|書道史|庭園史")
PERIOD_JA = re.compile(
    r"近世|中世|古代|江戸時代|江戸期|江戸幕府|江戸後期|江戸前期|江戸中期|徳川|明治|大正期|大正時代|"
    r"昭和戦前|昭和初期|昭和期|戦前期|戦前の|戦時|戦中|占領期|占領下|幕府|幕末|維新|[^東]藩|朝廷|王朝|"
    r"清代|清朝|清末|明代|明清|明末|唐代|宋代|元代|漢代|秦漢|隋唐|魏晋|南北朝|五代|高麗|朝鮮王朝|"
    r"朝鮮時代|朝鮮後期|李朝|植民地|帝国|満洲|満州|国民政府|民国期|中華民国|戦国|室町|鎌倉|平安|"
    r"奈良時代|律令|荘園|寺社|[一二三四五六七八九十0-9０-９]+世紀|世紀|ヴィクトリア朝|"
    r"革命期|共和政|帝政|王政|植民|開港|条約|外交|将軍|大名|武士|藩政|郷村|村落|寺院|神社|"
    r"王権|皇帝|天皇|在地|近代日本|近代中国|近代朝鮮|日清|日露|戦後改革|終戦|敗戦")
PERIOD_EN = re.compile(r"\b(meiji|tokugawa|edo period|qing|ming dynasty|dynast(y|ies)|medieval|"
                       r"early modern|colonial|empire|imperial|\d{2}(th|st|nd|rd)[- ]century|"
                       r"centur(y|ies)|wartime|occupation|postwar|prewar|shogun|samurai|"
                       r"song dynasty|tang|joseon|choson|manchukuo|heian|kamakura|muromachi)\b", re.I)
LIT = re.compile(r"文学|小説|物語|和歌|俳諧|俳句|詩|歌集|歌人|作品|文体|表現|作家|戯曲|能楽|狂言|"
                 r"歌舞伎|浄瑠璃|漢詩|注釈|語彙|語法|文法|音韻|方言|言語|日本語|中国語|英語|韓国語|"
                 r"翻訳|受容|享受|縁起|[ァ-ヶー]+語|修辞|説話|随筆|日記文学|表象|文藝|文芸|今様|歌謡|古事記|万葉|源氏|神話|伝承|表記|漢字|文字|音声|訓読|読本|論考|literature|literary|novel|poet|poem|fiction|"
                 r"linguistic|language|grammar|translation", re.I)
PHIL = re.compile(r"哲学|地理学|ジェントリフィケーション|倫理|形而上|存在論|認識論|現象学|美学|懐疑主義|社会学的|社会学|人類学|民族誌|エスノグラフィ|ethnograph|sociolog|anthropolog|philosoph|ethic|metaphys", re.I)
ART = re.compile(r"美術|オペラ|石窟|視覚|定家様|書跡|法帖|保存|ヘリテージ|文化財|(?<![計企区録])画|書芸術|書道|書法|絵画|彫刻|仏像|絵巻|図像|工芸|陶磁|建築|庭園|書画|版画|浮世絵|音楽|映画|演劇|舞踊|写真|デザイン|"
                 r"\bart\b|painting|sculpture|architectur|music|film|cinema|theat(er|re)", re.I)
ARCH = re.compile(r"考古|物質文化|動物骨|人骨|遺跡|古墳|土器|須恵器|埴輪|出土|発掘|石器|貝塚|縄文|弥生|遺構|窯|"
                  r"archaeolog|excavat|kofun|jomon|yayoi", re.I)
EDU_SOC = re.compile(r"心理|認知|教授法|学習者|調査研究|質問紙|実験|臨床|psycholog|cognitive", re.I)


def nfkc(s):
    return unicodedata.normalize("NFKC", s or "")


def degree_core(name):
    n = nfkc(name).replace(" ", "")
    m = re.search(r"博士\(([^)]+)\)", n)
    if m:
        return m.group(1)
    m = re.search(r"Doctor of ([A-Za-z ]+)", n)
    return m.group(1).strip() if m else n


# Degree groups for records without a history degree. "core" humanities degrees
# (programme often a history programme: e.g. Tokyo 総合文化研究科 grants 博士(学術),
# Hitotsubashi's history faculty sits in 社会学研究科) can reach "history" from title
# signals; social-science/professional degrees reach at most "possible".
CORE_DEGREE = re.compile(r"^(文学|学術|人文科学|人文学|人文|文化交渉学|地域研究|国際文化|比較文化|"
                         r"人間・環境学|社会学|文化史学|地域文化|文化学|日本学|国際日本学|日本文化|"
                         r"人間文化|人間文化学|人間文化科学|文化科学|人文社会科学|社会文化|国際関係|"
                         r"国際学|中国研究|アジア研究|宗教学|仏教学|神道学|言語文化|文学博士|博士|)$")
ART_DEGREE = re.compile(r"音楽|芸術|美術|デザイン|造形|映像")
LANG_SHI = re.compile(r"(日本語|国語|中国語|英語|言語|語彙|語)史")
SCI_TITLE = re.compile(r"地形|地質|堆積|第四紀|古生|中生代|土砂|岩石|岩体|変成|断層|花崗岩|生物群|個体群")
SCI_SHI = re.compile(r"生活史|進化史|形成史(?=.*(岩|地層|堆積))|熱史|変形史|冷却史|地史|履歴")


def classify(rec):
    """Return (label, reasons, flags). Rules are listed in the README."""
    titles = " / ".join(rec["all_titles"])
    t = nfkc(titles)
    reasons, flags = [], []
    degs = [degree_core(d) for d in rec["degree"]]
    deg_hist = any(d in HIST_DEGREES for d in degs)
    deg_sci = bool(degs) and all(SCI_DEGREE.search(d) for d in degs) and not deg_hist
    deg_art = bool(degs) and any(ART_DEGREE.search(d) for d in degs) and not deg_hist
    deg_core = (not degs) or any(CORE_DEGREE.match(d) for d in degs) or any(
        nfkc(x).replace(" ", "") in ("文学博士", "博士", "博士(文学)") for x in rec["degree"])
    lang_shi = bool(LANG_SHI.search(t))
    sci_shi = bool(SCI_SHI.search(t))
    t_h = SCI_SHI.sub(" ", LANG_SHI.sub(" ", t))   # language-history / life-history removed
    strong = [p for p in STRONG_JA if re.search(p, t_h)] + \
             [m.group(0) for p in STRONG_EN for m in [re.search(p, t_h, re.I)] if m]
    shi = [m.group(0) for m in GENERIC_SHI.finditer(t_h) if m.group(0) not in NON_HIST_SHI]
    art_shi = ART_SHI.findall(t)
    shi_hist = [x for x in shi if not any(x in a for a in art_shi)]
    t_p = re.sub(r"(21|二十一|２１)世紀|21st[- ]century", " ", t)   # "21st-century skills" etc.
    period = sorted(set(PERIOD_JA.findall(t_p))) + sorted(set(m.group(0).lower() for m in PERIOD_EN.finditer(t_p)))
    lit = bool(LIT.search(t)) or lang_shi
    phil, art, arch, edu = (bool(x.search(t)) for x in (PHIL, ART, ARCH, EDU_SOC))
    for cond, name in ((arch, "archaeology_topic"), (art or bool(art_shi), "art_or_architecture_topic"),
                       (lit, "literature_or_language_topic"), (phil, "philosophy_topic")):
        if cond:
            flags.append(name)
    hist_words = strong + shi_hist
    explicit = [w for w in strong if w in ("歴史", "史料", "史学", "歴史学", "古文書", "通史")] + \
               [w for w in strong if re.match(r"(?i)histor", w)]
    if deg_hist:
        reasons.append("history degree: " + ",".join(degs))
        return "history", reasons, flags
    if deg_sci:
        if hist_words and not sci_shi:
            reasons.append("science/medical degree with history wording: " + ",".join(hist_words))
            return "possible", reasons, flags
        return "other", ["science/medical degree"], flags
    if deg_art:
        if hist_words or period:
            reasons.append("arts degree with history/period wording: " + ",".join((hist_words + period)[:4]))
            return "possible", reasons, flags
        return "other", ["arts degree"], flags
    if not (hist_words or period or art_shi):
        return "other", ["no history signal in title"], flags
    if SCI_TITLE.search(t):
        reasons.append("earth/life-science wording in title: " + SCI_TITLE.search(t).group(0))
        return "possible", reasons, flags
    if not deg_core:
        reasons.append("social-science/professional degree (" + ",".join(degs) + ") with history wording: "
                       + ",".join((hist_words + period)[:4]))
        return "possible", reasons, flags
    # core humanities degree from here
    if art_shi and not explicit and not shi_hist:
        reasons.append("art/literature/architecture/language history: " + ",".join(art_shi))
        return "possible", reasons, flags
    if arch and not explicit:
        reasons.append("archaeology topic without explicit history wording")
        return "possible", reasons, flags
    if (art or lit or phil) and not explicit:
        if hist_words or period:
            reasons.append("history/period wording with literature/language/philosophy/art cues: "
                           + ",".join((hist_words + period)[:4]))
            return "possible", reasons, flags
    if hist_words:
        reasons.append("history wording: " + ",".join(hist_words[:4]))
        if period:
            reasons.append("period: " + ",".join(period[:4]))
        return "history", reasons, flags
    if period:
        reasons.append("period/polity wording: " + ",".join(period[:4]))
        return "history", reasons, flags
    return "possible", ["art/language history only: " + ",".join(art_shi)], flags


# ---------------------------------------------------------------- files
def file_kind(part):
    ot = (part.get("object_type") or "").lower()
    name = nfkc((part.get("label") or "") + " " + (part.get("url") or "")).lower()
    if re.search(r"review|shinsa|審査|kekka|result|_rev|hyoka|評価", name):
        return "examination_report"   # 審査結果の要旨
    if ot == "fulltext":
        return "fulltext"
    if ot == "abstract":
        return "abstract"             # 内容の要旨
    if ot == "summary":
        return "summary"              # 要約 (published when the full text is withheld)
    if re.search(r"abstract|youshi|yoshi|要旨|_abs|gaiyo|概要", name):
        return "abstract"
    if re.search(r"summary|youyaku|yoyaku|要約", name):
        return "summary"
    if re.search(r"fulltext|ftxt|full|honbun|本文|_body|text", name):
        return "fulltext"
    if ot:
        return ot
    return "unlabelled"


SLUGS = {
    "東京大学": ("tokyo", "University of Tokyo"), "京都大学": ("kyoto", "Kyoto University"),
    "大阪大学": ("osaka", "Osaka University"), "東北大学": ("tohoku", "Tohoku University"),
    "名古屋大学": ("nagoya", "Nagoya University"), "九州大学": ("kyushu", "Kyushu University"),
    "北海道大学": ("hokkaido", "Hokkaido University"), "筑波大学": ("tsukuba", "University of Tsukuba"),
    "広島大学": ("hiroshima", "Hiroshima University"), "神戸大学": ("kobe", "Kobe University"),
    "一橋大学": ("hitotsubashi", "Hitotsubashi University"),
    "お茶の水女子大学": ("ochanomizu", "Ochanomizu University"),
    "東京外国語大学": ("tufs", "Tokyo University of Foreign Studies"),
    "東京都立大学": ("tmu", "Tokyo Metropolitan University"),
    "首都大学東京": ("tmu", "Tokyo Metropolitan University"),
    "大阪公立大学": ("omu", "Osaka Metropolitan University"),
    "大阪市立大学": ("osaka-cu", "Osaka City University"), "千葉大学": ("chiba", "Chiba University"),
    "金沢大学": ("kanazawa", "Kanazawa University"), "岡山大学": ("okayama", "Okayama University"),
    "早稲田大学": ("waseda", "Waseda University"), "慶應義塾大学": ("keio", "Keio University"),
    "上智大学": ("sophia", "Sophia University"), "立教大学": ("rikkyo", "Rikkyo University"),
    "明治大学": ("meiji", "Meiji University"), "法政大学": ("hosei", "Hosei University"),
    "中央大学": ("chuo", "Chuo University"), "國學院大學": ("kokugakuin", "Kokugakuin University"),
    "國學院大学": ("kokugakuin", "Kokugakuin University"),
    "国学院大学": ("kokugakuin", "Kokugakuin University"),
    "学習院大学": ("gakushuin", "Gakushuin University"), "日本大学": ("nihon", "Nihon University"),
    "東洋大学": ("toyo", "Toyo University"), "駒澤大学": ("komazawa", "Komazawa University"),
    "駒沢大学": ("komazawa", "Komazawa University"), "大正大学": ("taisho", "Taisho University"),
    "立正大学": ("rissho", "Rissho University"), "専修大学": ("senshu", "Senshu University"),
    "青山学院大学": ("aoyama", "Aoyama Gakuin University"),
    "同志社大学": ("doshisha", "Doshisha University"), "立命館大学": ("ritsumeikan", "Ritsumeikan University"),
    "関西大学": ("kansai", "Kansai University"), "関西学院大学": ("kwansei", "Kwansei Gakuin University"),
    "龍谷大学": ("ryukoku", "Ryukoku University"), "佛教大学": ("bukkyo", "Bukkyo University"),
    "大谷大学": ("otani", "Otani University"), "奈良女子大学": ("nara-wu", "Nara Women's University"),
    "総合研究大学院大学": ("sokendai", "SOKENDAI (Graduate University for Advanced Studies)"),
    "東北学院大学": ("tohoku-gakuin", "Tohoku Gakuin University"), "愛知大学": ("aichi", "Aichi University"),
    "南山大学": ("nanzan", "Nanzan University"), "西南学院大学": ("seinan", "Seinan Gakuin University"),
    "国際基督教大学": ("icu", "International Christian University"), "創価大学": ("soka", "Soka University"),
    "日本女子大学": ("jwu", "Japan Women's University"), "東京女子大学": ("twcu", "Tokyo Woman's Christian University"),
    "二松学舎大学": ("nishogakusha", "Nishogakusha University"), "大東文化大学": ("daito", "Daito Bunka University"),
    "鹿児島大学": ("kagoshima", "Kagoshima University"), "熊本大学": ("kumamoto", "Kumamoto University"),
    "新潟大学": ("niigata", "Niigata University"), "信州大学": ("shinshu", "Shinshu University"),
    "静岡大学": ("shizuoka", "Shizuoka University"), "琉球大学": ("ryukyu", "University of the Ryukyus"),
    "島根大学": ("shimane", "Shimane University"), "茨城大学": ("ibaraki", "Ibaraki University"),
    "埼玉大学": ("saitama", "Saitama University"), "横浜国立大学": ("ynu", "Yokohama National University"),
    "東京学芸大学": ("u-gakugei", "Tokyo Gakugei University"), "名古屋市立大学": ("nagoya-cu", "Nagoya City University"),
    "愛知県立大学": ("aichi-pu", "Aichi Prefectural University"), "皇學館大学": ("kogakkan", "Kogakkan University"),
    "東海大学": ("tokai", "Tokai University"), "愛知学院大学": ("aichi-gakuin", "Aichi Gakuin University"),
    "九州大学大学院": ("kyushu", "Kyushu University"), "奈良大学": ("nara-u", "Nara University"),
    "花園大学": ("hanazono", "Hanazono University"), "京都女子大学": ("kyoto-wu", "Kyoto Women's University"),
    "神戸女子大学": ("kobe-wu", "Kobe Women's University"), "名古屋学院大学": ("ngu", "Nagoya Gakuin University"),
    "大阪大谷大学": ("osaka-ohtani", "Osaka Ohtani University"), "広島修道大学": ("shudo", "Hiroshima Shudo University"),
    "北海道教育大学": ("hokkyodai", "Hokkaido University of Education"), "高野山大学": ("koyasan", "Koyasan University"),
    "東京藝術大学": ("geidai", "Tokyo University of the Arts"), "放送大学": ("ouj", "The Open University of Japan"),
    "人間文化研究機構": ("nihu", "NIHU"), "国際日本文化研究センター": ("nichibunken", "Nichibunken"),
}


EN_GRANTORS = {
    "university of tokyo": "東京大学", "the university of tokyo": "東京大学", "kyoto university": "京都大学",
    "osaka university": "大阪大学", "tohoku university": "東北大学", "nagoya university": "名古屋大学",
    "kyushu university": "九州大学", "hokkaido university": "北海道大学", "university of tsukuba": "筑波大学",
    "hiroshima university": "広島大学", "kobe university": "神戸大学", "hitotsubashi university": "一橋大学",
    "waseda university": "早稲田大学", "keio university": "慶應義塾大学", "osaka city university": "大阪市立大学",
    "ochanomizu university": "お茶の水女子大学", "sophia university": "上智大学",
    "the graduate university for advanced studies": "総合研究大学院大学", "sokendai": "総合研究大学院大学",
    "ritsumeikan university": "立命館大学", "doshisha university": "同志社大学",
}


def grantor_ja(rec):
    for g in rec["grantors"]:
        g2 = nfkc(g).strip()
        m = re.search(r"\(([^()]*[\u3040-\u30ff\u4e00-\u9fff][^()]*)\)", g2)
        if m:
            return m.group(1).replace(" ", "")
        if CJK.search(g2):
            return re.split(r"[(（]", g2)[0].replace(" ", "")
    for g in rec["grantors"]:
        key = re.sub(r"\s+", " ", nfkc(g)).strip().lower().rstrip(".")
        if key in EN_GRANTORS:
            return EN_GRANTORS[key]
    return nfkc(rec["grantors"][0]) if rec["grantors"] else None


def grantor_slug(g, landing):
    if g:
        for k, v in SLUGS.items():
            if nfkc(k) == g or g.startswith(nfkc(k)):
                return v
    if landing:
        host = urlparse(landing).netloc
        if host.endswith(".repo.nii.ac.jp"):
            return host.split(".")[0], g
        if host and host != "hdl.handle.net" and host != "doi.org":
            return host.replace("www.", "").split(".")[0], g
    return ("jp-unknown", g)


def norm_title(s):
    s = nfkc(s).lower()
    return re.sub(r"[\W_]+", "", s)


def norm_number(n):
    n = nfkc(n).replace(" ", "")
    n = re.sub(r"^\d{4,6}", "", n)  # institution code prefix, e.g. 32641甲第697号
    m = re.search(r"([甲乙])?第?0*(\d+)号?", n)
    return (m.group(1) or "") + m.group(2) if m else n


def is_doctoral(r):
    if any("博士" in nfkc(d) or "doctor" in d.lower() for d in r["degree_names"]):
        return True
    if r["dissertation_numbers"]:
        return True
    return any("博士論文" in (m or "") or "Doctoral" in (m or "") for m in r["material_types"])


def year_of(vals):
    for v in vals:
        m = re.match(r"(\d{4})", nfkc(v))
        if m and 1900 < int(m.group(1)) < 2030:
            return int(m.group(1))
    return None


def access_category(files_kinds, open_record, ndl_only):
    if "fulltext" in files_kinds:
        return "open_fulltext_declared" if open_record is not False else "fulltext_declared_restricted"
    if "unlabelled" in files_kinds:
        return "files_unlabelled"      # may be the full text; check size/pages before counting
    if files_kinds & {"abstract", "summary", "examination_report"}:
        return "summary_only"
    if "unlabelled" in files_kinds or files_kinds:
        return "files_unlabelled"
    if ndl_only:
        return "ndl_only"
    return "no_files_declared"


def build(out: Path):
    raw = [json.loads(l) for l in open(out / "logs" / "harvest-raw-records.jsonl", encoding="utf-8")]
    matched = json.load(open(out / "logs" / "harvest-matched.json", encoding="utf-8"))
    recs = {r["ndl_id"]: r for r in raw if r.get("ndl_id")}
    doctoral = {k: r for k, r in recs.items() if is_doctoral(r)}

    # ---- cluster duplicates (union-find)
    parent = {k: k for k in doctoral}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    keys = collections.defaultdict(list)
    for k, r in doctoral.items():
        g = grantor_ja(r) or ""
        for n in r["dissertation_numbers"]:
            keys[("num", g, norm_number(n))].append(k)
        tt = [norm_title(t) for t in r["titles"] if len(norm_title(t)) >= 6]
        sur = norm_title(r["creators"][0]["name"].split(",")[0]) if r["creators"] else ""
        for t in tt[:1]:
            keys[("title", t, sur)].append(k)
        for lr in r.get("linked_records", []):
            other = lr.rsplit("/", 1)[-1].split("#")[0]
            if other in doctoral and other != k:
                keys[("link", min(k, other), max(k, other))] += [k, other]
    for v in keys.values():
        for x in v[1:]:
            union(v[0], x)
    clusters = collections.defaultdict(list)
    for k in doctoral:
        clusters[find(k)].append(k)

    def rank(k):
        r = doctoral[k]
        return (0 if r["category"] == "R000000025" else 1 if r["category"] == "R100000039" else 2,
                -len(r["has_part"]), k)

    out_rows = []
    for members in clusters.values():
        members.sort(key=rank)
        canon = doctoral[members[0]]
        allm = [doctoral[m] for m in members]
        titles, alts, creators, parts, see_also, ids = [], [], [], [], [], []
        degs, grants, nums, granted, issued, langs, acc, descs, subj = [], [], [], [], [], [], [], [], []
        queries = set()
        for r in allm:
            for t in r["titles"] + r["alternatives"]:
                if t not in titles:
                    titles.append(t)
            for c in r["creators"]:
                if c["name"] not in [x["name"] for x in creators]:
                    creators.append(c)
            for p in r["has_part"]:
                if p["url"] and p["url"] not in [x["url"] for x in parts]:
                    parts.append(p)
            for u in r["see_also"] + r.get("item_see_also", []):
                if u not in see_also:
                    see_also.append(u)
            for lst, key in ((degs, "degree_names"), (grants, "grantors"), (nums, "dissertation_numbers"),
                             (granted, "date_granted"), (issued, "issued"), (langs, "languages"),
                             (acc, "access_rights"), (descs, "descriptions"), (subj, "subjects"),
                             (ids, "identifiers")):
                for v in r.get(key, []):
                    if v not in lst:
                        lst.append(v)
            queries |= set(matched.get(r["ndl_id"], []))
        title_ja = next((t for t in titles if CJK.search(t)), None)
        title_en = next((t for t in titles if not CJK.search(t) and re.search(r"[A-Za-z]{3}", t)), None)
        names = [c["name"] for c in creators]
        romanised = [n for n in names if not CJK.search(n)] + \
                    [c["transcription"] for c in creators if c.get("transcription")]
        landing_repo = next((u for u in see_also if "repo.nii.ac.jp" in u or "hdl.handle.net" in u
                             or ("dl.ndl.go.jp" not in u and "id.ndl.go.jp" not in u
                                 and "doi.org" not in u)), None)
        ndl_dc = next((u for u in see_also if u.startswith("https://dl.ndl.go.jp/pid/")), None)
        doi = next((u for u in see_also if "doi.org/" in u), None)
        kinds = [file_kind(p) for p in parts]
        files = [{"url": p["url"], "object_type": p["object_type"], "label": p["label"], "kind": k}
                 for p, k in zip(parts, kinds)]
        open_record = True if any(a == "インターネット公開" for a in acc) else (
            False if any("限定" in a for a in acc) and not any(a == "インターネット公開" for a in acc) else None)
        ndl_only = any("国立国会図書館内限定" in a for a in acc)
        acat = access_category(set(kinds), open_record, ndl_only)
        g = grantor_ja(canon) or grantor_ja({"grantors": grants})
        slug, gname = grantor_slug(g, landing_repo)
        y_granted, y_issued = year_of(granted), year_of(issued)
        lang = []
        for l in langs:
            l = {"jpn": "ja", "eng": "en", "und": None}.get(l, l)
            if l and l not in lang:
                lang.append(l)
        if not lang:
            lang = ["ja"] if title_ja else (["en"] if title_en else [])
        advisors, committee = [], []
        for d in descs:
            dd = nfkc(d)
            for m in re.finditer(r"【?論文審査委員主査】?\s*([^\(\n【]+)", dd):
                advisors.append(m.group(1).strip(" ,，"))
            for m in re.finditer(r"【?論文審査委員副査】?\s*([^【\n]+)", dd):
                for part in re.split(r"[,，、]", re.sub(r"\([^)]*\)", "", m.group(1))):
                    if part.strip():
                        committee.append(part.strip())
        row = {
            "institution": slug,
            "institution_name": SLUGS.get(g, (None, None))[1] if g in SLUGS else gname,
            "grantor": g,
            "grantors": grants,
            "stream": "jp-irdb-ndlsearch",
            "id": canon["ndl_id"],
            "ndl_ids": members,
            "title": title_ja or title_en or (titles[0] if titles else None),
            "title_ja": title_ja,
            "title_en": title_en,
            "all_titles": titles,
            "title_transcriptions": [t for r in allm for t in r.get("title_transcriptions", [])][:2],
            "authors": names[:3],
            "authors_romanised": romanised[:3],
            "advisors": advisors,
            "committee": committee,
            "degree": degs,
            "degree_name": nfkc(degs[0]).replace(" ", "") if degs else None,
            "degree_level": ["doctoral"],
            "degree_classification": "doctoral",
            "dissertation_number": nums[0] if nums else None,
            "dissertation_numbers": nums,
            "date_granted": granted[0] if granted else None,
            "issued_dates": issued,
            "graduation_dates": granted,
            "copyright_dates": [],
            "year": y_granted or y_issued,
            "year_source": "dateGranted" if y_granted else ("issued" if y_issued else None),
            "candidate_years": sorted({y for y in (y_granted, y_issued) if y}),
            "language": lang,
            "subjects": subj,
            "descriptions": [d for d in descs if len(d) > 20][:3],
            "item_url": landing_repo or ndl_dc or doi,
            "landing_urls": see_also,
            "ndl_digital_url": ndl_dc,
            "doi": doi,
            "access_rights": acc,
            "files": files,
            "pdf_urls": [f["url"] for f in files if f["kind"] == "fulltext"],
            "summary_urls": [f["url"] for f in files if f["kind"] in ("abstract", "summary", "examination_report")],
            "pdf_open": bool([f for f in files if f["kind"] == "fulltext"]) and open_record is not False,
            "fulltext_status": ("fulltext_declared" if "fulltext" in kinds else
                                "summary_only" if set(kinds) & {"abstract", "summary", "examination_report"} else
                                "unlabelled_files" if kinds else "no_files_declared"),
            "access_category": acat,
            "source_queries": sorted(queries),
            "source_harvest": "data/field-research/japan-dissertations-2026-10-20",
            "country": "JP",
            "metadata_source": "NDL Search SRU, dpid=irdb (IRDB/JPCOAR via NDL Search)",
        }
        label, reasons, flags = classify(row)
        row["history_label"] = label
        row["history_reasons"] = reasons
        row["topic_flags"] = flags
        row["history_scope"] = {"history": "history_degree_or_history_title",
                                "possible": "possible_history", "other": "not_history"}[label]
        row["history_basis"] = ("history_degree" if reasons and reasons[0].startswith("history degree")
                                else "title_signals" if label == "history" else None)
        # Suggested graph eligibility (to be reviewed before ingest; see README):
        # only the History-degree records are strict; title-classified History is ~60-70% precise.
        row["eligibility"] = ("history_phd" if row["history_basis"] == "history_degree" else
                              "needs_review" if label in ("history", "possible") else "adjacent")
        row["eligibility_basis"] = "JP title/degree classifier: " + "; ".join(reasons)
        out_rows.append(row)
    out_rows.sort(key=lambda r: (r["history_label"] != "history", -(r["year"] or 0), r["id"]))
    # records.jsonl: history + possible; the "other" doctoral theses (needed for the
    # denominators and for re-classification) go to logs/records-other.jsonl
    with open(out / "records.jsonl", "w", encoding="utf-8") as fh, \
            open(out / "logs" / "records-other.jsonl", "w", encoding="utf-8") as fo:
        for r in out_rows:
            (fh if r["history_label"] != "other" else fo).write(json.dumps(r, ensure_ascii=False) + "\n")
    import csv
    cols = ["id", "history_label", "history_basis", "eligibility", "institution", "grantor", "degree_name",
            "dissertation_number", "date_granted", "year", "title_ja", "title_en", "authors",
            "authors_romanised", "language", "access_category", "item_url", "pdf_urls", "summary_urls",
            "topic_flags", "history_reasons"]
    with open(out / "records.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in out_rows:
            if r["history_label"] == "other":
                continue
            w.writerow([" | ".join(map(str, r[c])) if isinstance(r[c], list) else r[c] for c in cols])
    return recs, doctoral, out_rows


def summarise(out: Path, recs, doctoral, rows):
    C = collections.Counter
    s = {"generated_at": datetime.now(timezone.utc).isoformat(),
         "harvested_ndl_records": len(recs), "doctoral_ndl_records": len(doctoral),
         "clusters": len(rows), "by_label": C(r["history_label"] for r in rows)}
    for lab in ("history", "possible"):
        sub = [r for r in rows if r["history_label"] == lab]
        s[lab] = {
            "n": len(sub),
            "since_2013": sum(1 for r in sub if (r["year"] or 0) >= 2013),
            "by_access_category": C(r["access_category"] for r in sub),
            "by_access_category_since_2013": C(r["access_category"] for r in sub if (r["year"] or 0) >= 2013),
            "by_language": C(",".join(r["language"]) or "unknown" for r in sub),
            "by_year": dict(sorted(C(r["year"] for r in sub if r["year"]).items())),
            "no_year": sum(1 for r in sub if not r["year"]),
            "by_degree": C(r["degree_name"] for r in sub).most_common(30),
            "by_grantor": C(r["grantor"] for r in sub).most_common(60),
            "by_grantor_open_fulltext": C(r["grantor"] for r in sub if r["access_category"] == "open_fulltext_declared").most_common(40),
            "by_flag": C(f for r in sub for f in r["topic_flags"]),
        }
    s["other"] = {"n": sum(1 for r in rows if r["history_label"] == "other"),
                  "by_access_category": C(r["access_category"] for r in rows if r["history_label"] == "other")}
    s["history"]["by_basis"] = C(r["history_basis"] for r in rows if r["history_label"] == "history")
    s["history"]["by_basis_access"] = C(f'{r["history_basis"]}:{r["access_category"]}'
                                        for r in rows if r["history_label"] == "history")
    for name, key in (("logs/denominators.json", "denominators"), ("logs/harvest-coverage.json", "harvest_coverage")):
        f = out / name
        if f.exists():
            s[key] = json.loads(f.read_text())
    pf = out / "pilot-pdfs.csv"
    if pf.exists():
        import csv
        pr = list(csv.DictReader(open(pf, encoding="utf-8")))
        s["pilot"] = {"records": len({r["id"] for r in pr}), "files": len(pr),
                      "valid_pdf": sum(r["is_pdf"] == "True" and r["has_eof"] == "True" for r in pr),
                      "by_kind_pages": {k: sorted(int(r["pages"]) for r in pr if r["declared_kind"] == k and r["pages"])
                                        for k in sorted({r["declared_kind"] for r in pr})}}
    (out / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1, default=str))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    recs, doctoral, rows = build(out)
    s = summarise(out, recs, doctoral, rows)
    print(json.dumps({k: s[k] for k in ("harvested_ndl_records", "doctoral_ndl_records", "clusters", "by_label")},
                     ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
