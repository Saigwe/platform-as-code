# 3-minute walkthrough: Platform as Code

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, `terraform/modules/warehouse/`, `terraform/envs/prod.tfvars`, `k8s/base`, `policy/rules.py`, `output/platform_report.md`, `tests/fixtures/risky.tfvars`, `.github/workflows/ci.yml`, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README headline | Most surprise warehouse bills come from a change nobody reviewed. Here the whole analytics platform is code, and production spend is capped at $2,010 a month by the code itself. |
| 0:20–0:45 | `terraform/modules/warehouse/` | Terraform for Snowflake: database, schemas, functional roles, grants and warehouses. A warehouse can only be created through this module, and it always attaches a resource monitor that alerts at 75 and 90% and suspends at 100%. |
| 0:45–1:05 | `prod.tfvars` next to `dev.tfvars` | Same code for both environments, with different sizes, caps and Time Travel retention. Validation rejects anything above LARGE, and Terraform never runs as ACCOUNTADMIN. |
| 1:05–1:30 | `k8s/base` and the Dockerfile | dbt runs in a pinned, non-root Docker image with no secrets inside, scheduled by Kubernetes CronJobs: no overlapping runs, a deadline, resource limits and a read-only filesystem. Dev runs weekday mornings; prod runs hourly. |
| 1:30–2:00 | `policy/rules.py` | Guardrails check every pull request. Cost: size limits and a total budget per environment. Security: no privileged roles, no root containers, pinned images. Drift: the warehouse each Kubernetes job uses must exist in Terraform. |
| 2:00–2:25 | `risky.tfvars`, then `output/platform_report.md` | This sample change puts an XLARGE warehouse in dev. The report shows it rejected, with every reason, before it can merge. |
| 2:25–2:45 | `.github/workflows/ci.yml` | CI runs the guardrails, terraform fmt and validate, kubeconform on the rendered overlays and a Docker build on every push. Deploys to prod need an approval. |
| 2:45–3:00 | `tests/`, then the README top | Seven tests, including drift and an unsafe CronJob being caught. For a data leader: rebuild an environment with two commands, and no runaway bill. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `python -m policy.check` once before recording so the outputs are fresh.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say that it validates in CI but hasn't been deployed to a real Snowflake account or cluster; the README lists what a deploy needs.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the walkthrough line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
