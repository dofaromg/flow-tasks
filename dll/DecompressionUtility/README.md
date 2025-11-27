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

## 使用範例
```csharp
using DecompressionUtility;

var output = DecompressionHelper.ExtractZip("./input/sample.zip", "./output", overwrite: true);
var entries = DecompressionHelper.ListEntries("./input/sample.zip");
```
