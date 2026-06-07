import csv

W_CAREER = 0.50
W_BEHAVIORAL = 0.45
W_LOCATION = 0.05

candidates = []
with open("features.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['career'] = float(row['career'])
        row['behavioral'] = float(row['behavioral'])
        row['location'] = float(row['location'])
        row['honeypot'] = row['honeypot'] == 'True'
        row['exp_years'] = float(row['exp_years'])
        row['has_ranking'] = row['has_ranking'] == 'True'
        base_score = (W_CAREER * row['career'] +
                      W_BEHAVIORAL * row['behavioral'] +
                      W_LOCATION * row['location'])
        cand_num = int(row['candidate_id'].split('_')[1])
        tie_breaker = cand_num / 1_000_000_000.0
        row['score'] = base_score + tie_breaker
        if row['honeypot']:
            row['score'] = -1.0
        candidates.append(row)

candidates.sort(key=lambda x: x['score'], reverse=True)
top100 = candidates[:100]

def reasoning(cand):
    parts = [f"{cand['exp_years']:.0f} years experience"]
    if cand['has_ranking']:
        parts.append("built ranking/search systems")
    if cand['career'] >= 0.8:
        parts.append("strong product background")
    elif cand['career'] >= 0.5:
        parts.append("some product experience")
    else:
        parts.append("consulting-focused")
    if cand['behavioral'] >= 0.7:
        parts.append("highly active, short notice")
    else:
        parts.append(f"{cand['active_text']}, {cand['notice_text']}")
    loc = cand['location_text'].lower()
    if 'pune' in loc or 'noida' in loc:
        parts.append("based in Pune/Noida")
    elif cand['location'] >= 0.7:
        parts.append("Tier-1 city, willing to relocate")
    elif cand['location_text'] != 'Unknown':
        parts.append(f"based in {cand['location_text']}")
    return ". ".join(parts) + "."

with open("submission.csv", "w", newline='') as out:
    writer = csv.writer(out)
    writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
    for rank, cand in enumerate(top100, 1):
        writer.writerow([cand['candidate_id'], rank, cand['score'], reasoning(cand)])

print("Saved submission.csv – expanded consulting/product keywords, strict rejection rules")