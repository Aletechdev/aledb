# GitHub CI/CD Short-Term Roadmap

A staged plan for introducing GitHub Actions CI/CD to the ALEDB codebase, scoped for a 1-FTE team with no prior deployment experience. Each stage is independently valuable — you can stop at any point and still have gained something.

Companion doc: [deployment-review.md](deployment-review.md).

## Starting point

- Django tests exist across multiple apps ([dashboard/tests/](../../dashboard/tests/), [builder/tests/](../../builder/tests/), [filter/tests/](../../filter/tests/), etc.).
- Entry point is `python manage.py test`, wrapped by [test.sh](../../test.sh).
- **Known issue**: the test suite is outdated. Many tests are likely broken against current code. This changes *what CI starts with*, not *whether CI is worth doing*.

## Stage 0 — PR checks only, no deploy access (1 day)

The safest possible starting point. CI only *runs checks*, it has zero access to production. Even if you misconfigure everything, the worst case is "the green checkmark is wrong."

**Add `.github/workflows/ci.yml` that on every PR and push to master runs:**

1. **`docker build .`** — **blocking**. Proves the Dockerfile and `requirements.txt` still work together. Catches "someone added a dependency and forgot to pin it" and "the base image got updated and broke something." Currently untested because the prod bind-mount hides Dockerfile breakage.
2. **`python manage.py check`** — **blocking**. Django's built-in static validator. Catches broken URL routes, model field errors, circular imports, missing app config. No database required, runs in 5 seconds.
3. **`python manage.py makemigrations --check --dry-run`** — **blocking**. Fails CI if someone modified a model but forgot to generate the migration. Catches a bug that will definitely hit prod otherwise.
4. **`python manage.py collectstatic --dry-run --no-input`** — **blocking**. Catches broken template/static file references before deploy.
5. **Smoke tests** — **blocking**. 5 new tests that prove the app boots (see "Dealing with the outdated test suite" below).
6. **`python manage.py test`** — **non-blocking / informational**. The legacy suite runs, you see red/green, but merges are not gated on it.

### The SQLite vs MySQL gotcha

Run tests against SQLite in CI, not MySQL. SQLite is faster and CI should never touch prod data. Some tests may assume MySQL-specific behavior — if they fail on SQLite, either mark them `@skipUnlessDBFeature(...)` or spin up a MySQL service container in Actions (10 extra lines of YAML). Start with SQLite and see what breaks.

### What this buys you immediately

- Dockerfile breakage is caught *before* it hits the server. Right now nobody knows until the next image rebuild.
- Missing migrations are caught before production breaks.
- PRs stop needing a human to mentally verify "does this still run?"

## Dealing with the outdated test suite

CI without a working test suite is still ~70% as valuable, because most of Stage 0's checks are not tests. But you still want *some* test coverage gating merges. Three options, ordered by effort:

### Option 1 — Run old tests non-blocking (lowest effort)

```yaml
- name: Run tests (informational)
  run: python manage.py test || true
  continue-on-error: true
```

Green/red signal in the PR without preventing merges. Over time you see which tests are flaky vs. reliably passing. This is how most teams ratchet into CI on a legacy codebase.

### Option 2 — Triage: keep what works, quarantine what doesn't (few hours)

Run `manage.py test` locally once, get the failure list, and for each failing test do the quickest thing:

- **Actually broken** (references removed code, wrong assertions): `@skip("needs update 2026-04")` with a dated reason.
- **Infrastructure-dependent** (needs real MySQL, network, files): `@skipUnless(os.environ.get('INTEGRATION'))`.
- **Actually passing**: leave alone.

CI then runs `manage.py test` on the passing subset and blocks merges on regressions. The quarantined tests are a backlog you fix as you touch the code anyway.

### Option 3 — Write a handful of new smoke tests (half day)

Sometimes it is easier to write 5 *new* tests that prove the app boots than to fix 50 old ones. Candidates:

- Can the app import without errors?
- Does `GET /` return 200?
- Does `GET /home` return 200?
- Does `GET /search/?gene=rpoB` return 200?
- Does `GET /ale/projects/` return 200?

10-20 lines of test code total, no fixtures required, catches the vast majority of "the deploy broke the homepage" bugs.

### Recommended combination

**Option 1 + Option 3 together.** Run the legacy suite non-blocking (free signal), *and* write 5 smoke tests that CI blocks on. Safety net is in place while the legacy suite gets repaired whenever someone touches the relevant code.

An outdated test suite is itself a signal worth acting on eventually — it usually means tests encode old assumptions that no longer match the code. When you do repair them, you will probably delete more than you fix, and that is OK. The goal of tests is to catch regressions on *current* behavior, not to preserve historical behavior.

## Stage 1 — tagged image builds on merge (another day)

Still no deploy access. Every merge to master produces a tagged artifact.

**Extend the workflow so on push to `master`:**

