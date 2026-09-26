# Security and privacy boundary

The app binds to literal loopback only. Requests require the expected Host; a supplied Origin must match the local origin. Mutating endpoints additionally require a random per-server session token, JSON content type and a 2 MB limit. Path traversal outside allowed build/static roots is rejected. One expensive generation job runs at a time. No telemetry or automatic update endpoint exists.

AI is off by default. Cloud calls require explicit confirmation; API credentials stay in server memory, expire and are omitted from files/logs/status replies. Endpoint strings reject embedded credentials, query strings and fragments. Local inference is literal loopback HTTP only; cloud uses HTTPS. Redirects are not followed with keys. Returned AI data is schema/field checked and never executed. A confirmed user-selected compatible endpoint necessarily receives the request/key; the user must trust that provider.

This is not an audited sandbox or multi-user service. Local malware, an already compromised browser/OS, hostile installed Python dependencies, memory extraction and system proxies/CA configuration are outside the tested boundary. Do not expose the server on a LAN or internet. Do not put credentials in project notes. Python strings cannot be promised securely zeroed from RAM. OS keychain support, stronger per-job resource budgets and a formal penetration test remain open.

Reference images are retained in browser memory and are not transmitted to an AI provider. Project saves contain only metadata; closing the page loses the image bytes. Explicit model-download scripts contact public model hosting and verify the expected file checksum, but no downloaded Python is executed by those scripts.

Tests in `test_security_ai.py` exercise host/origin/token checks, traversal, endpoint restrictions, no-redirect handling, key-status redaction, AI-off and confirmation gates. Mock/schema tests are not proof of real-provider security or native installer hardening.
