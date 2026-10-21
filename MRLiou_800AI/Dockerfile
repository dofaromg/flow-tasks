FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
EXPOSE 8787
CMD ["python", "-m", "mrliou_800ai.cli", "serve", "--host", "0.0.0.0", "--port", "8787"]
