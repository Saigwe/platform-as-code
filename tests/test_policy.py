import copy

from policy.check import write_report
from policy.load import ROOT, load_hcl, render
from policy.rules import check_all, check_dockerfile, check_environment, check_kubernetes, check_terraform_code


def tfvars(env):
    return load_hcl(ROOT / "terraform" / "envs" / f"{env}.tfvars")


def test_committed_configuration_passes_every_guardrail():
    assert check_all() == {k: [] for k in check_all()}


def test_risky_change_is_blocked_for_every_reason():
    problems = check_environment(load_hcl(ROOT / "tests" / "fixtures" / "risky.tfvars"))
    text = " ".join(problems)
    assert "XLARGE is larger" in text
    assert "auto-suspend of 3600s" in text
    assert "ACCOUNTADMIN must not" in text
    assert "over the 150 credit budget" in text


def test_overlays_render_with_environment_specific_settings():
    dev, prod = render(ROOT / "k8s" / "overlays" / "dev"), render(ROOT / "k8s" / "overlays" / "prod")
    job = {e: next(d for d in docs if d["kind"] == "CronJob") for e, docs in (("dev", dev), ("prod", prod))}
    assert job["dev"]["spec"]["schedule"] == "0 7 * * 1-5" and job["prod"]["spec"]["schedule"] == "15 * * * *"
    prod_container = job["prod"]["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]
    assert prod_container["resources"]["limits"]["memory"] == "2Gi"
    assert prod_container["securityContext"]["readOnlyRootFilesystem"]      # base settings survive the patch
    assert all(d["metadata"].get("namespace") == "data-platform-prod" for d in prod if d["kind"] != "Namespace")


def test_config_drift_between_kubernetes_and_terraform_is_caught():
    docs = render(ROOT / "k8s" / "overlays" / "prod")
    cm = next(d for d in docs if d["kind"] == "ConfigMap")
    cm["data"]["SNOWFLAKE_WAREHOUSE"] = "PROD_ADHOC_WH"
    assert any("PROD_ADHOC_WH is not defined" in p for p in check_kubernetes(docs, tfvars("prod")))


def test_unsafe_cronjob_is_caught():
    docs = copy.deepcopy(render(ROOT / "k8s" / "overlays" / "dev"))
    job = next(d for d in docs if d["kind"] == "CronJob")
    job["spec"]["concurrencyPolicy"] = "Allow"
    c = job["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]
    c["image"], c["resources"] = "ghcr.io/saigwe/dbt-runner:latest", {}
    text = " ".join(check_kubernetes(docs, tfvars("dev")))
    assert "overlapping runs" in text and "not pinned" in text and "limits" in text


def test_code_level_checks(tmp_path):
    assert check_terraform_code() == [] and check_dockerfile() == []
    (tmp_path / "variables.tf").write_text('variable "terraform_role" {\n  default = "ACCOUNTADMIN"\n}\n')
    (tmp_path / "rogue.tf").write_text('resource "snowflake_warehouse" "adhoc" {\n  name = "ADHOC"\n}\n')
    text = " ".join(check_terraform_code(tmp_path))
    assert "outside the guarded module" in text and "no resource monitor" in text and "ACCOUNTADMIN" in text
    bad = tmp_path / "Dockerfile"
    bad.write_text("FROM python\nRUN pip install dbt-core\n")
    assert len(check_dockerfile(bad)) == 2


def test_report(tmp_path):
    report = write_report(tmp_path)
    assert report["caps"] == {"prod": 2010.0, "dev": 360.0}
    assert "$2,010 a month" in (tmp_path / "platform_report.md").read_text(encoding="utf-8")
