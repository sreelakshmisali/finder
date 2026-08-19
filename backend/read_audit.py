import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('audit_candidates.json') as f:
    jobs = json.load(f)
print(f'Total candidates: {len(jobs)}')
print()
hdr = f"{'#':<4} {'PROV':<14} {'TITLE':<44} {'COMPANY':<16} {'TOTAL':>6} {'T':>5} {'Sk':>5} {'D':>5} {'Pen':>5} {'ACCEPT':<8} MATCHED_TERMS / PENALTIES"
print(hdr)
print('-'*155)
for i, r in enumerate(jobs, 1):
    mt = ','.join(r['matched_terms'])[:28]
    pen = ('  PEN:' + ','.join(r['penalties'])[:35]) if r['penalties'] else ''
    acc = 'ACCEPT' if r['accepted'] else 'REJECT'
    print(f"{i:<4} {r['provider']:<14} {r['title'][:43]:<44} {r['company'][:15]:<16} {r['total_score']:>6.1f} {r['title_score']:>5.1f} {r['skill_score']:>5.1f} {r['desc_score']:>5.1f} {r['penalty_pts']:>5.1f} {acc:<8} {mt}{pen}")

print()
print('=== REJECTED ONLY with full reasons ===')
for i, r in enumerate(jobs, 1):
    if r['accepted']:
        continue
    print(f"\n#{i} [{r['provider']}] {r['title']!r} @ {r['company']!r}")
    print(f"   score={r['total_score']} title={r['title_score']} skill={r['skill_score']} desc={r['desc_score']} loc={r['loc_score']} pen={r['penalty_pts']}")
    print(f"   desc_len={r['description_len']}  skills={r['required_skills']}")
    print(f"   matched={r['matched_terms']}  missing={r['missing_terms']}")
    print(f"   matched_domains={r['matched_domains']}  conflicting={r['conflicting_domains']}")
    print(f"   penalties={r['penalties']}")
    print(f"   reasons={r['reasons'][:5]}")
