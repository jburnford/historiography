#!/usr/bin/env python3
"""Cache Crossref's journal registry metadata for a selected ISSN list."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from harvest_ahr_crossref import write_json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=Path('data/history-journals-crossref-2026-09-21'))
    args=parser.parse_args()
    selection=json.loads((args.work/'selection.json').read_text())
    out=args.work/'journal-registry';out.mkdir(exist_ok=True)
    for j in selection['journals']:
        path=out/(j['key']+'.json')
        if path.exists():result=json.loads(path.read_text())
        else:
            attempts=[]
            for issn in j['issns']:
                url='https://api.crossref.org/journals/'+issn
                response=subprocess.run(['curl','--fail','--location','--silent','--show-error','--max-time','55','--retry','3',url],capture_output=True,text=True)
                attempts.append({'url':url,'exit_code':response.returncode,'error':response.stderr.strip()})
                if response.returncode==6:raise RuntimeError(response.stderr)
                if response.returncode==0:break
                time.sleep(2)
            result={'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'attempts':attempts,'message':json.loads(response.stdout)['message'] if response.returncode==0 else {}}
            write_json(path,result);time.sleep(1)
        m=result['message']
        print(json.dumps({'key':j['key'],'requested':j['label'],'crossref_title':m.get('title'),'issns':m.get('ISSN'),'total_dois':m.get('counts',{}).get('total-dois')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
