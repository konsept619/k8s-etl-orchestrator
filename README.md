# k8-etl-orchestrator
## Abstract
There are 10 containers, that require cyclic maintenance. All of them have the same (from logic point of view) goal, but 5 of them are using very similar configuration unlike the rest of them which are operating on completely different variables and settings. 

## Installation
### Deploy Vault on cluster
Prepare a Helm repo and a namespace
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

kubectl create namespace vault
```
Create vault configuration
```yaml
#vault-values.yaml
server:
  enabled: true
  image:
    repository: "hashicorp/vault"
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "1000m"
      memory: "1Gi"

  dataStorage:
    enabled: true
    size: 10Gi
    storageClass: local-path

  auditStorage:
    enabled: false

  standalone:
    enabled: false

  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true

        listener "tcp" {
          tls_disable = 1
          address = "[::]:8200"
          cluster_address = "[::]:8201"
        }

        storage "raft" {
          path = "/vault/data"
        }

        service_registration "kubernetes" {}

ui:
  enabled: true

injector:
  enabled: false
```
Install Vault:

```bash
helm install vault hashicorp/vault -n vault -f vault-values.yaml
```
### Initialize and unseal Vault
Initialization:
```bash
kubectl exec -n vault vault-0 -- vault operator init -key-shares=1 -key-threshold=1
```
Output contains:
- Unseal key
- Initial root key

Unseal node:
```bash
kubectl exec -n vault vault-0 -- vault operator unseal <UNSEAL_KEY>
```
Login and verify:
```bash
kubectl exec -it -n vault vault-0 -- sh
vault login <ROOT_KEY>
vault status
exit
```

Verify if Vault is exposed:
```bash
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -n external-secrets -- \
  curl -s http://vault.vault.svc:8200/v1/sys/health
```

### Enable KV engine and put some secrets
```bash
kubectl exec -it -n vault vault-0 -- sh
vault login <ROOT_KEY>

vault secrets enable -path=secret kv-v2

vault kv put secret/integration/etl-app \
  db_password='SuperStrongPassword123!' \
  aws_default_region='eu-central-1' \
  http_proxy='http://proxy.internal:3128'

vault kv get secret/integration/etl-app
exit
```
