<#
.SYNOPSIS
    Cleans up all Kubernetes resources created for Zomato Analytics.
#>

Write-Host "Deleting Kubernetes resources in k8s/..." -ForegroundColor Yellow
kubectl delete -k k8s
Write-Host "Teardown complete." -ForegroundColor Green
