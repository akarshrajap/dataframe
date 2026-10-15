#!/usr/bin/env bash
# =============================================================================
# Automated Kubernetes Deployment Script for Zomato Analytics Dashboard
# =============================================================================
set -euo pipefail

echo "=========================================================="
echo "  Zomato Analytics - Kubernetes Deployment Pipeline        "
echo "=========================================================="

# 1. Verify Prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "[ERROR] kubectl is not installed or not in PATH."
    exit 1
fi

# 2. Check Kubernetes Cluster Connectivity
echo -e "\n[1/5] Checking Kubernetes cluster connectivity..."
CURRENT_CONTEXT=$(kubectl config current-context || true)
echo "Current Kubernetes Context: ${CURRENT_CONTEXT}"

if ! kubectl cluster-info --request-timeout=5s > /dev/null 2>&1; then
    echo "[ERROR] Unable to connect to a running Kubernetes cluster!"
    echo "Please start your preferred lightweight local Kubernetes cluster:"
    echo "  * Minikube:       minikube start --driver=docker"
    echo "  * Kind:           kind create cluster --name zomato-cluster"
    echo "  * K3d:            k3d cluster create zomato-cluster -p '8501:30501@agent:0'"
    echo "  * Docker Desktop: Enable Kubernetes in Docker Desktop Settings"
    exit 1
fi

# 3. Build Docker Image
echo -e "\n[2/5] Building Docker image 'zomato-analysis-dashboard:latest'..."
docker build -t zomato-analysis-dashboard:latest .

# 4. Sync Image with lightweight cluster
echo -e "\n[3/5] Syncing image to lightweight cluster..."
if [[ "$CURRENT_CONTEXT" == *"minikube"* ]]; then
    echo "Detected Minikube. Loading image..."
    minikube image load zomato-analysis-dashboard:latest
elif [[ "$CURRENT_CONTEXT" == *"kind"* ]]; then
    CLUSTER_NAME="${CURRENT_CONTEXT#kind-}"
    echo "Detected Kind (${CLUSTER_NAME}). Loading image..."
    kind load docker-image zomato-analysis-dashboard:latest --name "${CLUSTER_NAME}"
elif [[ "$CURRENT_CONTEXT" == *"k3d"* ]]; then
    CLUSTER_NAME="${CURRENT_CONTEXT#k3d-}"
    echo "Detected K3d (${CLUSTER_NAME}). Importing image..."
    k3d image import zomato-analysis-dashboard:latest -c "${CLUSTER_NAME}"
else
    echo "Docker Desktop / Standard context detected. Local image is directly accessible."
fi

# 5. Apply Manifests via Kustomize
echo -e "\n[4/5] Applying Kubernetes resources (k8s/)..."
kubectl apply -k k8s

# 6. Monitor Pod Rollout
echo -e "\n[5/5] Waiting for pods to become ready (max 90s)..."
kubectl rollout status deployment/zomato-dashboard -n zomato-analytics --timeout=90s

echo -e "\n=========================================================="
echo "  DEPLOYMENT SUCCESSFUL! All pods are running & healthy.   "
echo "=========================================================="

echo -e "\n[Active Pods in namespace 'zomato-analytics']"
kubectl get pods -n zomato-analytics -o wide

echo -e "\n[Exposed Services]"
kubectl get svc -n zomato-analytics

echo -e "\n--- Access Methods ---"
echo "1. NodePort:     http://localhost:30501"
echo "2. LoadBalancer: http://localhost:8501 (Docker Desktop)"
echo "3. Port-Forward: kubectl port-forward svc/zomato-dashboard-service 8501:8501 -n zomato-analytics"
echo "                 Then open: http://localhost:8501"
