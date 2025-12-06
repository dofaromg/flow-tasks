# DecompressionUtility DLL

這個 .NET 8 Class Library 提供 ZIP 解壓縮與內容檢視功能，可編譯成 DLL 後在各模組中重複使用。

## 功能
- `ExtractZip(zipPath, destinationDirectory, overwrite = false)`: 將 ZIP 檔案解壓縮到指定資料夾，可選擇覆寫已存在檔案。
- `ListEntries(zipPath)`: 在解壓前列出壓縮檔內的檔案與資料夾。

## 建置步驟
1. 安裝 .NET 8 SDK。
2. 在此目錄執行：
   ```bash
   dotnet build
   ```
   成品 DLL 會輸出至 `bin/Debug/net8.0/DecompressionUtility.dll`。

## 上傳 / 部署
若要快速打包並上傳 DLL，可在專案根目錄執行：

```bash
bash scripts/publish_decompression_dll.sh
```

該腳本會：
- 以 Release 模式建置並產出 XML 文件註解。
- 將 DLL 與 README 收斂到 `dll/DecompressionUtility/dist/`。
- 生成 ZIP（預設 `DecompressionUtility_Release.zip`），可直接上傳到 GitHub Release、內部檔案伺服器或 Artifact Registry。

## 使用範例
```csharp
using DecompressionUtility;

var output = DecompressionHelper.ExtractZip("./input/sample.zip", "./output", overwrite: true);
var entries = DecompressionHelper.ListEntries("./input/sample.zip");
```
