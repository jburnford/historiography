#!/usr/bin/env python3
"""Separate review flags; never rewrite the frozen ORCID evidence index."""
import csv
import json
from pathlib import Path
import duckdb
from harvest_history_orcids import DEFAULT
from harvest_ahr_crossref import sha,write_json

def audit(work=DEFAULT):
    database=work/'generated/v1/orcid-index.duckdb'
    demo='0000-0002-1825-0097'
    with duckdb.connect(str(database),read_only=True) as c:
        rows=c.execute('SELECT orcid_id,count(DISTINCT family_name) family_variants,count(DISTINCT record_id) publication_records FROM orcid_evidence GROUP BY 1 HAVING family_variants>=5 OR orcid_id=? ORDER BY family_variants DESC',[demo]).fetchall()
        flags=[{'orcid_id':oid,'flag':'known_demonstration_account' if oid==demo else 'multiple_family_names_review_needed',
            'exclude_from_person_grounding':oid==demo,'distinct_deposited_family_names':names,'publication_records':records,
            'review_status':'confirmed_demo_account' if oid==demo else 'unreviewed_name_variants',
            'evidence_url':'https://orcid.org/'+demo if oid==demo else '',
            'note':'Official profile identifies a fictional demonstration account; retain deposited evidence but exclude as a real-person grounding.' if oid==demo else 'Five or more distinct deposited family-name strings. May reflect attribution errors, transliteration, name changes, or metadata variants; no identity decision accepted.'}
            for oid,names,records in rows]
        path=work/'orcid-quality-flags.csv'
        with path.open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(flags[0]));writer.writeheader();writer.writerows(flags)
        c.execute("COPY (SELECT i.*,CASE WHEN i.orcid_id IN (SELECT orcid_id FROM orcid_evidence GROUP BY 1 HAVING count(DISTINCT family_name)>=5) THEN 'name_variants_need_review' ELSE 'unreviewed' END AS grounding_review_status FROM orcid_identifiers i WHERE orcid_id!=$demo ORDER BY publication_records DESC,orcid_id) TO $destination (HEADER)",{'demo':demo,'destination':str(work/'orcid-identifiers-for-review.csv')})
        counts={'deposited_unique_identifiers':c.execute('SELECT count(*) FROM orcid_identifiers').fetchone()[0],
                'known_demo_identifiers_excluded':c.execute('SELECT count(*) FROM orcid_identifiers WHERE orcid_id=?',[demo]).fetchone()[0],
                'non_demo_identifiers_for_review':c.execute('SELECT count(*) FROM orcid_identifiers WHERE orcid_id!=?',[demo]).fetchone()[0],
                'additional_name_variant_flags':sum(f['orcid_id']!=demo for f in flags),
                'metadata_hash_mismatches':c.execute('SELECT count(*) FROM records WHERE sha256(raw_metadata_json)!=metadata_sha256').fetchone()[0]}
    result={'checked_on':'2026-09-22','index_sha256':sha(database),'counts':counts,'flags':flags,
        'note':'Broad discovery includes neighbouring disciplines; these are deposited ORCID candidates, not a census of professional historians. One public demonstration profile was checked; no bulk ORCID profile or employment validation performed.',
        'primary_sources':['https://orcid.org/0000-0002-1825-0097','https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier']}
    write_json(work/'quality-review.json',result)
    print(json.dumps(counts,indent=2))

if __name__=='__main__':audit()
