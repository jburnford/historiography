import json,sys
for l in open(sys.argv[1]):
    r=json.loads(l)
    print('=====',r['id'],'|',r['query'])
    for c in r.get('crossref',[]): print('  CR',c['doi'],c['type'],'|',c['title'][:90],'|',c['container'][:40],'|',c['year'],'|',', '.join(c['authors'])[:80],'|',c['publisher'],c['vol'],c['issue'],c['page'],'| ABS' if c['abstract'] else '')
    for c in r.get('openlibrary',[]): print('  OL',c['key'],'|',c['title'][:80],'|',c['authors'],'|',c['first_year'],'|',c['publishers'][:3])
    for c in r.get('openalex',[]): print('  OA',c['doi'],c['type'],'|',c['title'][:90],'|',c['year'],'|',c['authors'],'| ABS' if c['abstract'] else '')
