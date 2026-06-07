import json
import csv
from datetime import datetime, date

# Expanded consulting firms (including big4, strategy, IT services)
CONSULTING = {
    'mindtree', 'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 'hcl',
    'tech mahindra', 'l&t infotech', 'mphasis', 'ibm services', 'deloitte', 'pwc',
    'pricewaterhousecoopers', 'ey', 'ernst young', 'kpmg', 'mckinsey', 'bain', 'bcg',
    'gartner', 'leidos', 'booz allen', 'cgi', 'lti', 'larsen & toubro infotech',
    'sapient', 'publicis sapient', 'virtusa', 'cyient', 'hexaware', 'zensar',
    'nagarro', 'globallogic', 'happiest minds', 'cvent', 'sutherland', 'conduent'
}

# Also check for any job where 'consult' appears in the description or title
# but that might cause false positives. Safer to submit as is.
# Expanded product companies (tech product companies, unicorns, big tech)
PRODUCT = {
    'google', 'microsoft', 'amazon', 'meta', 'facebook', 'uber', 'lyft', 'airbnb',
    'redrob', 'flipkart', 'razorpay', 'swiggy', 'zomato', 'oyo', 'netflix', 'spotify',
    'salesforce', 'adobe', 'oracle', 'sap', 'vmware', 'twitter', 'linkedin', 'nvidia',
    'amd', 'intel', 'workday', 'servicenow', 'stripe', 'square', 'paypal', 'pinterest',
    'snap', 'dropbox', 'atlassian', 'github', 'gitlab', 'digitalocean', 'cloudflare',
    'datadog', 'mongodb', 'elastic', 'confluent', 'snowflake', 'databricks', 'palantir',
    'robinhood', 'coinbase', 'block', 'chime', 'stripe', 'shopify', 'wayfair',
    'doordash', 'instacart', 'roblox', 'unity', 'epic games', 'twitch', 'discord'
}

TIER1 = {'mumbai','delhi','bangalore','hyderabad','chennai','kolkata','gurgaon','pune','noida','ahmedabad','jaipur'}

RANKING_KEYWORDS = ['ranking', 'retrieval', 'vector search', 'embedding', 'ndcg', 'mrr', 'map', 'recommendation', 'search', 'relevance', 'learning to rank', 'faiss', 'pinecone', 'weaviate', 'qdrant']

FOUNDING_YEARS = {
    'google':1998,'microsoft':1975,'amazon':1994,'facebook':2004,'meta':2004,
    'apple':1976,'netflix':1997,'adobe':1982,'salesforce':1999,'uber':2009,
    'lyft':2012,'airbnb':2008,'redrob':2020,'flipkart':2007,'razorpay':2014
}

def days_since(date_str):
    if not date_str: return 999
    try: return (date.today() - datetime.strptime(date_str, '%Y-%m-%d').date()).days
    except: return 999

def career_score(cand):
    total_months = product_months = consulting_months = 0
    has_ranking = False
    for job in cand.get('career_history', []):
        months = job.get('duration_months', 0)
        if months <= 0: continue
        total_months += months
        company = job.get('company', '').lower()
        desc = job.get('description', '').lower()
        title = job.get('title', '').lower()
        # Check product first (if matched, don't count as consulting)
        is_product = any(p in company for p in PRODUCT)
        if is_product:
            product_months += months
        elif any(c in company for c in CONSULTING):
            consulting_months += months
        # Also check for ranking keywords in description or title
        if any(kw in desc or kw in title for kw in RANKING_KEYWORDS):
            has_ranking = True
    if total_months == 0: return 0.0

    product_years = product_months / 12
    consulting_ratio = consulting_months / total_months if total_months > 0 else 0

    # Rule 1: if consulting ratio > 20% → reject
    if consulting_ratio > 0.2:
        return 0.0

    # Rule 2: if any consulting AND product_years < 5 → reject
    if consulting_months > 0 and product_years < 5:
        return 0.0

    # Rule 3: if consulting months exceed product months → reject
    if consulting_months > product_months:
        return 0.0

    product_ratio = product_months / total_months
    base = min(1.0, product_years / 5.0) * product_ratio
    if has_ranking:
        base = min(1.0, base + 0.4)
    return base

