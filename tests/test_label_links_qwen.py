import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import label_links_qwen as M  # noqa: E402

KEYS = ['p-1', 'p-22']


def test_own_book_prefix_only():
    books = {'p-1': ['The English Reformation : religion and cultural adaptation']}
    assert M.own_book('Review of The English Reformation: Religion and Cultural Adaptation', books['p-1'])
    assert M.own_book('Review of Enforcing the English Reformation in Ireland', books['p-1']) is None
    assert M.own_book('Review of The Short Book', ['The Short Book']) is None       # main title too short


def test_hard_rules_exclude_reviewed_author_on_reviews_only():
    cands = [dict(key='p-1', label='Jones, Norman L.'), dict(key='p-22', label='Jones, N.')]
    books = {'p-1': ['The English Reformation : religion and cultural adaptation']}
    keep, excl = M.apply_hard_rules('Norman Jones', 'reviewer', 'article', 'Review of The English Reformation', cands, books)
    assert [c['key'] for c in keep] == ['p-22'] and excl[0]['key'] == 'p-1'
    keep, excl = M.apply_hard_rules('Norman Jones', 'author', 'book', 'The English Reformation', cands, books)
    assert len(keep) == 2 and not excl


def test_schema_enum_and_order():
    s = M.schema_for(KEYS)
    assert s['properties']['decision']['enum'] == KEYS + ['not-keyed', 'cannot-tell']
    assert list(s['properties'])[:3] == ['facts', 'reason', 'decision']       # evidence before the answer
    assert M.schema_for([])['properties']['decision']['enum'] == ['not-keyed', 'cannot-tell']


def test_parse_verdict_strict():
    ok = json.dumps(dict(facts=['rare name'], reason='Only A fits.', decision='p-22', confidence='high', duplicate_keys=['p-1', 'p-9', 'p-22']))
    v = M.parse_verdict(ok, KEYS)
    assert v['decision'] == 'p-22' and v['duplicate_keys'] == ['p-1']
    assert M.parse_verdict('```json\n' + ok + '\n```', KEYS)['decision'] == 'p-22'
    assert M.parse_verdict('<think>x</think>' + ok, KEYS)['decision'] == 'p-22'
    assert M.parse_verdict(ok.replace('p-22"', 'p-3"', 1), KEYS) is None           # key not shown
    assert M.parse_verdict('not json', KEYS) is None
    assert M.parse_verdict(None, KEYS) is None
    nk = M.parse_verdict(json.dumps(dict(decision='not-keyed', duplicate_keys=['p-1'], confidence='odd')), KEYS)
    assert nk['duplicate_keys'] == [] and nk['confidence'] == 'low'


def test_vote_policies():
    assert M.vote(['p-1', 'p-1', 'not-keyed'], 'majority') == 'p-1'
    assert M.vote(['p-1', 'p-1', 'not-keyed'], 'unanimous') == 'cannot-tell'
    assert M.vote(['p-1', 'p-1', 'p-22'], 'majority') == 'cannot-tell'
    assert M.vote(['not-keyed', 'not-keyed', 'cannot-tell'], 'majority') == 'not-keyed'
    assert M.vote(['not-keyed', 'cannot-tell'], 'majority') == 'cannot-tell'
    assert M.vote(['error', 'error'], 'majority') == 'error'


def test_decide_and_outcome():
    ps = {0: dict(decision='p-1'), 1: dict(decision='p-1'), 2: dict(decision='cannot-tell'), 3: dict(decision='p-1')}
    assert M.decide(ps, 'greedy') == ('p-1', '1/1')
    assert M.decide(ps, 'sc-majority')[0] == 'p-1'
    assert M.decide(ps, 'sc-unanimous')[0] == 'cannot-tell'
    assert M.decide({0: dict(decision='p-1'), 1: dict(decision='p-22'), 2: dict(decision='p-22')}, 'greedy+sc')[0] == 'cannot-tell'
    assert M.decide({0: dict(decision='not-keyed', rule=True)}, 'sc-majority') == ('not-keyed', '1/1')
    assert M.outcome('p-1', 'p-5', 'p-5') == 'right-link'
    assert M.outcome('p-1', '', 'p-22') == 'dangerous'
    assert M.outcome('not-keyed', '', 'p-22') == 'dangerous'
    assert M.outcome('cannot-tell', '', 'p-22') == 'link-on-undecided'
    assert M.outcome('p-1', '', 'cannot-tell') == 'missed'
    assert M.outcome('not-keyed', '', 'not-keyed') == 'agree-nolink'


def test_permute_deterministic_and_complete():
    d = dict(item='X1', candidates=[dict(key=f'p-{i}') for i in range(5)])
    assert M.permute(d, 0) is d
    a, b = M.permute(d, 2), M.permute(d, 2)
    assert [c['key'] for c in a['candidates']] == [c['key'] for c in b['candidates']]
    assert sorted(c['key'] for c in a['candidates']) == sorted(c['key'] for c in d['candidates'])


def test_user_message_hides_openalex_ids():
    d = dict(item='X1', printed_name='A. B', role='author', title='T', kind='article', year=2000, venue='', work='w-1',
             other_names='', printed_aff='', more=0,
             candidates=[dict(key='p-1', label='B, A', ids='lcnaf openalexx3 wd', aff=[], works_n=0, works=[], facts=[])])
    t = M.user_message(d, facts=False)
    assert 'openalex' not in t and 'lcnaf wd' in t and 'linkage facts' not in t
