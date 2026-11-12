"""Analysis 9 (added 2026-11-11 evening): citations of translations, by thesis country.

Since 2026-11-11 a thesis citation of a translation or a later edition is rolled up to the original work
(data/graph/cited-works/editions.csv.gz: corpus work -> canonical work, relation translation / edition, cited language).
Compilations with no single original (Microfisica do poder ...) are corpus: works of their own (relation compilation).

Tables:
- 09-translation-share-by-country.csv: share of each country's strict citations (rows of strict-citations.csv.gz)
  that go to a corpus work identified as a translation / a later edition / a compilation, of all citations and of
  matched citations; share of theses citing at least one; the cited languages.
- 09-top-translated-works-by-country.csv: per country, the original works most often cited in translation (distinct
  theses citing a translation of it), with the theses citing it in any form and the share that comes via translation.
- 09-top-translated-authors-by-country.csv: the same for people (credits of the original work: key log, and key log +
  linked), distinct theses.
Lower bounds: a translation counts only when the 2026-11-11 crosswalk identified it (LC translation clusters for
matched works; the author-constrained route for unmatched ones, aimed at the Portuguese and Spanish canon). Distinct
citing documents throughout; no sum over person keys.
"""
import json

import pandas as pd

from common import connect, out

CC = ['CA', 'US', 'GB', 'FR', 'BR', 'MX']
TOPN = 30


def main():
    con = connect()
    con.execute(f"""CREATE TEMP TABLE c AS SELECT c.did, c.work_id,
            CASE WHEN d.country IN {tuple(CC)} THEN d.country ELSE 'other' END country,
            t.relation, t.cited_language lang, m.gkey, (x.work_id IS NOT NULL) AS is_matched,
            (m.route='compilation') AS compilation
        FROM cit c JOIN diss d ON d.id=c.did LEFT JOIN tx t USING (work_id) LEFT JOIN cmap m USING (work_id)
        LEFT JOIN xw x USING (work_id)""")
    share = con.execute("""SELECT country, count(*) citations, sum(is_matched::INT) AS matched,
            sum((relation='translation')::INT) translation, sum((relation='edition')::INT) later_edition,
            sum(compilation::INT) compilation, count(DISTINCT did) theses,
            count(DISTINCT CASE WHEN relation='translation' THEN did END) theses_citing_translation,
            count(DISTINCT CASE WHEN relation='translation' OR compilation THEN did END) theses_citing_transl_or_comp
        FROM c GROUP BY ROLLUP(country) ORDER BY country NULLS LAST""").df()
    share['country'] = share['country'].fillna('all')
    share['translation_share_of_all'] = (share.translation / share.citations).round(4)
    share['translation_share_of_matched'] = (share.translation / share.matched).round(4)
    share['edition_share_of_all'] = (share.later_edition / share.citations).round(4)
    share['compilation_share_of_all'] = (share.compilation / share.citations).round(4)
    share['theses_citing_translation_share'] = (share.theses_citing_translation / share.theses).round(4)
    share['theses_citing_transl_or_comp_share'] = (share.theses_citing_transl_or_comp / share.theses).round(4)
    langs = con.execute("""SELECT country, coalesce(nullif(lang,''),'?') lang, count(*) n FROM c
        WHERE relation='translation' GROUP BY ALL""").df()
    top_lang = langs.sort_values('n', ascending=False).groupby('country').apply(
        lambda g: '; '.join(f'{r.lang} {r.n}' for r in g.head(4).itertuples()), include_groups=False)
    share['translation_languages_top4'] = share['country'].map(top_lang)
    share.to_csv(out('09-translation-share-by-country.csv'), index=False)
    print(share.to_string())

    # works most cited in translation, per country
    con.execute("""CREATE TEMP TABLE tw AS SELECT country, gkey, count(DISTINCT did) theses_via_translation
        FROM c WHERE relation='translation' AND gkey IS NOT NULL GROUP BY 1,2""")
    con.execute("""CREATE TEMP TABLE anyw AS SELECT country, gkey, count(DISTINCT did) theses_any_form FROM c
        WHERE gkey IN (SELECT gkey FROM tw) GROUP BY 1,2""")
    nth = dict(con.execute("SELECT country, count(DISTINCT did) FROM c GROUP BY 1").fetchall())
    w = con.execute("""SELECT tw.country, tw.gkey AS key, g.label, g.year, tw.theses_via_translation, a.theses_any_form
        FROM tw JOIN anyw a USING (country, gkey) LEFT JOIN gw g ON g.key=tw.gkey""").df()
    w['share_of_country_theses'] = (w.theses_any_form / w.country.map(nth)).round(4)
    w['via_translation_share'] = (w.theses_via_translation / w.theses_any_form).round(4)
    w['rank'] = w.groupby('country')['theses_via_translation'].rank(method='first', ascending=False).astype(int)
    w = w[w['rank'] <= TOPN].sort_values(['country', 'rank'])
    w.to_csv(out('09-top-translated-works-by-country.csv'), index=False)

    # people most cited in translation (credits of the original work), key log and key log + linked
    rows = []
    for cred, hw in (('keylog', "('authored','edited')"),
                     ('keylog+linked', "('authored','edited','linked_authored','linked_edited')")):
        p = con.execute(f"""WITH t AS (SELECT c.country, k.person, count(DISTINCT c.did) via
                    FROM c JOIN cred k ON k.work=c.gkey AND k.how IN {hw}
                    WHERE c.relation='translation' OR c.compilation GROUP BY 1,2),
                 a AS (SELECT c.country, k.person, count(DISTINCT c.did) n_any
                    FROM c JOIN cred k ON k.work=c.gkey AND k.how IN {hw}
                    WHERE k.person IN (SELECT person FROM t) GROUP BY 1,2)
            SELECT t.country, t.person AS key, pr.label, t.via theses_via_translation_or_compilation,
                   a.n_any theses_any_matched_work
            FROM t JOIN a USING (country, person) LEFT JOIN person pr ON pr.key=t.person""").df()
        p['credits'] = cred
        p['via_share'] = (p.theses_via_translation_or_compilation / p.theses_any_matched_work).round(4)
        p['share_of_country_theses_any'] = (p.theses_any_matched_work / p.country.map(nth)).round(4)
        p['rank'] = p.groupby('country')['theses_via_translation_or_compilation'].rank(
            method='first', ascending=False).astype(int)
        rows.append(p[p['rank'] <= TOPN])
    pa = pd.concat(rows).sort_values(['credits', 'country', 'rank'])
    pa.to_csv(out('09-top-translated-authors-by-country.csv'), index=False)
    pd.set_option('display.width', 250)
    print(w[w.country.isin(['BR', 'FR', 'MX'])].groupby('country').head(10).to_string())
    print(pa[(pa.credits == 'keylog+linked') & pa.country.isin(['BR', 'FR', 'MX', 'US'])].groupby('country').head(10).to_string())
    out('09-summary.json').write_text(json.dumps(dict(share=share.to_dict('records')), indent=1, default=str))


if __name__ == '__main__':
    main()
