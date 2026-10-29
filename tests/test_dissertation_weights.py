import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import dissertation_weights as dw  # noqa: E402


def synthetic_aha():
    """Every mapped department appears once (resolve() requires them); Michigan and Yale carry the output."""
    aha = [(f'o{i}', name, 1990) for i, name in enumerate(dw.DEPARTMENT.values())]
    mich, yale = 'o' + str(list(dw.DEPARTMENT).index('michigan')), 'o' + str(list(dw.DEPARTMENT).index('yale'))
    aha += [(mich, dw.DEPARTMENT['michigan'], 2015)] * 100 + [(yale, dw.DEPARTMENT['yale'], 2015)] * 300
    aha += [(mich, dw.DEPARTMENT['michigan'], 2022)] * 100
    return aha


def test_institutions_count_in_proportion_to_aha_output():
    rows = [(f'm{i}', 'michigan', 2015) for i in range(30)] + [(f'y{i}', 'yale', 2015) for i in range(10)]
    rows += [(f'n{i}', 'michigan', 2022) for i in range(20)]
    w, rep = dw.weights(rows, synthetic_aha())
    decade = [d for d, _, y in rows if y == 2015]
    yale = sum(w[d] for d, s, y in rows if s == 'yale') / sum(w[d] for d in decade)
    assert abs(yale - 0.75) < 1e-9  # Yale awards 300 of the 400 2010s PhDs
    assert abs(sum(w.values()) / len(w) - 1) < 1e-9
    assert rep['n'] == 60 and rep['n_eff'] < 60


def test_decades_follow_aha_totals_and_old_rows_are_excluded():
    rows = [(f'm{i}', 'michigan', 2015) for i in range(20)] + [(f'n{i}', 'michigan', 2022) for i in range(20)]
    rows += [('old', 'michigan', 1975), ('undated', 'michigan', None)]
    w, _ = dw.weights(rows, synthetic_aha())
    assert 'old' not in w and 'undated' not in w
    share_2010s = sum(w[d] for d, _, y in rows if y == 2015) / sum(w.values())
    assert abs(share_2010s - 400 / 500) < 1e-9


def test_unmapped_institutions_take_the_period_mean():
    rows = [(f'm{i}', 'michigan', 2015) for i in range(10)] + [('b1', 'base:hdl:1', 2015)]
    w, rep = dw.weights(rows, synthetic_aha())
    assert rep['unmapped'] == ['base:hdl:1']
    assert abs(w['b1'] - w['m0']) < 1e-9


def test_decade_coverage_reports_largest_institution():
    rows = [(f'm{i}', 'michigan', 2015) for i in range(3)] + [('y1', 'yale', 2015)]
    by = {c['period']: c for c in dw.decade_coverage(rows, synthetic_aha())}
    assert by[2010]['top'] == 'michigan' and by[2010]['top_share'] == 0.75
    assert by[2010]['aha_covered'] == 1.0
