"""Load Terraform (HCL) and render Kubernetes overlays without needing terraform or kubectl installed."""
from __future__ import annotations

import copy
from pathlib import Path

import hcl2
import yaml

ROOT = Path(__file__).resolve().parent.parent


def _clean(value):
    """python-hcl2 keeps HCL quoting ("\"dev\""); strip it so values compare naturally."""
    if isinstance(value, dict):
        return {_clean(k): _clean(v) for k, v in value.items() if k != "__is_block__"}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, str) and len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def load_hcl(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return _clean(hcl2.load(f))


def terraform_resources(tf_dir: Path = ROOT / "terraform") -> list[dict]:
    """Every resource block in every .tf file: {"type", "name", "file", "attrs"}."""
    out = []
    for path in sorted(tf_dir.rglob("*.tf")):
        for block in load_hcl(path).get("resource", []):
            for rtype, named in block.items():
                for name, attrs in named.items():
                    out.append({"type": rtype, "name": name, "file": path.relative_to(tf_dir).as_posix(),
                                "attrs": attrs})
    return out


def terraform_variable_default(name: str, tf_dir: Path = ROOT / "terraform"):
    for block in load_hcl(tf_dir / "variables.tf").get("variable", []):
        if name in block:
            return block[name].get("default")
    return None


# --- a small kustomize: resources, namespace, image tags and strategic-merge patches ---------------------------

def _merge(base, patch):
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k, v in patch.items():
            out[k] = _merge(base.get(k), v) if k in base else copy.deepcopy(v)
        return out
    if isinstance(base, list) and isinstance(patch, list) and all(isinstance(x, dict) and "name" in x
                                                                   for x in base + patch):
        merged = {x["name"]: x for x in base}           # lists of named items (containers) merge by name
        for x in patch:
            merged[x["name"]] = _merge(merged.get(x["name"], {}), x)
        return list(merged.values())
    return copy.deepcopy(patch)


def render(kustomize_dir: Path) -> list[dict]:
    spec = yaml.safe_load((kustomize_dir / "kustomization.yaml").read_text(encoding="utf-8"))
    docs: list[dict] = []
    for res in spec.get("resources", []):
        path = kustomize_dir / res
        docs += render(path) if path.is_dir() else [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8"))]
    for p in spec.get("patches", []):
        patch = yaml.safe_load((kustomize_dir / p["path"]).read_text(encoding="utf-8"))
        for i, d in enumerate(docs):
            if (d["kind"], d["metadata"]["name"]) == (patch["kind"], patch["metadata"]["name"]):
                docs[i] = _merge(d, patch)
    tags = {img["name"]: img["newTag"] for img in spec.get("images", [])}
    for d in docs:
        if "namespace" in spec and d["kind"] != "Namespace":
            d["metadata"]["namespace"] = spec["namespace"]
        for c in containers(d):
            name = c["image"].rsplit(":", 1)[0]
            if name in tags:
                c["image"] = f"{name}:{tags[name]}"
    return docs


def containers(doc: dict) -> list[dict]:
    if doc["kind"] != "CronJob":
        return []
    return doc["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"]
