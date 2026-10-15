#!/usr/bin/env bash
echo "Deleting Kubernetes resources in k8s/..."
kubectl delete -k k8s
echo "Teardown complete."
