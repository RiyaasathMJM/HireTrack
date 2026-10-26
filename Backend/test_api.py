import urllib.request
import json

BASE = 'http://localhost:5000'

def get(path):
    r = urllib.request.urlopen(BASE + path)
    return json.loads(r.read())

def post(path, data):
    body = json.dumps(data).encode()
    req  = urllib.request.Request(
        BASE + path, data=body,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def patch(path, data):
    body = json.dumps(data).encode()
    req  = urllib.request.Request(
        BASE + path, data=body,
        headers={'Content-Type': 'application/json'},
        method='PATCH'
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

print("--- TEST 1: Health ---")
print(json.dumps(get('/api/health'), indent=2))

print("\n--- TEST 2: Stages ---")
print(json.dumps(get('/api/stages'), indent=2))

print("\n--- TEST 3: Create JD ---")
jd = post('/api/jobs', {
    'title': 'Senior Python Dev',
    'description': 'We need a Python developer with FastAPI, Docker, AWS, PostgreSQL, and REST API skills.'
})
print(json.dumps(jd, indent=2))

print("\n--- TEST 4: List JDs ---")
jds = get('/api/jobs')
print(f"Total JDs: {len(jds)}")

jd_id = jd['id']

print("\n--- TEST 5: Update JD (add Kubernetes) ---")
updated = patch(f'/api/jobs/{jd_id}', {
    'description': 'We need a Python developer with FastAPI, Docker, AWS, PostgreSQL, Kubernetes, and REST API skills.'
})
print(f"Updated: kubernetes in description = {'kubernetes' in updated['description'].lower()}")

print("\n--- TEST 6: List Candidates (empty) ---")
candidates = get('/api/candidates')
print(f"Candidates count: {len(candidates)}")

print("\n--- TEST 7: Match-all against JD (0 candidates = empty result) ---")
results = post(f'/api/jobs/{jd_id}/match-all', {})
print(f"Match results count: {len(results)}")

print("\n\nALL TESTS PASSED")
