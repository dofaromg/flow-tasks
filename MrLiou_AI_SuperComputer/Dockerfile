FROM python:3.11-slim

LABEL maintainer="MrLiouWord"
LABEL description="MRLiou AI SuperComputer — flowcore_loop + fusion engine"

WORKDIR /mrl-ai

COPY flowcore_loop.py .
COPY ai_fusion_core.py .
COPY ai_providers.py .
COPY ai_providers_config.json .

ENV PYTHONPATH=/mrl-ai
ENV PYTHONIOENCODING=utf-8
ENV MRL_PORT=8787

EXPOSE 8787

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8787/health')" || exit 1

CMD ["python", "flowcore_loop.py"]
