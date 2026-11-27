#!/usr/bin/env python3
"""Block historical-state claims based only on a current account-status snapshot.

Input: already-authorized derived SQL receipts. This does not query or alter any
remote source, add permissions, infer freeze times, or label a user high-risk.
"""
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
import json
from pathlib import Path
import sys

EFFECTIVE_FIELDS = {'frozen_at', 'status_effective_at', 'account_status_changed_at'}

def exact_amount_sum(amounts):
    least_place = min(amount.as_tuple().exponent for amount in amounts)
    highest_place = max(amount.adjusted() for amount in amounts)
    with localcontext() as context:
        context.prec = max(context.prec, highest_place - least_place + 1 + len(str(len(amounts))))
        return str(sum(amounts, Decimal(0)))

def evaluate(user_schema, event_rows):
    cols = {r['column_name'] for r in user_schema}
    if not {'uid','account_status','created_at'}.issubset(cols):
        raise ValueError('user schema lacks core fields')
    if len(event_rows) != len({str(r['order_id']) for r in event_rows}):
        raise ValueError('non-unique order ids')
    dated = [(datetime.fromisoformat(row['created_at']), row) for row in event_rows]
    if len({created.utcoffset() is not None for created, _ in dated}) > 1:
        raise ValueError('mixed offset-aware and naive order times')
    events=[]
    amounts=[]
    for t, row in sorted(dated, key=lambda item: item[0]):
        if row['account_status']!='frozen' or row['direction']!='withdrawal':
            raise ValueError('wrong source cohort')
        done=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None
        if done is not None and (done.utcoffset() is None) != (t.utcoffset() is None):
            raise ValueError('inconsistent completion timestamp timezone')
        if done is not None and done < t:
            raise ValueError('completed_at precedes created_at')
        try:
            amount = Decimal(str(row.get('amount')))
        except InvalidOperation as error:
            raise ValueError(f"invalid amount for order {row['order_id']}") from error
        if not amount.is_finite():
            raise ValueError(f"non-finite amount for order {row['order_id']}")
        amounts.append(amount)
        events.append({
            'order_id':str(row['order_id']),'asset':row['asset'],
            'amount':str(amount),
            'created_at':row['created_at'],'completed_at':row.get('completed_at'),
            'recorded_order_status':row['status'],
            'recorded_account_status':row['account_status'],
            'account_status_at_order_time':'UNKNOWN',
            'restrictions_in_force_at_order_time':'UNKNOWN',
            'external_settlement':'UNKNOWN'
        })
    present=sorted(cols.intersection(EFFECTIVE_FIELDS))
    verdict='IN_SOURCE_FIELD_REVIEW_REQUIRED' if present else 'NEEDS_AUTHORIZED_HISTORY'
    same_asset=len({r['asset'] for r in events})==1
    amount_sum = exact_amount_sum(amounts) if same_asset else None
    completed = sum(event['recorded_order_status'] == 'completed' for event in events)
    if completed:
        verified_claim = 'A frozen account snapshot coexists with completed-status withdrawal records.'
    elif events:
        verified_claim = 'Withdrawal records are present; none has completed status.'
    else:
        verified_claim = 'No withdrawal records were supplied.'
    hypotheses = []
    if events:
        hypotheses.append('Status changed to frozen before the first withdrawal')
        if len(events) > 1:
            hypotheses.append('Status changed between withdrawals')
        hypotheses.append('Status changed to frozen after the last withdrawal')
    return {
        'verdict':verdict,'in_source_effective_fields':present,
        'account_status_at_withdrawal_identified':False,
        'events':events,
        'completed_withdrawals':completed,
        'amount_sum_same_asset_only':amount_sum,
        'asset':events[0]['asset'] if same_asset and events else None,
        'verified_claim':verified_claim,
        'blocked_claim':'The account was frozen at withdrawal approval or settlement.',
        'hypotheses_not_observations':hypotheses,
        'missing_evidence':[
            'Authenticated account status-transition event log and effective times',
            'Applicable withdrawal restriction/exception policy as of order time',
            'Authorization, release, payout and settlement events for the order IDs'
        ],
        'next_step':('Inspect the allowed source effective-time column' if present else
                     'Request authorized status-transition audit log; do not repeat four-table SQL'),
        'case_disposition':'OPEN_EVIDENCE_GAP_NOT_CONFIRMED_VIOLATION',
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('evidence_dir',type=Path)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    root=args.evidence_dir
    schema=json.loads((root/'schema_users.json').read_text(encoding='utf-8'))
    rows=json.loads((root/'frozen_account_activity.json').read_text(encoding='utf-8'))
    result=evaluate(schema,rows)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'temporal_state_gate':result['verdict'],
        'completed_withdrawals':result['completed_withdrawals'],
        'amount_sum':result['amount_sum_same_asset_only'],
        'historical_status_proven':result['account_status_at_withdrawal_identified']},
        ensure_ascii=False))
    return 0

if __name__=='__main__':sys.exit(main())
