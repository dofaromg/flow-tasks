FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY amp ./amp
COPY adapters ./adapters
COPY cli.py ./cli.py
COPY config.sample.yaml ./config.sample.yaml

VOLUME ["/data"]
ENV AMP_CONFIG=/data/config.yaml

ENTRYPOINT ["python", "cli.py"]
CMD ["--config", "/data/config.yaml"]
