<#
.SYNOPSIS
    Automated Kubernetes Deployment Script for Zomato Analytics Dashboard
.DESCRIPTION
    Builds the Docker image, verifies the active lightweight cluster,
    applies Kustomize manifests, and monitors the pod rollout.
#>

[CmdletBinding()]
param (
    [switch]$SkipBuild,
    [switch]$PortForward
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Zomato Analytics - Kubernetes Deployment Pipeline        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Prerequisites
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl is not installed or not in PATH. Please install kubectl."
    exit 1
}

# 2. Check Kubernetes Cluster Connectivity
Write-Host "`n[1/5] Checking Kubernetes cluster connectivity..." -ForegroundColor Yellow
$currentContext = ""
try {
    $currentContext = (kubectl config current-context).Trim()
    Write-Host "Current Kubernetes Context: $currentContext" -ForegroundColor Green
    kubectl cluster-info --request-timeout=5s | Select-Object -First 2
} catch {
    Write-Host "`n[ERROR] Unable to connect to a running Kubernetes cluster!" -ForegroundColor Red
    Write-Host "Please start your preferred lightweight local Kubernetes cluster:" -ForegroundColor Yellow
    Write-Host "  * Docker Desktop: Open Docker Desktop -> Settings -> Kubernetes -> Check 'Enable Kubernetes'"
    Write-Host "  * Minikube:       minikube start --driver=docker"
    Write-Host "  * Kind:           kind create cluster --name zomato-cluster"
    Write-Host "  * K3d:            k3d cluster create zomato-cluster -p `"8501:30501@agent:0`""
    exit 1
}

# 3. Build Docker Image (if not skipped)
if (-not $SkipBuild) {
    Write-Host "`n[2/5] Building Docker image 'zomato-analysis-dashboard:latest'..." -ForegroundColor Yellow
    docker build -t zomato-analysis-dashboard:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed."
        exit $LASTEXITCODE
    }
    Write-Host "Docker image built successfully." -ForegroundColor Green
} else {
    Write-Host "`n[2/5] Skipping Docker build (-SkipBuild specified)..." -ForegroundColor Gray
}

# 4. Load Image into Cluster (Minikube / Kind / K3d specifics)
Write-Host "`n[3/5] Syncing image to lightweight cluster..." -ForegroundColor Yellow
if ($currentContext -like "*minikube*") {
    Write-Host "Detected Minikube context. Loading image into Minikube cache..." -ForegroundColor Cyan
    minikube image load zomato-analysis-dashboard:latest
} elseif ($currentContext -like "*kind*") {
    $clusterName = $currentContext.Replace("kind-", "")
    Write-Host "Detected Kind context ($clusterName). Loading image into Kind nodes..." -ForegroundColor Cyan
    kind load docker-image zomato-analysis-dashboard:latest --name $clusterName
} elseif ($currentContext -like "*k3d*") {
    $clusterName = $currentContext.Replace("k3d-", "")
    Write-Host "Detected K3d context ($clusterName). Importing image into K3d nodes..." -ForegroundColor Cyan
    k3d image import zomato-analysis-dashboard:latest -c $clusterName
} else {
    Write-Host "Docker Desktop / Standard context detected. Local image is directly accessible." -ForegroundColor Green
}

# 5. Apply Kubernetes Manifests via Kustomize
Write-Host "`n[4/5] Applying Kubernetes resources (k8s/)..." -ForegroundColor Yellow
kubectl apply -k k8s
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to apply Kubernetes manifests."
    exit $LASTEXITCODE
}

# 6. Monitor Pod Rollout Status
Write-Host "`n[5/5] Waiting for pods to become ready (max 90s)..." -ForegroundColor Yellow
kubectl rollout status deployment/zomato-dashboard -n zomato-analytics --timeout=90s

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT SUCCESSFUL! All pods are running & healthy.   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

Write-Host "`n[Active Pods in namespace 'zomato-analytics']" -ForegroundColor Cyan
kubectl get pods -n zomato-analytics -o wide

Write-Host "`n[Exposed Services]" -ForegroundColor Cyan
kubectl get svc -n zomato-analytics

Write-Host "`n--- Access Methods ---" -ForegroundColor Yellow
Write-Host "1. NodePort:     http://localhost:30501"
Write-Host "2. LoadBalancer: http://localhost:8501 (Docker Desktop)"
Write-Host "3. Port-Forward: kubectl port-forward svc/zomato-dashboard-service 8501:8501 -n zomato-analytics"
Write-Host "                 Then open: http://localhost:8501"

if ($PortForward) {
    Write-Host "`nStarting port-forwarding to http://localhost:8501 (Ctrl+C to exit)..." -ForegroundColor Cyan
    Start-Process "http://localhost:8501"
    kubectl port-forward svc/zomato-dashboard-service 8501:8501 -n zomato-analytics
}
