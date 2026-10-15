"""Validated relational analysis over local data; no generated code or SQL execution."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from .milestone_tools import TEAM_TOTAL_PATTERN, _period, PRECISION_NOTE


def number(value):
    try:
        result = float(str(value).replace(',', ''))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def relations(table, players, reports):
    """Keep source columns and add explicit identities and match evidence."""
    output = {'players': [dict(r, player=r.get('Player'), team=r.get('Squad')) for r in players],
              'teams': [dict(r, team=r.get('Squad')) for r in table],
              'matches': [], 'team_matches': [], 'player_matches': [], 'keeper_matches': []}
    seen = set()
    seen_rows = set()
    for report in reports:
        if report.get('competition') and 'premier league' not in str(report['competition']).casefold():
            continue
        try:
            day = date.fromisoformat(report['date']).isoformat()
            home, away = (report['teams'][s] for s in ('home', 'away'))
            hs, aws = number(home['score']), number(away['score'])
            if any(v is None or v < 0 or not v.is_integer() for v in (hs, aws)): continue
            if not home.get('name') or not away.get('name'): continue
        except (KeyError, TypeError, ValueError):
            continue
        identity = f"{day}|{home['name']}|{away['name']}"
        new_match = identity not in seen
        seen.add(identity)
        evidence = dict(date=day, match_id=identity, home_team=home['name'], away_team=away['name'],
                        home_score=hs, away_score=aws, total_goals=hs + aws)
        if new_match: output['matches'].append(evidence)
        for side, team, opponent, gf, ga in [('home', home, away, hs, aws), ('away', away, home, aws, hs)]:
            context = dict(evidence, team=team['name'], opponent=opponent['name'], side=side, matchweek=report.get('matchweek'), venue_time=report.get('venue_time'))
            if new_match: output['team_matches'].append(dict(context, goals_for=gf, goals_against=ga,
                goal_difference=gf-ga, points=3 if gf>ga else 1 if gf==ga else 0))
            for source, target in [('player_stats', 'player_matches'), ('keeper_stats', 'keeper_matches')]:
                unique = set()
                for row in report.get(source, {}).get(side, []):
                    name = str(row.get('Player') or '').strip()
                    row_key = (identity, side, target, name)
                    if not name or TEAM_TOTAL_PATTERN.fullmatch(name) or row_key in seen_rows: continue
                    seen_rows.add(row_key)
                    record = dict(row, **context, player=name)
                    if target == 'player_matches':
                        goals = number(row.get('Performance_Gls'))
                        if goals is None or goals < 0 or not goals.is_integer():
                            record['Performance_Gls'] = None
                    if target == 'keeper_matches':
                        keepers = report.get('keeper_stats', {}).get(side, [])
                        valid = len(keepers)==1 and number(row.get('Min'))==90 and number(row.get('Shot Stopping_GA'))==ga
                        record['keeper_clean_sheet'] = int(ga==0) if valid else None
                    output[target].append(record)
    return output


def discover_data(table, players, reports):
    data = relations(table, players, reports)
    return {'status': 'ok', 'competition': 'English Premier League', 'season': '2024/25',
        'datasets': {name: {'rows': len(rows), 'columns': sorted({k for r in rows for k in r})}
                     for name, rows in data.items()},
        'match_period': _period(reports),
        'coverage': f'{len(reports)} source reports; partial season. CSV snapshot dates are unknown; inspect MP for games covered.',
        'meanings': {'Performance_Gls': 'individual goals, excluding own goals', 'Performance_Ast': 'assists',
                     'Min': 'minutes played in this match', 'Playing Time_Min': 'aggregate minutes',
                     'GF': 'team goals scored', 'GA': 'team goals conceded', 'MP': 'team matches played'},
        'operations': ['filter', 'derive', 'group', 'sort', 'ordinal', 'cumulative', 'difference'],
        'identity': 'player plus team; names have no globally stable player IDs. Do not merge names across teams automatically.',
        'limitations': [PRECISION_NOTE, 'Missing matches prevent true season milestone and fastest-appearance claims.',
                       'Keeper rows provide minutes and goals allowed; partial clean sheets lack substitution timing.']}


def analyze_data(table, players, reports, dataset, steps):
    """Execute an ordered, bounded analysis plan. Discovery documents the step language."""
    data = relations(table, players, reports)
    if dataset not in data:
        return {'status': 'unsupported', 'reason': 'Unknown dataset', 'available': list(data)}
    rows = data[dataset]
    columns = {k for r in rows for k in r}
    original_count = len(rows)
    missing_goal_rows = sum(number(r.get('Performance_Gls')) is None for r in data['player_matches'])
    warnings = []
    if missing_goal_rows:
        warnings.append(f'{missing_goal_rows} player rows have missing or invalid goals; cumulative goals may be incomplete.')
    if len(data['matches']) != len(reports):
        warnings.append('Invalid, duplicate or out-of-competition match reports were excluded.')
    def require(fields):
        missing = set(fields) - columns
        if missing: raise ValueError('Unavailable columns: ' + ', '.join(sorted(missing)))
    try:
        if len(steps) > 30: raise ValueError('At most 30 steps are supported')
        for step in steps:
            op = step['op']
            if op == 'filter':
                field, value, operator = step['field'], step['value'], step.get('operator', 'eq')
                require([field])
                if operator not in ('eq','contains','in','ge','gt','le','lt'): raise ValueError('Unsupported filter operator')
                def matches(row):
                    actual = row.get(field)
                    if operator == 'eq':
                        a, b = number(actual), number(value)
                        return a == b if a is not None and b is not None else str(actual).casefold() == str(value).casefold()
                    if operator == 'contains': return str(value).casefold() in str(actual).casefold()
                    if operator == 'in': return actual in value
                    if operator not in ('ge','gt','le','lt'): raise ValueError('Unsupported filter operator')
                    a, b = number(actual), number(value)
                    if actual is None or actual == '': return False
                    if b is not None and a is None: return False
                    if a is None or b is None: a, b = str(actual), str(value)
                    return {'ge': a>=b, 'gt': a>b, 'le': a<=b, 'lt': a<b}[operator]
                rows = [r for r in rows if matches(r)]
            elif op == 'derive':
                fields, name, method = step['fields'], step['name'], step['method']
                require(fields)
                if method not in ('add','subtract','per90') or not fields or (method != 'add' and len(fields) != 2):
                    raise ValueError('Unsupported derivation or field count')
                for r in rows:
                    values = [number(r.get(f)) for f in fields]
                    value = None
                    if all(v is not None for v in values):
                        if method == 'add': value = sum(values)
                        elif method == 'subtract' and len(values)==2: value = values[0]-values[1]
                        elif method == 'per90' and len(values)==2: value = values[0]*90/values[1] if values[1]>0 else None
                        else: raise ValueError('Unsupported derivation')
                    r[name] = value
                columns.add(name)
            elif op in ('cumulative', 'difference'):
                groups, field, name = step['by'], step['field'], step['name']
                require(groups + [field, 'date', 'match_id'])
                buckets = defaultdict(list)
                for r in rows: buckets[tuple(r.get(k) for k in groups)].append(r)
                for bucket in buckets.values():
                    bucket.sort(key=lambda r: (r['date'], r['match_id']))
                    total, previous, observed_matches = 0, None, 0
                    for r in bucket:
                        value = number(r.get(field))
                        observed_matches += 1
                        r['observed_matches'] = observed_matches
                        r[name + '_before'] = total if op == 'cumulative' else previous
                        r[name] = None
                        if value is None:
                            total = None
                        if value is not None and total is not None:
                            total += value
                            r[name] = total if op=='cumulative' else value-previous if previous is not None else None
                            previous = value
                columns.update([name, name + '_before', 'observed_matches'])
            elif op == 'group':
                keys, metrics = step.get('by', []), step['metrics']
                require(keys + [m['field'] for m in metrics.values() if m.get('field')])
                for spec in metrics.values():
                    if spec['agg'] not in ('count','distinct','first','sum','mean','min','max'):
                        raise ValueError('Unsupported aggregation')
                buckets = defaultdict(list)
                if not keys and not rows: buckets[()] = []
                for r in rows: buckets[tuple(r.get(k) for k in keys)].append(r)
                grouped = []
                for key, bucket in buckets.items():
                    result = dict(zip(keys, key))
                    for label, spec in metrics.items():
                        values = [number(r.get(spec.get('field'))) for r in bucket]
                        valid = [v for v in values if v is not None]
                        method = spec['agg']
                        if method == 'count': value = len(bucket)
                        elif method == 'distinct': value = len({r.get(spec['field']) for r in bucket if r.get(spec['field']) is not None})
                        elif method == 'first': value = min((r.get(spec['field']) for r in bucket if r.get(spec['field']) is not None), default=None)
                        elif method in ('sum','mean','min','max'):
                            value = None if len(valid)!=len(bucket) or not valid else {'sum':sum, 'mean':lambda v:sum(v)/len(v), 'min':min, 'max':max}[method](valid)
                        else: raise ValueError('Unsupported aggregation')
                        result[label] = value
                    grouped.append(result)
                rows, columns = grouped, set(keys) | set(metrics)
            elif op == 'sort':
                fields = step['by']; require(fields)
                def sortkey(r):
                    return tuple((r.get(f) is None, number(r.get(f)) if number(r.get(f)) is not None else str(r.get(f))) for f in fields)
                present = [r for r in rows if all(r.get(f) is not None for f in fields)]
                absent = [r for r in rows if any(r.get(f) is None for f in fields)]
                rows = sorted(present, key=sortkey, reverse=step.get('descending', False)) + absent
            elif op == 'ordinal':
                field, position = step['field'], step['position']; require([field])
                if not isinstance(position, int) or position == 0: raise ValueError('Ordinal must be a nonzero integer')
                if rows and ((position > 0 and position <= len(rows)) or (position < 0 and -position <= len(rows))):
                    index = position-1 if position>0 else position
                    value = rows[index][field]
                    start = next(i for i, r in enumerate(rows, 1) if r[field] == value)
                    tied = [r for r in rows if r[field] == value]
                    rows = [dict(r, rank_start=start, rank_end=start + len(tied)-1) for r in tied]
                else: rows = []
            else: raise ValueError('Unsupported operation: ' + str(op))
    except (KeyError, TypeError, ValueError) as exc:
        return {'status': 'unsupported', 'reason': str(exc), 'dataset': dataset, 'steps': steps}
    return {'status': 'ok' if rows else 'not_found', 'dataset': dataset, 'steps': steps,
            'rows': rows, 'row_count': len(rows), 'source_rows': original_count,
            'data_period': _period(reports) if dataset not in ('players','teams') else None,
            'coverage_note': 'Partial match reports only; missing records may change totals and rankings.' if dataset not in ('players','teams') else '2024/25 aggregate snapshot; exact snapshot date unknown.',
            'precision_note': PRECISION_NOTE, 'identity_note': 'Names are qualified by team; no global player IDs.', 'warnings': warnings, 'support': 'partial' if warnings or dataset not in ('players','teams') else 'supported'}
