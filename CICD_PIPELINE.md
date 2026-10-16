# Production CI/CD Pipeline Architecture: GitHub Actions to Kubernetes

This document provides complete architectural specifications, workflow blueprints, and operational runbooks for the automated **Continuous Integration and Continuous Deployment (CI/CD)** pipeline powering the **Zomato Analytics Platform**.

---

## 1. End-to-End Pipeline Architecture

The CI/CD pipeline automates the full path from developer commit to live cluster rollout across 3 deterministic stages:

```mermaid
flowchart TD
    subgraph Trigger["1. Triggers"]
        P1["Git Push / PR (main, master)"]
        P2["Manual Trigger (workflow_dispatch)"]
    end

    subgraph Stage1["Stage 1: Quality Gate & Validation (01-Lint-And-Test)"]
        C1["Checkout Code (actions/checkout@v4)"]
        C2["Python 3.12 Runtime & Pip Cache"]
        C3["Code Style & Syntax Check (Flake8 E9, F63, F7, F82)"]
        C4["Dataset Schema & Boundary Tests (Pytest)"]
        C5["K8s Manifest PyYAML Validation (Pytest)"]
    end

    subgraph Stage2["Stage 2: Container Release (02-Build-And-Publish)"]
        B1["Docker Buildx Engine & QEMU"]
        B2["Authenticate to GitHub Container Registry (ghcr.io)"]
        B3["Semantic Tagging: :latest & :sha-xxxxxxx"]
        B4["Multi-Stage Build with GitHub Layer Caching (type=gha)"]
        B5["Push Immutable Image to GHCR"]
    end

    subgraph Stage3["Stage 3: Controlled Deployment (03-Controlled-Kubernetes-Deployment)"]
        D1["Cluster Authentication (Decoded KUBECONFIG Secret)"]
        D2["Kustomize Image Override (:sha-xxxxxxx)"]
        D3["Atomic Manifest Apply (kubectl apply -k k8s)"]
        D4["Zero-Downtime Rollout Gate (kubectl rollout status)"]
        D5["Post-Deploy Telemetry & Health Probe Verification"]
    end

    subgraph Target["Reachable Kubernetes Cluster (Docker Desktop / Kind / Cloud)"]
        Node["desktop-control-plane"]
        NS["Namespace: zomato-analytics"]
        Pod1["Pod 1 (1/1 Ready)"]
        Pod2["Pod 2 (1/1 Ready)"]
        SVC["LoadBalancer (8501) / NodePort (30501)"]
    end

    Trigger --> Stage1
    Stage1 -->|Pass Quality Gate| Stage2
    Stage2 -->|Image Published| Stage3
    Stage3 --> Target
    NS --> Pod1
    NS --> Pod2
    SVC --> Pod1
    SVC --> Pod2
```

---

## 2. Pipeline Stage Breakdown

### Stage 1: Quality Gate & Automated Validation (`01-Lint-And-Test`)
* **Environment**: `ubuntu-latest`, Python `3.12` with cached pip wheels.
* **Flake8 Linter**: Scans for fatal Python errors (E9 syntax errors, F63/F7 invalid code constructs, F82 undefined names).
* **Automated Data Validation (`tests/test_data_validation.py`)**:
  * Asserts presence and integrity of `zomato_clean_validated.csv`.
  * Enforces schema columns: `name`, `votes`, `location`, `rest_type`, `cuisines`, `rating`, `approx_cost_inr`, `has_online_order`, `has_table_booking`, `price_tier`.
  * Verifies numerical boundaries (ratings $\in [1.0, 5.0]$, votes $\ge 0$, costs $> 0$).
  * Validates executive KPI summary tables (`kpi_summary_channel.csv`, `kpi_summary_executive.csv`, `kpi_summary_price_tier.csv`).
* **Manifest Structural Integrity (`tests/test_k8s_manifests.py`)**:
  * Parses all YAML manifests in `k8s/` using `PyYAML`.
  * Enforces container port `8501`, non-root user `appuser` (UID `1000`), resource requests/limits, and triple health probes (`startupProbe`, `livenessProbe`, `readinessProbe`).

### Stage 2: Container Image Build & Publication (`02-Build-And-Publish`)
* **Registry**: GitHub Container Registry (`ghcr.io`).
* **Authentication**: Ephemeral `${{ secrets.GITHUB_TOKEN }}` with `packages: write` permissions (zero long-lived credentials).
* **Tagging Strategy**:
  * Dual-tagging: `:latest` on default branch + `:sha-<7-char-commit-hash>` for deterministic traceability and rollbacks.
