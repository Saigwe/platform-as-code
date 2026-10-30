"""Run every guardrail and write output/platform_report.md: python -m policy.check (exits 1 on any violation)."""
from __future__ import annotations

import sys
from pathlib import Path

from .load import ROOT, load_hcl
from .rules import CREDIT_PRICE_USD, CREDITS_PER_HOUR, MONTHLY_BUDGET_CREDITS, check_all, check_environment


def environment_table(env: str) -> tuple[str, int]:
    whs = load_hcl(ROOT / "terraform" / "envs" / f"{env}.tfvars")["warehouses"]
    rows = ["| Warehouse | Size | Auto-suspend | Monthly credit cap | Spend cap | Used by |", "|---|---|---|---|---|---|"]
    for name, w in whs.items():
        rows.append(f"| {env.upper()}_{name}_WH | {w['size']} ({CREDITS_PER_HOUR[w['size']]} cr/h) | "
                    f"{w['auto_suspend_seconds']}s | {w['monthly_credit_quota']} | "
                    f"${w['monthly_credit_quota'] * CREDIT_PRICE_USD:,.0f} | "
                    f"{', '.join(env.upper() + '_' + u for u in w['users'])} |")
    return "\n".join(rows), sum(w["monthly_credit_quota"] for w in whs.values())


def write_report(out_dir: Path = ROOT / "output") -> dict:
    results = check_all()
    caps = {}
    sections = []
    for env in ("prod", "dev"):
        table, credits = environment_table(env)
        caps[env] = credits * CREDIT_PRICE_USD
        sections.append(f"### {env}\n\n{table}\n\nCapped at **{credits} credits (${caps[env]:,.0f}) a month**, "
                        f"inside the {MONTHLY_BUDGET_CREDITS[env]} credit budget.")
    status = "\n".join(f"| {k} | {'pass' if not v else 'FAIL: ' + '; '.join(v)} |" for k, v in results.items())
    risky = check_environment(load_hcl(ROOT / "tests" / "fixtures" / "risky.tfvars"))
    blocked = "\n".join(f"- {p}" for p in risky)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "platform_report.md").write_text(f"""# Platform as code: guardrail report

**Summary for leadership:** every Snowflake warehouse, role, grant and scheduled dbt job is defined in code and
reviewed like any other change. Production spend is **capped at ${caps['prod']:,.0f} a month** and dev at
**${caps['dev']:,.0f}**: warehouses suspend automatically at their limit, so a runaway query cannot become a surprise
bill. Rebuilding an environment is one `terraform apply` and one `kubectl apply -k`, not a week of console clicks.

## Spending caps by environment

{chr(10).join(sections)}

## Guardrail results

| Check | Result |
|---|---|
{status}

## What the guardrails block

A pull request that adds this to dev (an XLARGE warehouse, hourly auto-suspend and ACCOUNTADMIN access) is rejected
before it merges:

{blocked}
""", encoding="utf-8")
    return {"results": results, "caps": caps, "risky": risky}


if __name__ == "__main__":
    report = write_report()
    failures = {k: v for k, v in report["results"].items() if v}
    for k, v in report["results"].items():
        print(f"{k:22} {'pass' if not v else 'FAIL'}")
        for p in v:
            print("   -", p)
    print(f"monthly caps: prod ${report['caps']['prod']:,.0f}, dev ${report['caps']['dev']:,.0f}")
    sys.exit(1 if failures else 0)
