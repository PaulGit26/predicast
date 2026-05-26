FROM python:3.11-slim

WORKDIR /app

# Install in stages to stay within Docker daemon memory limits
RUN pip install --no-cache-dir --prefer-binary \
    flask>=3.0.0 \
    numpy>=1.26.2 \
    pandas>=2.1.3 \
    joblib>=1.3.2

RUN pip install --no-cache-dir --prefer-binary \
    scikit-learn>=1.3.2

RUN pip install --no-cache-dir --prefer-binary \
    xgboost==2.0.3

RUN pip install --no-cache-dir --prefer-binary \
    scipy>=1.11.4

RUN pip install --no-cache-dir --prefer-binary \
    statsmodels>=0.14.0

RUN pip install --no-cache-dir --prefer-binary \
    matplotlib>=3.8.2 seaborn>=0.13.1

COPY scripts/ ./scripts/
COPY run_pipeline.py server.py ./

EXPOSE 5001
CMD ["python", "server.py"]
