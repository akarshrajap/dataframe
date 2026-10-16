"""
Test Suite: Kubernetes Manifest Integrity & Security Validation
Parses all YAML manifests in k8s/ using PyYAML to verify apiVersions, kinds,
resource constraints, security contexts, probes, and naming conventions.
"""

import os
import glob
import yaml
import pytest


K8S_DIR = "k8s"


def test_manifest_directory_and_files_exist():
    """Ensure k8s directory contains all required resource specifications."""
    assert os.path.exists(K8S_DIR), f"Directory '{K8S_DIR}' not found!"
    yaml_files = sorted(glob.glob(os.path.join(K8S_DIR, "*.yaml")))
    expected_files = [
        "configmap.yaml",
        "deployment.yaml",
        "hpa.yaml",
        "kustomization.yaml",
        "namespace.yaml",
        "service.yaml",
    ]
    basenames = [os.path.basename(f) for f in yaml_files]
    for expected in expected_files:
        assert expected in basenames, f"Missing manifest: {expected}"


def test_all_manifests_valid_yaml():
    """Verify that all YAML manifests parse successfully without syntax errors."""
    yaml_files = glob.glob(os.path.join(K8S_DIR, "*.yaml"))
    for file_path in yaml_files:
        with open(file_path, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
            assert len(docs) > 0, f"Empty YAML file: {file_path}"
            for doc in docs:
                if doc is None:
                    continue
                assert "apiVersion" in doc, f"Missing 'apiVersion' in {file_path}"
                assert "kind" in doc, f"Missing 'kind' in {file_path}"
                if doc["kind"] != "Kustomization":
                    assert "metadata" in doc, f"Missing 'metadata' in {file_path}"
                    assert "name" in doc["metadata"], f"Missing 'metadata.name' in {file_path}"


def test_deployment_manifest_specifications():
    """Verify production security context, probes, replicas, and ports in deployment.yaml."""
    dep_path = os.path.join(K8S_DIR, "deployment.yaml")
    with open(dep_path, "r", encoding="utf-8") as f:
        dep = yaml.safe_load(f)

    assert dep["kind"] == "Deployment"
    assert dep["metadata"]["name"] == "zomato-dashboard"
    assert dep["metadata"]["namespace"] == "zomato-analytics"

    spec = dep["spec"]
    assert spec["replicas"] >= 2, "Deployment should specify at least 2 replicas for high availability"
    assert spec["strategy"]["type"] == "RollingUpdate"

    template = spec["template"]
    pod_spec = template["spec"]

    # Security: Non-root user validation
    assert pod_spec.get("securityContext", {}).get("runAsNonRoot") is True
    assert pod_spec.get("securityContext", {}).get("runAsUser") == 1000

    container = pod_spec["containers"][0]
    assert container["name"] == "dashboard"

    # Container port 8501 for Streamlit
    ports = [p["containerPort"] for p in container.get("ports", [])]
    assert 8501 in ports, "Streamlit container must expose port 8501"

    # Health Probes
    assert "startupProbe" in container, "Deployment must define a startupProbe for data loading"
    assert "livenessProbe" in container, "Deployment must define a livenessProbe"
    assert "readinessProbe" in container, "Deployment must define a readinessProbe"

    for probe_name in ["startupProbe", "livenessProbe", "readinessProbe"]:
        probe = container[probe_name]
        assert "httpGet" in probe
        assert probe["httpGet"]["path"] == "/_stcore/health"

    # Resource requests and limits
    res = container.get("resources", {})
    assert "requests" in res and "cpu" in res["requests"] and "memory" in res["requests"]
    assert "limits" in res and "cpu" in res["limits"] and "memory" in res["limits"]


def test_service_manifest_specifications():
    """Verify that service exposes port 8501 and routes to Streamlit."""
    svc_path = os.path.join(K8S_DIR, "service.yaml")
    with open(svc_path, "r", encoding="utf-8") as f:
        services = list(yaml.safe_load_all(f))

    svc_names = [s["metadata"]["name"] for s in services if s]
    assert "zomato-dashboard-service" in svc_names or "zomato-dashboard-lb" in svc_names

    for svc in services:
        if not svc:
            continue
        ports = svc["spec"]["ports"]
        target_ports = [p["port"] for p in ports]
        assert 8501 in target_ports
