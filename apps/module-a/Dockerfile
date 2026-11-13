# Module-A Service Dockerfile
FROM python:3.10-slim

# Build from apps/: keep common/ beside module-a/ for the existing imports.
WORKDIR /app/module-a

# 安裝依賴
COPY module-a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY common/ /app/common/
COPY module-a/app.py module-a/core.py ./

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# 啟動應用
CMD ["python", "app.py"]
