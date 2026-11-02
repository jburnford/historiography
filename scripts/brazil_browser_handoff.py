#!/usr/bin/env python3
"""Browser handoff list for Brazilian History doctorates behind bot checks (2026-11-01).

User, 2026-11-01: "there is a difference between you, an LLM agent and me, a real researcher
running scripts" -> yes to a browser handoff. FGV, UFSC, UNISINOS, UNICAMP, PUC/SP and PUC/RS
answer scripts with bot challenges or refusals (Anubis, Cloudflare, 403/468), which are not
circumvented. A person can open the pages in a browser and save the PDFs; this script lists the
CAPES doctorates of those universities so that can be done in order, and
``register_brazil_browser_downloads.py`` matches the saved files back to CAPES.

Output: ``<out>/browser-handoff/index.html`` (also copied next to the drop folder on E:) and
``queue.json``. Rows are newest first (older theses are often not digitized), with the item link
when the OAI harvest found one and a site-limited search link otherwise. A tick box per row is
kept in the browser's localStorage.

    python3 scripts/brazil_browser_handoff.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import html
import json
import shutil
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brazil_match_capes import capes_doctorates, doc_key  # noqa: E402

DROP = Path('/mnt/e/historiography-dissertation-pdfs/brazil-theses-2026-10-31/browser-drop')
DROP_WINDOWS = r'E:\historiography-dissertation-pdfs\brazil-theses-2026-10-31\browser-drop'
SITES = {  # CAPES acronym -> (label, search domain)
    'FGV/RJ': ('FGV (CPDOC)', 'repositorio.fgv.br'), 'FGV-RJ': ('FGV (CPDOC)', 'repositorio.fgv.br'),
    'UNICAMP': ('UNICAMP', 'repositorio.unicamp.br'), 'PUC/SP': ('PUC-SP', 'pucsp.br'),
    'PUC/RS': ('PUC-RS', 'pucrs.br'), 'PUCRS': ('PUC-RS', 'pucrs.br'),
    'UFSC': ('UFSC', 'repositorio.ufsc.br'), 'UNISINOS': ('UNISINOS', 'repositorio.jesuita.org.br'),
}


def search_link(domain, d):
    words = ' '.join(d['title'].split()[:10])
    q = f'site:{domain} "{d["author"].title()}" {words}'
    return 'https://www.google.com/search?q=' + urllib.parse.quote_plus(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    item_urls, pdf_urls = {}, {}
    # Direct file links from FGV's OAI feed in ORE format (the feed is open; the site is bot-checked).
    ore_path = out / 'oai' / 'FGV-ore-pdfs.json'
    ore = json.loads(ore_path.read_text()) if ore_path.exists() else {}
    cands = out / 'candidates.json'
    if cands.exists():
        for c in json.loads(cands.read_text()):
            item_urls[c['key']] = c['repository'].get('url')
            files = ore.get(c['repository'].get('oai_id') or '')
            if files:
                pdf_urls[c['key']] = files[0]
    downloaded = set()
    if (out / 'downloads.jsonl').exists():
        for line in open(out / 'downloads.jsonl', encoding='utf-8'):
            r = json.loads(line)
            if r['status'] == 'downloaded':
                downloaded.add(r['key'])
    groups = {}
    for d in capes_doctorates(out):
        if d['inst'] not in SITES:
            continue
        d['key'] = doc_key(d)
        if d['key'] in downloaded:
            continue
        label, domain = SITES[d['inst']]
        d['item_url'] = item_urls.get(d['key'])
        d['pdf_url'] = pdf_urls.get(d['key'])
        d['search_url'] = search_link(domain, d)
        groups.setdefault(label, []).append(d)
    for rows in groups.values():
        rows.sort(key=lambda d: (-d['year'], d['author']))
    hb = out / 'browser-handoff'
    hb.mkdir(exist_ok=True)
    queue = [dict(key=d['key'], inst=d['inst'], year=d['year'], author=d['author'], title=d['title'],
                  advisors=d['advisors'], pdf_url=d['pdf_url'], capes_url=d['fulltext_url'],
                  item_url=d['item_url'], search_url=d['search_url'])
             for rows in groups.values() for d in rows]
    (hb / 'queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=0))

    e = html.escape
    parts = [f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Brazil browser handoff</title>
<style>body{{font:14px system-ui,sans-serif;margin:2em;max-width:1200px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #ddd;padding:4px 6px;vertical-align:top;text-align:left}}tr.done{{opacity:.35}}
h2{{margin-top:2em}}code{{background:#f4f4f4;padding:1px 4px}}.old{{color:#777}}</style>
<h1>Brazilian History doctorates to save by hand</h1>
<p>Open a link, pass any check as you normally would, and save the thesis PDF into
<code>{e(DROP_WINDOWS)}</code>. Any filename is fine. Then run
<code>python3 scripts/register_brazil_browser_downloads.py</code>, which matches each file to its CAPES record by
title and author. Tick a row when it is done or not available (ticks stay in this browser).
Newest first; theses before about 2006 are often not online.</p>
<p><b>PDF</b> opens the file itself (FGV, from its repository feed). <b>item</b> is the repository record.
<b>search</b> is a search limited to the university's own sites, where an open thesis will be.
<b>CAPES record</b> (2013 on) opens the legacy Sucupira record. When it says "O trabalho possui divulgação
autorizada", click the file name under <i>Anexo</i> to download the PDF; when it says "não possui", there is no
file there, so try <b>search</b>.</p><p>"""]
    parts.append(' · '.join(f'<a href="#{e(k)}">{e(k)} ({len(v)})</a>' for k, v in groups.items()) + '</p>')
    for label, rows in groups.items():
        parts.append(f'<h2 id="{e(label)}">{e(label)}: {len(rows)} doctorates</h2><table>'
                     '<tr><th></th><th>Year</th><th>Author</th><th>Title</th><th>Advisor</th><th>Links</th></tr>')
        for d in rows:
            links = []
            if d['pdf_url']:
                links.append(f'<a href="{e(d["pdf_url"])}" target="_blank"><b>PDF</b></a>')
            if d['item_url']:
                links.append(f'<a href="{e(d["item_url"])}" target="_blank">item</a>')
            links.append(f'<a href="{e(d["search_url"])}" target="_blank"><b>search</b></a>')
            if d['fulltext_url']:
                # The legacy host shows the attachment ("Anexo") when the author authorized publication.
                legacy = d['fulltext_url'].replace('://sucupira.capes.gov.br/', '://sucupira-legado.capes.gov.br/')
                links.append(f'<a href="{e(legacy)}" target="_blank"><b>CAPES record</b></a>')
            cls = ' class="old"' if d['year'] < 2006 else ''
            parts.append(f'<tr data-key="{e(d["key"])}"{cls}><td><input type="checkbox"></td><td>{d["year"]}</td>'
                         f'<td>{e(d["author"].title())}</td><td>{e(d["title"])}</td>'
                         f'<td>{e("; ".join(d["advisors"]).title())}</td><td>{" ".join(links)}</td></tr>')
        parts.append('</table>')
    parts.append("""<script>
for (const tr of document.querySelectorAll('tr[data-key]')) {
  const k = 'br-handoff:' + tr.dataset.key, box = tr.querySelector('input');
  box.checked = localStorage.getItem(k) === '1'; tr.classList.toggle('done', box.checked);
  box.addEventListener('change', () => { localStorage.setItem(k, box.checked ? '1' : '0'); tr.classList.toggle('done', box.checked); });
}
</script></html>""")
    page = '\n'.join(parts)
    (hb / 'index.html').write_text(page, encoding='utf-8')
    DROP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(hb / 'index.html', DROP.parent / 'browser-handoff.html')  # exFAT: no chmod
    print(f'{len(queue)} doctorates: ' + ', '.join(f'{k} {len(v)}' for k, v in groups.items()))
    print(f'page: {hb / "index.html"} (copy: {DROP.parent / "browser-handoff.html"})')
    print(f'save PDFs to: {DROP_WINDOWS}')


if __name__ == '__main__':
    main()
