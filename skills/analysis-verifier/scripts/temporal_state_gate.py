#!/usr/bin/env python3
"""Block historical-state claims based only on a current account-status snapshot.

Input: already-authorized derived SQL receipts. This does not query or alter any
remote source, add permissions, infer freeze times, or label a user high-risk.
"""
import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys

EFFECTIVE_FIELDS = {'frozen_at', 'status_effective_at', 'account_status_changed_at'}

def evaluate(user_schema, event_rows):
    cols = {r['column_name'] for r in user_schema}
    if not {'uid','account_status','created_at'}.issubset(cols):
        raise ValueError('user schema lacks core fields')
    if len(event_rows) != len({str(r['order_id']) for r in event_rows}):
        raise ValueError('non-unique order ids')
    events=[]
    for row in sorted(event_rows,key=lambda r:r['created_at']):
        if row['account_status']!='frozen' or row['direction']!='withdrawal':
            raise ValueError('wrong source cohort')
        t=datetime.fromisoformat(row['created_at'])
        done=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None
        if done is not None and done < t:
            raise ValueError('completed_at precedes created_at')
        events.append({
            'order_id':str(row['order_id']),'asset':row['asset'],
            'amount':str(Decimal(str(row['amount']))),
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
    amount=(str(sum((Decimal(str(r['amount'])) for r in events),Decimal(0)))
            if same_asset else None)
    return {
        'verdict':verdict,'in_source_effective_fields':present,
        'account_status_at_withdrawal_identified':False,
        'events':events,
        'completed_withdrawals':sum(r['recorded_order_status']=='completed' for r in events),
        'amount_sum_same_asset_only':amount,
        'asset':events[0]['asset'] if same_asset and events else None,
        'verified_claim':'A frozen account snapshot coexists with completed-status withdrawal records.',
        'blocked_claim':'The account was frozen at withdrawal approval or settlement.',
        'hypotheses_not_observations':[
            'Status changed to frozen before both withdrawals',
            'Status changed between the two withdrawals',
            'Status changed to frozen after both withdrawals'
        ],
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
