# b12

Application submitter for the B12 Full Stack Engineer (Backend Emphasis) role.

Builds a canonical JSON payload, signs it with HMAC-SHA256, POSTs it to the
B12 application endpoint, and returns the receipt. Stdlib only.

## Layout

- `submit.py` — the submitter.
- `test_submit.py` — unit tests for canonicalization and signing.
- `.github/workflows/apply.yml` — `workflow_dispatch` that runs the tests, the
  submitter, and uploads the receipt as a build artifact.

## Running

### GitHub Actions

Set three repository secrets:

- `APPLICANT_NAME`
- `APPLICANT_EMAIL`
- `RESUME_LINK`

Then trigger **Submit application** from the Actions tab. It defaults to a
dry run — full pipeline except the POST, so you can verify that secrets are
wired and the signed payload looks right without spending a submission. Set
the `dry_run` input to `false` to submit for real. `repository_link` and
`action_run_link` are derived from the standard `GITHUB_*` env vars. The
receipt is uploaded as a build artifact on real runs only.

### Locally

```bash
APPLICANT_NAME="Jon Karlsen" \
APPLICANT_EMAIL="karlsen.jon@icloud.com" \
RESUME_LINK="https://jon-karlsen.dev/resume.pdf" \
REPOSITORY_LINK="https://github.com/jon-karlsen/b12" \
ACTION_RUN_LINK="https://github.com/jon-karlsen/b12/actions/runs/0" \
python submit.py
```

## Tests

```bash
python -m unittest discover
```

---

Jon Karlsen · [jon-karlsen.dev](https://jon-karlsen.dev)
