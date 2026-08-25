#!/usr/bin/env python3
"""Google Safe Browsing + Search Console CLI for isakzvegelj.com.

Uses only Python stdlib + the `openssl` CLI (for RS256 JWT signing).
No third-party packages, no secrets stored in this file.

Usage:
  # 1) Definitive Safe Browsing verdict (needs a Safe Browsing API key):
  tools/gsc.py sb <API_KEY> [url]

  # 2) Search Console actions (needs the service-account JSON key path):
  tools/gsc.py sites <sa.json>                 # list accessible properties
  tools/gsc.py sitemaps <sa.json>              # list submitted sitemaps
  tools/gsc.py submit <sa.json> <sitemap-url>  # submit a sitemap
  tools/gsc.py inspect <sa.json> <url>         # URL inspection (index status)

Service-account JSON must have Search Console API enabled in its project and
the service-account email added as an Owner in Search Console.
"""
import base64, json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error

SB_SCOPE = "https://www.googleapis.com/auth/webmasters"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def http(method: str, url: str, body=None, headers=None):
    req = urllib.request.Request(url, method=method, data=body)
    req.add_header("User-Agent", "personal-site-gsc-tool/1.0")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def mint_token(sa_path: str, scope: str) -> str:
    sa = json.load(open(sa_path))
    hdr = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    now = int(time.time())
    claims = b64url(json.dumps({
        "iss": sa["client_email"], "scope": scope,
        "aud": TOKEN_URL, "iat": now, "exp": now + 3600,
    }).encode())
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
        f.write(sa["private_key"]); pem = f.name
    try:
        sig = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", pem],
            input=f"{hdr}.{claims}".encode(), capture_output=True, check=True,
        ).stdout
    finally:
        os.unlink(pem)
    assertion = f"{hdr}.{claims}.{b64url(sig)}"
    status, resp = http("POST", TOKEN_URL, urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode(), {"Content-Type": "application/x-www-form-urlencoded"})
    if status != 200:
        sys.exit(f"token exchange failed: {status} {resp}")
    return resp["access_token"]


def cmd_sb(key: str, url="https://isakzvegelj.com/"):
    body = json.dumps({
        "client": {"clientId": "personal-site", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING",
                            "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }).encode()
    status, resp = http("POST",
                        f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}",
                        body, {"Content-Type": "application/json"})
    print(f"HTTP {status}")
    if resp.get("matches"):
        for m in resp["matches"]:
            print("FLAGGED:", m.get("threatType"), "·", m.get("platformType"))
        print("VERDICT: ON Safe Browsing list -> request review in Search Console.")
    else:
        print("VERDICT: CLEAN — domain is NOT on any Safe Browsing list.")


def gsc(sa: str, method: str, path: str, body=None):
    tok = mint_token(sa, SB_SCOPE)
    url = f"https://www.googleapis.com/webmasters/v3/{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {tok}"}
    if data:
        headers["Content-Type"] = "application/json"
    return http(method, url, data, headers)


def cmd_sites(sa):
    status, resp = gsc(sa, "GET", "sites")
    print(f"HTTP {status}")
    for s in resp.get("siteEntry", []):
        print(f"  {s['permissionLevel']:>10}  {s['siteUrl']}")
    if not resp.get("siteEntry"):
        print("  (no properties — add the service-account email as Owner in Search Console)")


def cmd_sitemaps(sa):
    site = "https://isakzvegelj.com/"
    status, resp = gsc(sa, "GET", f"sites/{urllib.parse.quote(site, safe='')}/sitemaps")
    print(f"HTTP {status}")
    for s in resp.get("sitemap", []):
        print(f"  {s.get('type','?'):>12}  {s.get('errors',0)} errors / {s.get('warnings',0)} warn  {s['path']}")
    if not resp.get("sitemap"):
        print("  (no sitemaps submitted yet)")


def cmd_submit(sa, feedpath):
    site = "https://isakzvegelj.com/"
    status, resp = gsc(sa, "PUT",
                       f"sites/{urllib.parse.quote(site, safe='')}/sitemaps/{urllib.parse.quote(feedpath, safe='')}")
    print(f"HTTP {status}" + ("  — sitemap submitted ✓" if status in (200, 201) else f"  {resp}"))


def cmd_inspect(sa, url):
    tok = mint_token(sa, SB_SCOPE)
    status, resp = http("POST", "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                        json.dumps({"inspectionUrl": url, "siteUrl": "https://isakzvegelj.com/"}).encode(),
                        {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    print(f"HTTP {status}")
    r = resp.get("inspectionResult", {})
    idx = r.get("indexStatusResult", {})
    print("  verdict:", idx.get("verdict"), "| indexing:", idx.get("coverageState"))
    if "securityIssues" in json.dumps(resp):
        print("  raw:", json.dumps(resp, indent=2)[:800])


if __name__ == "__main__":
    cmds = {"sb": (cmd_sb, 1), "sites": (cmd_sites, 0), "sitemaps": (cmd_sitemaps, 0),
            "submit": (cmd_submit, 1), "inspect": (cmd_inspect, 1)}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    fn, extra = cmds[sys.argv[1]]
    args = sys.argv[2:]
    if len(args) < extra + 1:
        sys.exit(__doc__)
    fn(*args)
