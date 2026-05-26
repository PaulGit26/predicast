Resumen de artefactos creados:

- `frontend/nextjs/` - Next.js skeleton with `pages/index.js` and `package.json`.
- `frontend/nextjs/Dockerfile` - Dockerfile to build the frontend image.
- `infra/terraform/` - Terraform skeleton creating an S3 bucket (placeholder for full infra).
- `infra/kubernetes/` - K8s manifests for frontend Deployment/Service.
- `.github/workflows/ci-cd.yml` - CI pipeline that runs Python tests and builds/pushes Docker images to GitHub Container Registry.

Siguientes pasos para desplegar en AWS (resumen rápido):

1. Configure AWS credentials (Secrets/Github) and set real bucket names in `infra/terraform/variables.tf`.
2. Implement RDS & ElastiCache modules in Terraform or enable managed services via existing IaC.
3. Build and publish Docker images (CI does this if you enable `GITHUB_TOKEN` push to GHCR).
4. Deploy to EKS (apply k8s manifests) or use ECS/Fargate as preferred.

Comandos útiles locales:

```bash
# Frontend dev
cd 07_Sistema_Produccion/frontend/nextjs
npm install
npm run dev

# Run backend tests
python -m pytest 07_Sistema_Produccion/tests/test_pipeline_integration.py -q

# Terraform init / plan (infra)
cd 07_Sistema_Produccion/infra/terraform
terraform init
terraform plan
```
