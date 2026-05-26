Predicast pipeline - Prefect orchestration
=========================================

This folder contains a minimal Prefect 2 flow to orchestrate the existing scripts in `04_Scripts_Nuevos`.

Requirements
-----------
- Python 3.10+
- Install dependencies (prefect):

```bash
pip install prefect
```

Run locally
---------

From the repository root run:

```bash
python -m 07_Sistema_Produccion.orchestrator.prefect.pipeline_flow
```

Or with prefect CLI:

```bash
prefect deployment build 07_Sistema_Produccion/orchestrator/prefect/pipeline_flow.py:pipeline_flow -n predicast-pipeline
prefect deployment apply pipeline_flow-deployment.yaml
prefect agent start --work-queue 'default'
prefect deployment run predicast-pipeline
```

Notes
----
- The flow executes the original scripts via the Python interpreter; it does not refactor them. Prefer refactoring scripts into importable functions for better observability and testing.
- Adjust `base_dir` parameter if your workspace layout differs.
