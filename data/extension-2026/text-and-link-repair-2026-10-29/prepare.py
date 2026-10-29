"""Prepare revision 1.216: restore missing spaces and remove links to blocked source routes.

Inputs beside this script:
  respacing.json   {"table|id|field": [[old, new], ...]} — space-only insertions, reviewed per record
                   (field is a JSON path for node text); applied in order.
  link-repair.json {"url_sets": {source_id: doi-or-null}, "text_edits": [{table, id, field, old, new}],
                    "name_fixes": [[old, new], ...]} — applied after respacing.
Writes batch.json (edge_revisions, source_field_sets, text_revisions, field_sets) guarded against the
exact 1.215 graph, then `scripts/apply_person_entries.py DIR --build` freezes the packet.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.source_hosts import blocked_url, findings  # noqa: E402


def space_only(old, new):
    i = 0
    for ch in new:
        if i < len(old) and ch == old[i]:
            i += 1
        elif ch != ' ':
            return False
    return i == len(old)


def get(obj, path):
    for p in path:
        obj = obj[p]
    return obj


def main():
    g = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    assert g['revision_history'][-1]['version'] == '1.215', g['revision_history'][-1]['version']
    resp = json.loads((HERE / 'respacing.json').read_text())
    links = json.loads((HERE / 'link-repair.json').read_text())
    nodes = {n['id']: n for n in g['nodes']}
    edges = {e['id']: e for e in g['edges']}
    sources = {s['id']: s for s in g['sources']}
    new = {}   # (table, id, field-or-path-json) -> text

    def current(table, rid, field):
        key = (table, rid, field)
        if key in new:
            return new[key]
        if table == 'edges':
            return edges[rid][field]
        if table == 'sources':
            src = sources[rid]
            return src['verification']['note'] if field == 'verification.note' else src[field]
        return get(nodes[rid], json.loads(field))

    for key, pairs in resp.items():
        table, rid, field = key.split('|', 2)
        before = text = current(table, rid, field)
        for old, rep in pairs:
            assert space_only(old, rep), (key, old, rep)
            if old in text:
                text = text.replace(old, rep)
            else:   # already covered by a longer pair applied earlier
                assert rep in text, (key, old, rep)
        assert space_only(before, text), key
        new[(table, rid, field)] = text
    for old, rep in links.get('name_fixes', []):
        for k, t in list(new.items()):
            if old in t:
                new[k] = t.replace(old, rep)
    for te in links.get('text_edits', []):
        k = (te['table'], te['id'], te['field'])
        t = current(*k)
        assert t.count(te['old']) == 1, (k, te['old'][:60])
        new[k] = t.replace(te['old'], te['new'])

    batch = dict(revision='1.216', baseline_revision='1.215', date='2026-10-29', batch_dir='group-revision-1.216',
                 persons=[], extras=[], source_merges={},
                 summary=('Text and link repair: missing spaces restored in relationship texts, evidence notes, '
                          'source records and node text (space-only insertions, reviewed per record), and links to '
                          'blocked source routes replaced with DOI links or removed, with route names dropped from notes.'),
                 authorization=("User, 2026-10-29: 'we need to fix the missing spaces'; 'either remove the links or "
                                "replace them with links to the paywalled content'; 'fixing and pushing the sol work is the priority'."),
                 rationale=('Revisions 1.200–1.215 drafted many notes without spaces between words; the site shows these '
                            'texts. No wording changes beyond inserted spaces, two restored hyphens in names and the '
                            'neutral rewording of route names. Sources keep their readings; only the route is no longer named.'),
                 edge_revisions={}, source_field_sets=[], text_revisions=[], field_sets=[])
    # original values straight from the 1.215 graph
    def orig(table, rid, field):
        if table == 'edges':
            return edges[rid][field]
        if table == 'sources':
            return (sources[rid].get('verification') or {}).get('note') if field == 'verification.note' else sources[rid].get(field)
        return get(nodes[rid], json.loads(field))
    chron = {}
    for (table, rid, field), text in sorted(new.items()):
        o = orig(table, rid, field)
        if text == o:
            continue
        if table == 'edges':
            batch['edge_revisions'].setdefault(rid, {})[field] = text
        elif table == 'sources':
            batch['source_field_sets'].append(dict(id=rid, field=field, expect=o, value=text))
        else:
            path = json.loads(field)
            node = nodes[rid]
            if path[0] == 'chronology':
                c = chron.setdefault(rid, deepcopy(node['chronology']))
                get(c, path[1:-1])[path[-1]] = text
            elif len(path) == 1 and path[0] in ('date_label', 'scope_note'):
                batch['field_sets'].append(dict(node=rid, field=path[0], expect=o, value=text))
            elif len(path) == 1:
                batch['text_revisions'].append(dict(node=rid, field=path[0], old=o, new=text))
            elif path[0] == 'representative_people' and len(path) == 3:
                batch['text_revisions'].append(dict(node=rid, person_id=node['representative_people'][path[1]]['person_id'],
                                                    field=path[2], old=o, new=text))
            elif path[0] == 'strands' and len(path) == 3:
                batch['text_revisions'].append(dict(node=rid, strand=node['strands'][path[1]]['id'], field=path[2], old=o, new=text))
            else:
                raise SystemExit(f'unsupported node path {rid} {path}')
    for rid, c in chron.items():
        batch['field_sets'].append(dict(node=rid, field='chronology', expect=nodes[rid]['chronology'], value=c))
    for sid, doi in links['url_sets'].items():
        s = sources[sid]
        assert blocked_url(s['url']), sid
        batch['source_field_sets'].append(dict(id=sid, field='url', expect=s['url'], value=f'https://doi.org/{doi}' if doi else None))
    # every remaining blocked link or route name must be handled
    left = []
    for s in g['sources']:
        for f in ('url', 'title', 'citation', 'verification.note'):
            k = ('sources', s['id'], f)
            if f == 'url':
                v = next((x['value'] for x in batch['source_field_sets'] if x['id'] == s['id'] and x['field'] == 'url'), s.get('url'))
            else:
                v = new.get(k, orig(*k))
            if isinstance(v, str) and findings(v):
                left.append((s['id'], f, findings(v)[:2]))
    for e in g['edges']:
        for f in ('relationship', 'evidence_note'):
            v = new.get(('edges', e['id'], f), e.get(f))
            if isinstance(v, str) and findings(v):
                left.append((e['id'], f, findings(v)[:2]))
    (HERE / 'remaining-findings.json').write_text(json.dumps(left, indent=1, ensure_ascii=False) + '\n')
    (HERE / 'batch.json').write_text(json.dumps(batch, indent=1, ensure_ascii=False) + '\n')
    print(f"edges {len(batch['edge_revisions'])}, source sets {len(batch['source_field_sets'])}, "
          f"text revisions {len(batch['text_revisions'])}, field sets {len(batch['field_sets'])}, unresolved route findings {len(left)}")


if __name__ == '__main__':
    main()
