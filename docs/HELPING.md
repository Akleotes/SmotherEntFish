# Helping test Smotherfish

Smotherfish improvements are tested by playing thousands of games. Anyone
with a GitHub account can lend their GitHub Actions minutes to these tests.
Your fork plays its share of each experiment on GitHub's machines; nothing
runs on your own computer and there is nothing to install.

All of this is testing of Smotherfish itself: each job builds Smotherfish
from the experiment's branch and plays it against Stockfish or Maia.

## Joining (about two minutes)

1. Fork this repository on GitHub (keep the `smotherfish` branch; you only
   need that branch).
2. Open your fork's **Actions** tab and enable workflows (GitHub disables
   them on new forks).
3. Still in Actions, choose **Helper poll** and press **Run workflow** once.
   It should finish green in under a minute.

That is all. Your fork is found automatically from the list of forks of
this repository. Its helper poll runs on a schedule; it copies any
experiment meant for your fork and starts it there.

## What your fork does

- Every experiment is split into shares; each fork gets one (some accounts
  with more capacity get more).
- Your fork plays about 20 jobs at once, each 25 games on a 4-core GitHub
  machine, and writes the results to the branch `actions-exp/<experiment>`
  in your fork. The maintainers read them from there; nothing is pushed to
  this repository.
- Public repositories have free Actions minutes on GitHub's standard
  machines.

## Faster results

The schedule polls about once an hour. If you want an experiment to start
right away, press **Run workflow** on **Helper poll** again.

## Keeping your fork up to date

Use **Sync fork** on your fork's main page only when the maintainers ask:
experiments are built on the version your fork is on.

## Leaving

Disable the workflows in the Actions tab, or delete the fork. If your fork
stops running, its share is re-issued to the other helpers
(`notes/scripts/volunteers.py refill`), so nothing is lost.

## For maintainers

- `notes/scripts/volunteers.py list` shows the helpers (by ID only).
- `notes/scripts/distribute.sh PLAN.json` spreads an experiment over all
  of them (shares from `notes/volunteers.json`).
- `notes/scripts/volunteers.py status EXP` shows games delivered per
  account; `refill EXP` writes a plan with the shares of accounts that never
  ran (distribute it with `ONLY=...` as the command prints);
  `merge EXP OUTDIR` collects everything, refills included.
