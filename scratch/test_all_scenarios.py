import requests
import json

scenarios = [
    'legitimate', 'channel', 'forgery', 'impersonation',
    'replay', 'unauthorized', 'ledger', 'timing_oracle',
    'adaptive_x', 'transferability', 'blind'
]

print("Testing all 11 scenarios against backend...")
for s in scenarios:
    try:
        r = requests.post(f'http://localhost:8000/v1/testbed/attack/{s}', timeout=15)
        d = r.json()
        print(f"[{s:15}] code={r.status_code} actual={d.get('actual_outcome')} detected={d.get('detected')} findings={len(d.get('findings', []))}")
        if s in ['timing_oracle', 'adaptive_x', 'transferability', 'blind']:
            print(f"   -> findings: {d.get('findings')}")
            print(f"   -> reason: {d.get('reason')}")
    except Exception as e:
        print(f"[{s:15}] ERROR: {e}")
