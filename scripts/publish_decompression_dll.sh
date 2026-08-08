#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="${REPO_ROOT}/dll/DecompressionUtility"
PROJECT_FILE="${PROJECT_DIR}/DecompressionUtility.csproj"
CONFIG="${CONFIG:-Release}"
OUTPUT_DIR="${PROJECT_DIR}/bin/${CONFIG}/net8.0"
DIST_DIR="${PROJECT_DIR}/dist"
ZIP_NAME="${ZIP_NAME:-DecompressionUtility_${CONFIG}.zip}"

if ! command -v dotnet >/dev/null 2>&1; then
  echo "dotnet SDK 未找到，請先安裝 .NET 8 SDK。" >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "zip 指令未找到，請安裝 zip 工具後重試。" >&2
  exit 1
fi

echo "[1/4] 還原與建置 (${CONFIG})..."
dotnet restore "${PROJECT_FILE}" >/dev/null
# 產出 XML 文件以便共用說明
dotnet build "${PROJECT_FILE}" -c "${CONFIG}" /p:GenerateDocumentationFile=true >/dev/null

if [ ! -f "${OUTPUT_DIR}/DecompressionUtility.dll" ]; then
  echo "建置失敗：找不到輸出 DLL (${OUTPUT_DIR}/DecompressionUtility.dll)。" >&2
  exit 1
fi

echo "[2/4] 整理佈署內容..."
rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"
cp "${OUTPUT_DIR}/DecompressionUtility.dll" "${DIST_DIR}/"
[ -f "${OUTPUT_DIR}/DecompressionUtility.xml" ] && cp "${OUTPUT_DIR}/DecompressionUtility.xml" "${DIST_DIR}/"
cp "${PROJECT_DIR}/README.md" "${DIST_DIR}/README.md"

echo "[3/4] 打包 ZIP..."
(
  cd "${DIST_DIR}"
  zip -rq "${ZIP_NAME}" .
)

ARTIFACT_PATH="${DIST_DIR}/${ZIP_NAME}"
echo "[4/4] 完成。佈署包位置：${ARTIFACT_PATH}"
echo "可直接上傳到內部 Artifact Registry、GitHub Release 或文件系統供重複使用。"
