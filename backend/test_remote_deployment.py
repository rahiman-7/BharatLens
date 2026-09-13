"""
BharatLens — Remote Render Backend Automated Verification Suite
Usage: python test_remote_deployment.py https://<your-render-service>.onrender.com
"""

import sys
import json
import httpx

def run_remote_verification(base_url: str):
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/api/v1"):
        api_url = f"{base_url}/api/v1"
    else:
        api_url = base_url

    print("=" * 60)
    print(f"  BharatLens Remote Backend Verification")
    print(f"  Target: {api_url}")
    print("=" * 60)

    client = httpx.Client(timeout=30.0, follow_redirects=True)
    results = {}

    # 1. Health Endpoint
    print("\n[1/8] Testing /health...")
    try:
        r = client.get(f"{api_url}/health")
        print(f"  Status: HTTP {r.status_code}")
        data = r.json()
        print(f"  Database Status: {data.get('database')}")
        print(f"  Ingestion Telemetry: {json.dumps(data.get('ingestion'), indent=2)}")
        results["health"] = (r.status_code == 200 and data.get("status") == "healthy")
    except Exception as e:
        print(f"  [ERROR] Health check failed: {e}")
        results["health"] = False

    # 2. Categories Endpoint
    print("\n[2/8] Testing /categories...")
    try:
        r = client.get(f"{api_url}/categories")
        categories = r.json()
        print(f"  Status: HTTP {r.status_code} | Count: {len(categories)}")
        results["categories"] = (r.status_code == 200 and len(categories) == 11)
    except Exception as e:
        print(f"  [ERROR] Categories failed: {e}")
        results["categories"] = False

    # 3. States Endpoint
    print("\n[3/8] Testing /states...")
    try:
        r = client.get(f"{api_url}/states")
        states = r.json()
        print(f"  Status: HTTP {r.status_code} | Count: {len(states)}")
        results["states"] = (r.status_code == 200 and len(states) >= 28)
    except Exception as e:
        print(f"  [ERROR] States failed: {e}")
        results["states"] = False

    # 4. News Latest & Feed Isolation
    print("\n[4/8] Testing /news/latest...")
    try:
        r = client.get(f"{api_url}/news/latest?limit=10")
        feed = r.json()
        total = feed.get("total", 0)
        items = feed.get("items", [])
        print(f"  Status: HTTP {r.status_code} | Total Live Articles: {total} | Items: {len(items)}")
        has_demo = any(item.get("is_demo") for item in items)
        print(f"  Demo Articles Isolated: {'YES (No demo items in feed)' if not has_demo else 'NO (Demo items leaked)'}")
        results["news_latest"] = (r.status_code == 200 and total >= 390 and not has_demo)
    except Exception as e:
        print(f"  [ERROR] News latest failed: {e}")
        results["news_latest"] = False

    # 5. Stories / Clusters Endpoint
    print("\n[5/8] Testing /stories...")
    try:
        r = client.get(f"{api_url}/stories?limit=10")
        stories_data = r.json()
        total_clusters = stories_data.get("total", 0)
        print(f"  Status: HTTP {r.status_code} | Total Story Clusters: {total_clusters}")
        results["stories"] = (r.status_code == 200 and total_clusters >= 350)
    except Exception as e:
        print(f"  [ERROR] Stories failed: {e}")
        results["stories"] = False

    # 6. Historical Archive Time Machine
    print("\n[6/8] Testing /archive...")
    try:
        r = client.get(f"{api_url}/archive?date=2026-09-05&limit=5")
        archive_data = r.json()
        archived_total = archive_data.get("total", 0)
        print(f"  Status: HTTP {r.status_code} | Archived Items for 2026-09-05: {archived_total}")
        results["archive"] = (r.status_code == 200)
    except Exception as e:
        print(f"  [ERROR] Archive failed: {e}")
        results["archive"] = False

    # 7. Database Full Search
    print("\n[7/8] Testing /search...")
    try:
        r = client.get(f"{api_url}/search?q=ISRO&limit=5")
        search_data = r.json()
        search_total = search_data.get("total", 0)
        print(f"  Status: HTTP {r.status_code} | Search Matches for 'ISRO': {search_total}")
        results["search"] = (r.status_code == 200)
    except Exception as e:
        print(f"  [ERROR] Search failed: {e}")
        results["search"] = False

    # 8. Temporary Safe Auth & Me Check
    print("\n[8/8] Testing Authentication Flow...")
    try:
        # Test 401 on protected endpoint without token
        unauth_r = client.get(f"{api_url}/auth/me")
        print(f"  Unauthenticated /auth/me returns: HTTP {unauth_r.status_code} (Expected: 401)")
        results["auth_protection"] = (unauth_r.status_code == 401)
    except Exception as e:
        print(f"  [ERROR] Auth protection failed: {e}")
        results["auth_protection"] = False

    print("\n" + "=" * 60)
    print("  VERIFICATION SUMMARY")
    print("=" * 60)
    for check, passed in results.items():
        print(f"  - {check.upper()}: {'[PASS] 🟢' if passed else '[FAIL] 🔴'}")

    all_passed = all(results.values())
    print("\nOVERALL STATUS:", "🟢 ALL REMOTE CHECKS PASSED" if all_passed else "🔴 CHECKS FAILED")
    return all_passed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_remote_deployment.py <RENDER_URL>")
        sys.exit(1)
    url = sys.argv[1]
    success = run_remote_verification(url)
    sys.exit(0 if success else 1)