1. Build the image.
2. Tag it with the git SHA: `aledb:7258e74`.
3. Push to a registry. **GitHub Container Registry (ghcr.io) is free and requires zero Azure setup.** Use Azure Container Registry later if you want.

### What this buys you

- "What was running in prod last Tuesday?" becomes answerable.
- Rollback becomes "run the old image tag" instead of "git checkout and pray."
- You can pull the image to a dev laptop to reproduce bugs.

Deployment is still manual — someone still SSHes into the VM. But the deploy is now `docker pull ghcr.io/aletechdev/aledb:<sha> && docker-compose up -d` instead of `git pull`. **This is the cattle-not-pet transition**, and it requires no CI deploy credentials.

## Stage 2 — automated deploy to prod (1-2 days, after Stage 1 is stable)

CI now changes production state. Two common patterns — pick one:

### Option A — Push-based (CI SSHes into the VM)

GitHub Actions holds an SSH key (repo secret) and runs `ssh azure-vm 'cd /var/www/aledb && docker pull ... && docker-compose up -d web'`.

- **Pros**: simple, one workflow file, deploy logs in GitHub.
- **Cons**: VM accepts SSH from GitHub's IP range (or you whitelist Actions IPs, which change). SSH key is a high-value secret.

### Option B — Pull-based (VM polls)

Cron on the VM polls "is there a newer tag than what I'm running?" every minute. Or use [Watchtower](https://containrrr.dev/watchtower/) which does this in a container.

- **Pros**: VM never exposes SSH to CI. No secrets leave GitHub except registry read access.
- **Cons**: ~1 minute deploy lag. Slightly harder to debug when something goes wrong.

### Recommendation

**Option B with Watchtower.** ~10 lines of docker-compose, zero SSH key management, failure modes are obvious (container running → working). You give up instant deploys but for a research database with a small team that does not matter.

### Critical guardrail

**Do not auto-deploy to prod on every master merge.** Either:

- Require a GitHub Release tag to trigger prod deploy (`on: release: [published]`), or
- Gate prod deploy behind a manual `workflow_dispatch` button.

You want the option to say "CI is green but I don't want this on prod for another hour."

## Stage 3 — staging environment (after Stage 2 works)

Second VM, auto-deploys on every master merge. Prod still requires manual promote.

Workflow becomes: merge PR → 2 minutes later staging has it → click around → if it looks good, click "deploy to prod" in GitHub Actions.

Staging is also where you test MySQL migrations *before* they hit prod. Worth the cost of the second VM for that reason alone.

This is the full loop. "I am scared to deploy" stops being a feeling you have.

## What not to do in the short term

- **Do not skip straight to Stage 2 or 3.** Get Stage 0 + 1 stable for 2-3 weeks first. You need to build confidence that CI is reliable before letting it touch prod.
- **Do not run CI against the real Azure MySQL database.** Network latency, permission issues, and a buggy test could write to prod data.
- **Do not put production secrets in GitHub Actions secrets until Stage 2.** Until you need them, they are just an attack surface.
- **Do not write custom shell scripts for deployment** when `docker pull && docker-compose up -d` does the job. Simplest thing that works is correct.
- **Do not add matrix builds across multiple Python versions.** You run one version in prod; test that one.
- **Do not lint-gate PRs immediately.** Ruff or Black will flag thousands of issues on a codebase this old. Run in non-blocking mode to gather signal, clean up incrementally, then make it blocking. Otherwise the first PR after merging CI gets buried under style noise.
- **Do not try to fix the entire legacy test suite before introducing CI.** That is a months-long project and blocks everything else. Use the ratchet approach in the "Dealing with the outdated test suite" section.

## Suggested order

- **Day 1**: Stage 0. Single `.github/workflows/ci.yml` with `docker build`, `manage.py check`, `makemigrations --check`, `collectstatic --dry-run`, 5 smoke tests (blocking), legacy `manage.py test` (non-blocking). Merge it. Watch a few PRs go through. Fix what breaks.
- **Week 2**: Stage 1. Push to ghcr.io on master merges. Manually pull+restart on the VM for the next few deploys to get comfortable with the workflow.
- **Week 3-4**: Stage 2. Add Watchtower to the VM. Still require manual "promote to prod."
- **Month 2**: Stage 3. Stand up staging VM, auto-deploy staging on master merge, prod stays manual.

## Open decisions to make when you come back

- **Registry choice**: ghcr.io (free, zero setup) vs Azure Container Registry (lives in the same cloud as everything else, costs a few dollars a month). Ghcr.io is the right starting point.
- **Test strategy**: Option 1 / 2 / 3 or a combination? Recommendation is Option 1 + 3.
- **Deploy trigger**: push-based (SSH) vs pull-based (Watchtower). Recommendation is Watchtower.
- **Prod gate**: release tag vs manual workflow_dispatch. Either works; release tag is slightly more "official feeling."
- **Whether to stand up a separate `staging.aledb.org` now or after Stage 2**. Doing it earlier lets you practice image-based deploys somewhere safe before touching prod.
