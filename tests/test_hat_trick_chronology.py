"""Regression for the existing tool's full chronology and conditional caveats."""
import json
import pytest
from agent.milestone_tools import get_scoring_milestones
from agent.data_loader import load_matches


def report(day, player, goals=3):
    return {'date':day, 'teams':{'home':{'name':'A','score':goals},
                               'away':{'name':'B','score':0}},
            'player_stats':{'home':[{'Player':player,'Performance_Gls':goals}], 'away':[]}}


@pytest.mark.parametrize('ordinal,rank', [('first',1),('second',2),('3rd',3),('last',3),('latest',3)])
def test_hat_trick_tool_exposes_requested_date_rank_without_timestamp_excuse(ordinal,rank):
    reports=[report('2024-12-22','Last'), report('2024-08-18','First'),
             report('2024-09-01','Second',4)]
    result=json.loads(get_scoring_milestones(reports,f'Who scored the {ordinal} hat-trick?'))
    assert result['status']=='ok' and result['qualifying_events']==3
    assert [r['player'] for r in result['rows']]==['First','Second','Last']
    selected=[r for r in result['rows'] if r['rank_start']<=rank<=r['rank_end']]
    assert len(selected)==1 and selected[0]['player']==['First','Second','Last'][rank-1]
    assert 'timestamps' not in json.dumps(result)
    assert '2024-08-18 through 2024-12-22' in result['coverage_note']
    assert 'cannot establish the final hat-trick' in result['coverage_note']


def test_timestamp_limitation_belongs_only_to_tied_events():
    reports=[report('2024-08-18','Early'), report('2024-09-01','Tie A'),
             report('2024-09-01','Tie B'), report('2024-12-22','Late')]
    result=json.loads(get_scoring_milestones(reports,'Who scored the latest hat-trick?'))
    assert 'precision_note' not in result
    for row in result['rows']:
        if row['date']=='2024-09-01':
            assert (row['rank_start'],row['rank_end'])==(2,3)
            assert 'timestamps' in row['precision_note']
        else:
            assert 'precision_note' not in row
    assert result['rows'][-1]['rank_start']==4


def test_real_report_chronology_matches_raw_player_match_goals():
    reports=load_matches()
    expected=sorted((r['date'],p['Player']) for r in reports for side in ('home','away')
                    for p in r['player_stats'][side]
                    if not p['Player'].endswith('Players') and p['Performance_Gls']>=3)
    result=json.loads(get_scoring_milestones(reports,'Who scored the last hat-trick?'))
    assert sorted((r['date'],r['player']) for r in result['rows'])==expected
    assert result['rows'][-1]['date']==expected[-1][0]
    assert result['data_period']=={'start':'2024-08-18','end':'2024-12-22'}
