"""Guardrails that run on every pull request, before anything reaches Snowflake or the cluster.

Each rule returns a list of plain-English violations; an empty list means the change is allowed.
"""
from __future__ import annotations

from pathlib import Path

from .load import ROOT, containers, render, terraform_resources, terraform_variable_default

CREDIT_PRICE_USD = 3.0
CREDITS_PER_HOUR = {"XSMALL": 1, "SMALL": 2, "MEDIUM": 4, "LARGE": 8, "XLARGE": 16, "XXLARGE": 32}
MONTHLY_BUDGET_CREDITS = {"dev": 150, "prod": 800}
MAX_SIZE = {"dev": "SMALL", "prod": "LARGE"}
MAX_AUTO_SUSPEND_SECONDS = 300
PRIVILEGED_ROLES = {"ACCOUNTADMIN", "SECURITYADMIN", "ORGADMIN", "SYSADMIN"}


def check_environment(tfvars: dict) -> list[str]:
    env, whs = tfvars["environment"], tfvars["warehouses"]
    sizes = list(CREDITS_PER_HOUR)
    problems = []
    for name, w in whs.items():
        if sizes.index(w["size"]) > sizes.index(MAX_SIZE[env]):
            problems.append(f"{env}/{name}: {w['size']} is larger than the {MAX_SIZE[env]} allowed in {env}")
        if w["auto_suspend_seconds"] > MAX_AUTO_SUSPEND_SECONDS:
            problems.append(f"{env}/{name}: auto-suspend of {w['auto_suspend_seconds']}s bills idle time "
                            f"(max {MAX_AUTO_SUSPEND_SECONDS}s)")
        for role in sorted(set(w["users"]) & PRIVILEGED_ROLES):
            problems.append(f"{env}/{name}: {role} must not be granted warehouse access directly")
    total = sum(w["monthly_credit_quota"] for w in whs.values())
    if total > MONTHLY_BUDGET_CREDITS[env]:
        problems.append(f"{env}: credit caps total {total}, over the {MONTHLY_BUDGET_CREDITS[env]} credit budget "
                        f"(${total * CREDIT_PRICE_USD:,.0f} vs ${MONTHLY_BUDGET_CREDITS[env] * CREDIT_PRICE_USD:,.0f})")
    return problems


def check_terraform_code(tf_dir: Path = ROOT / "terraform") -> list[str]:
    problems = []
    for r in terraform_resources(tf_dir):
        if r["type"] == "snowflake_warehouse":
            if not r["file"].startswith("modules/warehouse/"):
                problems.append(f"{r['file']}: warehouse {r['name']} is created outside the guarded module")
            if not r["attrs"].get("resource_monitor"):
                problems.append(f"{r['file']}: warehouse {r['name']} has no resource monitor")
    if str(terraform_variable_default("terraform_role", tf_dir)).upper() == "ACCOUNTADMIN":
        problems.append("variables.tf: Terraform must not run as ACCOUNTADMIN")
    return problems


def check_kubernetes(docs: list[dict], tfvars: dict) -> list[str]:
    env = tfvars["environment"]
    prefix = env.upper()
    warehouses = {f"{prefix}_{k}_WH" for k in tfvars["warehouses"]}
    roles = {f"{prefix}_{r}" for w in tfvars["warehouses"].values() for r in w["users"]}
    problems = []
    for d in docs:
        where = f"{env}/{d['kind']}/{d['metadata']['name']}"
        if d["kind"] == "CronJob":
            spec = d["spec"]
            job = spec["jobTemplate"]["spec"]
            pod = job["template"]["spec"]
            if spec.get("concurrencyPolicy") != "Forbid":
                problems.append(f"{where}: overlapping runs allowed (set concurrencyPolicy: Forbid)")
            if not job.get("activeDeadlineSeconds"):
                problems.append(f"{where}: no activeDeadlineSeconds, a hung run would block the schedule")
            if not pod.get("securityContext", {}).get("runAsNonRoot"):
                problems.append(f"{where}: pod may run as root")
            for c in containers(d):
                tag = c["image"].rsplit(":", 1)[1] if ":" in c["image"] else ""
                if tag in ("", "latest"):
                    problems.append(f"{where}/{c['name']}: image is not pinned to a version")
                limits = c.get("resources", {}).get("limits", {})
                if not {"cpu", "memory"} <= set(limits):
                    problems.append(f"{where}/{c['name']}: missing CPU or memory limits")
                if not c.get("securityContext", {}).get("readOnlyRootFilesystem"):
                    problems.append(f"{where}/{c['name']}: root filesystem is writable")
        if d["kind"] == "ConfigMap" and "SNOWFLAKE_WAREHOUSE" in d.get("data", {}):
            data = d["data"]
            if data["SNOWFLAKE_WAREHOUSE"] not in warehouses:
                problems.append(f"{where}: warehouse {data['SNOWFLAKE_WAREHOUSE']} is not defined in Terraform "
                                f"for {env}")
            if data.get("SNOWFLAKE_ROLE") not in roles:
                problems.append(f"{where}: role {data.get('SNOWFLAKE_ROLE')} is not defined in Terraform for {env}")
            if data.get("DBT_TARGET") != env:
                problems.append(f"{where}: DBT_TARGET is {data.get('DBT_TARGET')}, expected {env}")
    return problems


def check_dockerfile(path: Path = ROOT / "docker" / "Dockerfile") -> list[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    problems = []
    for ln in lines:
        if ln.upper().startswith("FROM "):
            image = ln.split()[1]
            if ":" not in image or image.endswith(":latest"):
                problems.append(f"Dockerfile: base image {image} is not pinned")
    users = [ln.split()[1] for ln in lines if ln.upper().startswith("USER ")]
    if not users or users[-1] in ("root", "0"):
        problems.append("Dockerfile: container runs as root")
    return problems


def check_all(envs=("dev", "prod")) -> dict[str, list[str]]:
    from .load import load_hcl
    results = {"terraform code": check_terraform_code(), "docker image": check_dockerfile()}
    for env in envs:
        tfvars = load_hcl(ROOT / "terraform" / "envs" / f"{env}.tfvars")
        results[f"{env} warehouses"] = check_environment(tfvars)
        results[f"{env} kubernetes"] = check_kubernetes(render(ROOT / "k8s" / "overlays" / env), tfvars)
    return results