* **Build Acceleration**: Uses Buildx GitHub Actions cache (`type=gha,mode=max`) to reuse identical Docker layers across pipeline runs.

### Stage 3: Controlled Kubernetes Deployment (`03-Controlled-Kubernetes-Deployment`)
* **Gated Execution**: Only runs on merges to `main` (pull requests execute stages 1 and 2 in build-only mode without pushing or deploying).
* **Cluster Authentication**: Securely authenticates via base64-encoded `KUBECONFIG` stored in GitHub Actions Secrets.
* **Dynamic Kustomize Image Patching**: Overrides image reference in `k8s/deployment.yaml` with the exact Git commit SHA tag published in Stage 2.
* **Controlled Rolling Update**:
  * Applies resources: `kubectl apply -k k8s`
  * Rollout verification gate:
    ```bash
    kubectl rollout status deployment/zomato-dashboard -n zomato-analytics --timeout=120s
    ```
  * Blocks pipeline if pods fail health checks within the timeout budget.

---

## 3. Repository File Structure

```
data_analysis/
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions CI/CD Pipeline definition
├── tests/
│   ├── test_data_validation.py   # Dataset schema, data types & KPI tests
│   └── test_k8s_manifests.py     # Kubernetes manifest structure & probe tests
├── k8s/
│   ├── namespace.yaml            # Isolated zomato-analytics namespace
│   ├── configmap.yaml            # Application configuration & theme
│   ├── deployment.yaml           # Deployment spec (2 replicas, probes, security)
│   ├── service.yaml              # LoadBalancer (8501) & NodePort (30501)
│   ├── hpa.yaml                  # Horizontal Pod Autoscaler
│   └── kustomization.yaml        # Kustomize manifest bundle
├── Dockerfile                    # Multi-stage, non-root Streamlit container
├── deploy-k8s.ps1                # Automated Windows PowerShell deployment pipeline
├── deploy-k8s.sh                 # Automated Linux/macOS deployment pipeline
├── requirements.txt              # Application runtime dependencies
├── requirements-dev.txt          # CI/CD and testing dependencies
├── zomato_clean_validated.csv    # Clean production dataset
└── CICD_PIPELINE.md              # Pipeline architecture and runbook
```

---

## 4. GitHub Secret Configuration for Remote Deployment

To connect your remote GitHub Actions workflow to a reachable Kubernetes training cluster:

1. Obtain your cluster's kubeconfig file.
2. Encode the kubeconfig in base64:
   ```powershell
   # Windows PowerShell:
   [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("$HOME\.kube\config"))
   ```
   ```bash
   # Linux/macOS:
   cat ~/.kube/config | base64 -w 0
   ```
3. Navigate to **GitHub Repository** -> **Settings** -> **Secrets and variables** -> **Actions**.
4. Click **New repository secret**:
   * **Name**: `KUBECONFIG`
   * **Value**: Paste the base64-encoded string.

---

## 5. Local Training Cluster Deployment Runbook

You can trigger the entire end-to-end pipeline locally on the reachable training cluster at any time:

### Using Windows PowerShell
```powershell
# Full release: Runs Quality Gate (Flake8 + Pytest), builds image, applies K8s manifests, and verifies rollout:
.\deploy-k8s.ps1

# With browser auto-launch and port-forwarding:
.\deploy-k8s.ps1 -PortForward

# Skip build if using existing cached image:
.\deploy-k8s.ps1 -SkipBuild
```

### Using Linux / WSL / macOS
```bash
chmod +x deploy-k8s.sh
./deploy-k8s.sh
```

---

## 6. Verification and Health Checks

### Check Rollout Status
```powershell
kubectl rollout status deployment/zomato-dashboard -n zomato-analytics
```

### View Running Pods and IP Addresses
```powershell
kubectl get pods -n zomato-analytics -o wide
```

### View Services and Port Bindings
```powershell
kubectl get svc -n zomato-analytics
```

### Query Application Health Endpoint Directly
```powershell
curl http://localhost:8501/_stcore/health
# Returns: "ok" (HTTP 200)
```

---

## 7. Emergency Rollback Runbook

If a faulty release is applied to the cluster, execute an instant zero-downtime rollback:

```powershell
# 1. View deployment revision history:
kubectl rollout history deployment/zomato-dashboard -n zomato-analytics

# 2. Roll back to the previous stable revision:
kubectl rollout undo deployment/zomato-dashboard -n zomato-analytics

# 3. Monitor rollback completion:
kubectl rollout status deployment/zomato-dashboard -n zomato-analytics
```
