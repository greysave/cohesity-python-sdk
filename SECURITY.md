# Security

* Report vulnerabilities privately to the maintainer; do not open public issues with credentials or cluster details.
* Never commit cluster addresses, credentials, tokens, CA keys, or exported reports. `.gitignore` excludes `.env`, keys, and spreadsheets.
* The library verifies TLS by default; disabling verification is an explicit opt-in and unsuitable for production.
* Test fixtures are synthetic (`*.example.invalid`, invented names and values). Keep it that way.
