# Inventory reconciler on Kubernetes (learning project)

A small Python (Flask + pandas) service that merges mock server inventories from
three fictional sources (AD, SCCM, Veeam) and reports what is missing from where.
All data is fictional and written for this project. It is used to practise
containers, Kubernetes, Terraform on Azure (AKS + ACR) and CI/CD.

It serves a small web page at `/` (summary cards plus a table, click a card to
filter) and JSON endpoints: `/summary`, `/servers?missing=veeam`, `/healthz`, `/readyz`.
The page shows the name of the pod serving the request.

## Plan to Tuesday (keep it small)

- Sat/Sun: Stage 1 up to the local cluster. App open in your browser via port-forward.
- Mon: do the practice items (delete a pod, rolling update, rollback, one deliberate
  break) and fill in LEARNING-LOG.md. Push the repo to GitHub.
- Stage 2 (AKS) and the pipeline are optional. Only do them if Stage 1 is solid.

## Stage 1 - Docker and a local cluster (start here)

    cd app
    docker build -t inventory:0.1 .
    docker run --rm -p 8080:8080 inventory:0.1
    # open http://localhost:8080 in your browser, then Ctrl+C

    kind create cluster --name learn --config ../k8s/kind-config.yaml
    kind load docker-image inventory:0.1 --name learn
    kubectl apply -f ../k8s/
    kubectl -n inventory-demo get pods -w
    kubectl -n inventory-demo port-forward svc/inventory 8080:80
    # open http://localhost:8080 - the page shows which pod served it

Then practise: scale replicas, delete a pod and watch it recover, change the
ConfigMap, bump the image tag for a rolling update and use `kubectl rollout undo`.
Break things on purpose and record them in LEARNING-LOG.md.

## Stage 2 - AKS with Terraform

    az login
    cd terraform
    terraform init && terraform plan
    terraform apply
    az aks get-credentials -g rg-k8slearn -n aks-k8slearn
    az acr build --registry <acr_login_server minus .azurecr.io> --image inventory:0.1 ../app
    # edit k8s/deployment.yaml image to <acr_login_server>/inventory:0.1, then:
    kubectl apply -f ../k8s/
    terraform destroy        # ALWAYS when you stop - the node costs money while it runs

Check `node_vm_size` is available for your subscription and region before apply.

## Stage 3 - Pipeline

`azure-pipelines.yml` builds with ACR Tasks, deploys to AKS and rolls back if the
rollout fails. Replace the placeholders and create an Azure service connection.

## Stage 4 - Extras

Container insights (Azure Monitor) with an alert on pod restarts, a Helm chart
version of the manifests, namespaces and RBAC.