def behavioral_score(cand):
    sig = cand.get('redrob_signals', {})
    if not sig: return 0.0
    days = days_since(sig.get('last_active_date', ''))
    recency = max(0.0, 1.0 - (days / 180.0))
    response = sig.get('recruiter_response_rate', 0.0)
    interview = sig.get('interview_completion_rate', 0.0)
    open_flag = 1.0 if sig.get('open_to_work_flag') else 0.0
    saved = min(1.0, sig.get('saved_by_recruiters_30d', 0) / 10.0)
    notice = sig.get('notice_period_days', 180)
    notice_score = 1.0 if notice <= 30 else 0.3 if notice <= 60 else 0.0
    return recency * response * interview * open_flag * (0.5 + saved*0.5) * notice_score

def get_location(cand):
    if cand.get('current_location'): return cand['current_location']
    profile = cand.get('profile', {})
    if isinstance(profile, dict):
        for key in ['current_location', 'city', 'current_city', 'location']:
            if key in profile and profile[key]: return profile[key]
    signals = cand.get('redrob_signals', {})
    if isinstance(signals, dict):
        for key in ['preferred_location', 'city', 'location']:
            if key in signals and signals[key]: return signals[key]
    return ''

def location_score(cand):
    loc = get_location(cand).lower()
    willing = cand.get('redrob_signals', {}).get('willing_to_relocate', False)
    if 'pune' in loc or 'noida' in loc: return 1.0
    if any(city in loc for city in TIER1): return 0.9 if willing else 0.6
    return 0.6 if willing else 0.2

def is_honeypot(cand):
    skills = cand.get('skills', [])
    if sum(1 for s in skills if s.get('proficiency')=='expert' and s.get('years_used',0)==0) >= 3: return True
    for job in cand.get('career_history', []):
        company = job.get('company', '').lower()
        start_date = job.get('start_date', '')
        if start_date and len(start_date)>=4:
            start_year = int(start_date[:4])
            for co, founding in FOUNDING_YEARS.items():
                if co in company and start_year < founding: return True
    sig = cand.get('redrob_signals', {})
    if sig.get('profile_completeness_score',0) > 90 and sig.get('saved_by_recruiters_30d',0) == 0: return True
    total_months = sum(job.get('duration_months',0) for job in cand.get('career_history',[]))
    total_years = total_months/12
    titles = ' '.join([job.get('title','').lower() for job in cand.get('career_history',[])])
    if 'senior' in titles and total_years < 2: return True
    return False

def get_summary(cand):
    first = cand.get('career_history', [])[0] if cand.get('career_history') else {}
    total_months = sum(job.get('duration_months',0) for job in cand.get('career_history',[]))
    exp_years = round(total_months/12,1)
    loc = get_location(cand) or 'Unknown'
    sig = cand.get('redrob_signals', {})
    notice = sig.get('notice_period_days', 'Unknown')
    days = days_since(sig.get('last_active_date',''))
    active_text = 'very active' if days<=7 else 'active' if days<=30 else 'inactive'
    notice_text = 'short notice' if (isinstance(notice,int) and notice<=30) else 'long notice'
    has_ranking = any(any(kw in job.get('description','').lower() or kw in job.get('title','').lower() for kw in RANKING_KEYWORDS) for job in cand.get('career_history',[]))
    return {'exp_years':exp_years, 'location':loc, 'notice':notice, 'active_text':active_text, 'notice_text':notice_text, 'has_ranking':has_ranking, 'title':first.get('title','Unknown'), 'company':first.get('company','Unknown')}

print("Processing all candidates...")
rows = []
with open("data/candidates.jsonl", "rt") as f:
    for line in f:
        cand = json.loads(line)
        rows.append({
            'candidate_id': cand['candidate_id'],
            'career': career_score(cand),
            'behavioral': behavioral_score(cand),
            'location': location_score(cand),
            'honeypot': is_honeypot(cand),
            'summary': get_summary(cand)
        })

with open("features.csv", "w", newline='') as out:
    writer = csv.DictWriter(out, fieldnames=['candidate_id','career','behavioral','location','honeypot','exp_years','title','company','location_text','notice','active_text','notice_text','has_ranking'])
    writer.writeheader()
    for r in rows:
        writer.writerow({
            'candidate_id': r['candidate_id'],
            'career': r['career'],
            'behavioral': r['behavioral'],
            'location': r['location'],
            'honeypot': r['honeypot'],
            'exp_years': r['summary']['exp_years'],
            'title': r['summary']['title'],
            'company': r['summary']['company'],
            'location_text': r['summary']['location'],
            'notice': r['summary']['notice'],
            'active_text': r['summary']['active_text'],
            'notice_text': r['summary']['notice_text'],
            'has_ranking': r['summary']['has_ranking']
        })
print(f"Saved {len(rows)} candidates to features.csv")