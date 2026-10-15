"""Synthetic edge cases and source-backed integration, without provider calls."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from agent.analytics import analyze_data, discover_data, relations
from agent.milestone_tools import scoring_events
from agent.data_loader import load_datasets


def report(day, goals, away_goals=None):
    return {'date':f'2024-08-{day:02}', 'teams':{'home':{'name':'A','score':sum(goals.values())},
        'away':{'name':'B','score':sum((away_goals or {}).values())}},
        'player_stats':{'home':[{'Player':p,'Performance_Gls':g,'Min':90} for p,g in goals.items()],
                        'away':[{'Player':p,'Performance_Gls':g,'Min':90} for p,g in (away_goals or {}).items()]}}


def test_all_hat_tricks_ordinals_and_source_evidence():
    reports = [report(3,{'P':4}), report(1,{'P':3}), report(2,{'Q':3}),
               report(4,{'R':1}),report(5,{'R':1}),report(6,{'R':1})]
    assert scoring_events(reports)['qualifying_events']==3
    for position, player, goals in [(1,'P',3),(2,'Q',3),(3,'P',4)]:
        result=scoring_events(reports,position=position)
        row=result['rows'][0]
        assert (row['player'],row['Performance_Gls'])==(player,goals)
        assert row['match_id'] and row['opponent']=='B'
    assert scoring_events(reports,position=-1)['rows'][0]['date']=='2024-08-03'
    assert scoring_events(reports,position=10)['status']=='not_found'
    assert scoring_events(reports)['rows']==scoring_events(list(reversed(reports)))['rows']


def test_multiple_in_match_and_date_ties_never_invent_order():
    reports=[report(1,{'P':3,'Q':4},{'R':3})]
    for position in (1,2,3):
        result=scoring_events(reports,position=position)
        assert result['status']=='ambiguous'
        assert len(result['rows'])==3


@pytest.mark.parametrize('threshold,expected',[(3,['P','Q','R']),(5,['Q'])])
def test_configurable_cumulative_thresholds(threshold,expected):
    reports=[report(1,{'P':2,'Q':0,'R':0}),report(2,{'P':1,'Q':2,'R':0}),
             report(3,{'P':0,'Q':3,'R':0}),report(4,{'P':1,'Q':0,'R':3})]
    result=scoring_events(reports,threshold)
    assert [r['player'] for r in result['rows']]==expected
    for i,p in enumerate(expected,1): assert scoring_events(reports,threshold,i)['rows'][0]['player']==p


def test_threshold_ties_missing_records_and_dates():
    reports=[report(1,{'P':3,'Q':3})]
    assert scoring_events(reports,3,2)['status']=='ambiguous'
    broken=report(2,{'R':0}); broken['player_stats']['home'][0]['Performance_Gls']=None
    result=analyze_data([],[],reports+[broken],'player_matches',[])
    assert result['warnings'] and result['data_period']['end']=='2024-08-02'
    assert 'Partial' in result['coverage_note']
    with pytest.raises(ValueError): scoring_events(reports,0)


def test_general_composition_rankings_rates_and_missing_fields():
    players=[{'Player':'P','Squad':'A','Performance_Gls':3,'Playing Time_Min':180},
             {'Player':'P','Squad':'B','Performance_Gls':1,'Playing Time_Min':0}]
    steps=[{'op':'derive','name':'rate','method':'per90','fields':['Performance_Gls','Playing Time_Min']},
           {'op':'filter','field':'Playing Time_Min','operator':'gt','value':0},
           {'op':'sort','by':['rate'],'descending':True}]
    result=analyze_data([],players,[],'players',steps)
    assert result['rows'][0]['rate']==1.5
    assert len(analyze_data([],players,[],'players',[])['rows'])==2
    assert analyze_data([],players,[],'players',[{'op':'filter','field':'player','value':'Missing'}])['status']=='not_found'
    assert analyze_data([],players,[],'players',[{'op':'sort','by':['clean_sheets']}])['status']=='unsupported'
    assert analyze_data([],players,[],'players',[{'op':'eval'}])['status']=='unsupported'
    teams=analyze_data([],[],[report(1,{'P':3})],'team_matches',[
        {'op':'group','by':['team'],'metrics':{'goals':{'agg':'sum','field':'goals_for'}}},
        {'op':'sort','by':['goals'],'descending':True}])
    assert teams['rows'][0]=={'team':'A','goals':3}


def test_clean_sheet_requires_full_keeper_evidence():
    r=report(1,{'P':0}); r['keeper_stats']={'home':[{'Player':'K','Min':90,'Shot Stopping_GA':0}]}
    assert relations([],[],[r])['keeper_matches'][0]['keeper_clean_sheet']==1
    r['keeper_stats']['home'][0]['Min']=60
    assert relations([],[],[r])['keeper_matches'][0]['keeper_clean_sheet'] is None


def test_repository_events_independently_verified():
    table,players,reports,_=load_datasets()
    raw=sorted((r['date'],p['Player'],p['Performance_Gls']) for r in reports for side in ('home','away')
               for p in r['player_stats'][side] if 'Players' not in p['Player'] and p['Performance_Gls']>=3)
    result=scoring_events(reports)
    assert sorted((r['date'],r['player'],r['Performance_Gls']) for r in result['rows'])==raw
    assert [scoring_events(reports,position=i)['rows'][0]['player'] for i in (1,2,3)]==['Erling Haaland','Noni Madueke','Erling Haaland']
    assert discover_data(table,players,reports)['datasets']['players']['rows']==574


def test_ask_passes_context_and_preserves_composed_graph_answer(monkeypatch):
    import agent.workflow as workflow
    table,players,reports,_=load_datasets(); calls=[]
    class Graph:
        def invoke(self,state):
            calls.append(state)
            # Mock planner performs separate event selection and opponent aggregation.
            chosen=scoring_events(reports,position=2)['rows'][0]
            grouped=analyze_data(table,players,reports,'player_matches',[
                {'op':'filter','field':'Performance_Gls','operator':'ge','value':3},
                {'op':'group','by':['opponent'],'metrics':{'count':{'agg':'count'}}}])
            return {'messages':[SimpleNamespace(content=json.dumps({'selected':chosen,'conceded':grouped['rows']}))]}
    monkeypatch.setattr(workflow,'_runtime',lambda:(Graph(),players,reports,table))
    answer=workflow.ask('Who scored the second hat-trick and which teams conceded most?',max_len=10000,
                        history=[{'role':'user','content':'Use the available reports'}])
    assert json.loads(answer)['selected']['player']=='Noni Madueke'
    assert json.loads(answer)['conceded']
    assert calls[0]['messages'][0]['content']=='Use the available reports'


@pytest.mark.parametrize('position',[1,2,3])
def test_ask_ordinal_and_threshold_with_mock_planner(monkeypatch,position):
    import agent.workflow as workflow
    table,players,reports,_=load_datasets()
    class Graph:
        def invoke(self,state):
            threshold=10 if '10 goals' in state['messages'][-1].content else None
            return {'messages':[SimpleNamespace(content=json.dumps(scoring_events(reports,threshold,position)))]}
    monkeypatch.setattr(workflow,'_runtime',lambda:(Graph(),players,reports,table))
    for question in (f'Who scored hat-trick number {position}?',f'Who reached 10 goals in position {position}?'):
        result=json.loads(workflow.ask(question,max_len=20000)); assert result['rows']

def test_real_graph_routes_and_combines_tools_with_mock_models(monkeypatch):
    """Exercise the real StateGraph and tool dispatch, without calling a provider."""
    import agent.workflow as workflow
    import langchain.agents
    import langchain.chat_models
    from langchain_core.messages import AIMessage, ToolMessage
    monkeypatch.setattr(workflow, 'get_settings', lambda **kwargs: SimpleNamespace(main_model='mock',strong_model='mock'))
    selected_tools=[]; calls=[]
    class Analyst:
        def __init__(self,tools): self.tools={t.name:t for t in tools}
        def invoke(self,state):
            calls.append(state)
            discovered=self.tools['inspect_data'].invoke({})
            assert 'player_matches' in discovered['datasets']
            result=self.tools['analyze'].invoke({'dataset':'player_matches','steps':[
                {'op':'filter','field':'Performance_Gls','operator':'ge','value':3},
                {'op':'sort','by':['date']}, {'op':'ordinal','field':'date','position':2}]})
            evidence=result['rows'][0]
            supporting=self.tools['analyze'].invoke({'dataset':'matches','steps':[
                {'op':'filter','field':'match_id','value':evidence['match_id']}]})
            return {'messages':[AIMessage(content=json.dumps({'event':evidence,'match':supporting['rows'][0]}))]}
    def create(**kwargs):
        selected_tools.append([t.name for t in kwargs['tools']]); return Analyst(kwargs['tools'])
    class Supervisor:
        def bind_tools(self,tools): return self
        def invoke(self,messages):
            if isinstance(messages[-1],ToolMessage): return AIMessage(content=messages[-1].content)
            return AIMessage(content='',tool_calls=[{'name':'call_stats_analyst','args':{'query':messages[-1].content},'id':'analysis-1','type':'tool_call'}])
    monkeypatch.setattr(langchain.agents,'create_agent',create)
    monkeypatch.setattr(langchain.chat_models,'init_chat_model',lambda *args:Supervisor())
    workflow._runtime.cache_clear()
    try:
        answer=json.loads(workflow.ask('Who scored the second hat-trick and what was the score?',max_len=20000))
        assert answer['event']['player']=='Noni Madueke'
        assert answer['match']['away_score']==6
        assert len(calls)==1
        assert all('analyze' in tools and 'inspect_data' in tools for tools in selected_tools)
    finally:
        workflow._runtime.cache_clear()


def test_notebook_general_analysis_parity():
    import typing, re
    from datetime import date
    notebook=json.loads((Path(__file__).parents[1]/'notebook.ipynb').read_text(encoding='utf-8'))
    table,players,reports,_=load_datasets()
    namespace={'tool':lambda f:f,'Any':typing.Any,'Iterable':typing.Iterable,'Optional':typing.Optional,
               'date':date,'json':json,'re':re,'TABLE_ROWS':table,'PLAYER_ROWS':players,'MATCH_REPORTS':reports}
    exec(compile(''.join(notebook['cells'][9]['source']),'notebook tools','exec'),namespace)
    for position in (1,2,3,-1):
        assert namespace['scoring_events'](reports,position=position)==scoring_events(reports,position=position)
    for target in (3,5,10,15):
        assert namespace['scoring_events'](reports,target)==scoring_events(reports,target)
    assert namespace['discover_data'](table,players,reports)==discover_data(table,players,reports)


def test_streamlit_forwards_followup_history(monkeypatch):
    import app
    from unittest.mock import Mock
    mock=Mock(return_value='answer'); monkeypatch.setattr(app,'ask',mock)
    history=[{'role':'user','content':'Who scored the first hat-trick?'}]
    assert app.run_chat_query('And the second?',history)=='answer'
    mock.assert_called_once_with('And the second?',history=history)

def test_source_rankings_scores_and_contributions():
    table,players,reports,_=load_datasets()
    result=analyze_data(table,players,reports,'matches',[{'op':'sort','by':['total_goals'],'descending':True},
        {'op':'ordinal','field':'total_goals','position':1}])
    expected=max(r['teams']['home']['score']+r['teams']['away']['score'] for r in reports)
    assert all(r['total_goals']==expected for r in result['rows'])
    result=analyze_data(table,players,reports,'players',[
        {'op':'derive','name':'contributions','method':'add','fields':['Performance_Gls','Performance_Ast']},
        {'op':'sort','by':['contributions'],'descending':True}])
    assert result['rows'][0]['contributions']==max(int(r['Performance_Gls'])+int(r['Performance_Ast']) for r in players)
    result=analyze_data(table,players,reports,'teams',[{'op':'sort','by':['GA']}, {'op':'ordinal','field':'GA','position':1}])
    assert all(int(r['GA'])==min(int(t['GA']) for t in table) for r in result['rows'])


def test_improvement_zeros_missing_values_and_numeric_sort():
    reports=[report(1,{'P':0}),report(2,{'P':3}),report(3,{'P':1})]
    result=analyze_data([],[],reports,'player_matches',[
        {'op':'difference','by':['player','team'],'field':'Performance_Gls','name':'improvement'},
        {'op':'sort','by':['improvement'],'descending':True}])
    assert [r['improvement'] for r in result['rows']]==[3,-2,None]
    bad=report(2,{'P':0});bad['player_stats']['home'][0]['Performance_Gls']=None
    result=analyze_data([],[],[reports[0],bad,reports[2]],'player_matches',[
        {'op':'cumulative','by':['player','team'],'field':'Performance_Gls','name':'total'}])
    assert [r['total'] for r in result['rows']]==[0,None,None]
    assert result['support']=='partial'
