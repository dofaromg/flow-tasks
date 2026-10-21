using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace DecompressionUtility;

/// <summary>
/// 提供 ZIP 檔案的解壓縮與檢視功能，封裝成可重複使用的 DLL。
/// </summary>
public static class DecompressionHelper
{
    /// <summary>
    /// 將指定 ZIP 檔案解壓到目標資料夾。
    /// </summary>
    /// <param name="zipPath">ZIP 檔案路徑。</param>
    /// <param name="destinationDirectory">解壓輸出的目標資料夾。</param>
    /// <param name="overwrite">若目標檔案已存在，是否允許覆寫。</param>
    /// <returns>解壓後的實際輸出路徑。</returns>
    /// <exception cref="FileNotFoundException">當 ZIP 檔案不存在時。</exception>
    public static string ExtractZip(string zipPath, string destinationDirectory, bool overwrite = false)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(zipPath);
        ArgumentException.ThrowIfNullOrWhiteSpace(destinationDirectory);

        if (!File.Exists(zipPath))
        {
            throw new FileNotFoundException($"找不到 ZIP 檔案: {zipPath}");
        }

        Directory.CreateDirectory(destinationDirectory);

        // 使用 ZipArchive 以支援覆寫選項
        using var archive = ZipFile.OpenRead(zipPath);
        foreach (var entry in archive.Entries)
        {
            var destinationPath = Path.Combine(destinationDirectory, entry.FullName);
            var destinationDir = Path.GetDirectoryName(destinationPath);
            if (!string.IsNullOrEmpty(destinationDir))
            {
                Directory.CreateDirectory(destinationDir);
            }

            if (string.IsNullOrEmpty(entry.Name))
            {
                continue; // 目錄條目，不需處理
            }

            if (!overwrite && File.Exists(destinationPath))
            {
                continue;
            }

            entry.ExtractToFile(destinationPath, overwrite: true);
        }

        return Path.GetFullPath(destinationDirectory);
    }

    /// <summary>
    /// 列出 ZIP 檔案內容，方便在實際解壓前檢視。
    /// </summary>
    /// <param name="zipPath">ZIP 檔案路徑。</param>
    /// <returns>檔案與資料夾條目的清單。</returns>
    /// <exception cref="FileNotFoundException">當 ZIP 檔案不存在時。</exception>
    public static IReadOnlyList<string> ListEntries(string zipPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(zipPath);

        if (!File.Exists(zipPath))
        {
            throw new FileNotFoundException($"找不到 ZIP 檔案: {zipPath}");
        }

        using var archive = ZipFile.OpenRead(zipPath);
        return archive.Entries
            .Select(entry => string.IsNullOrEmpty(entry.Name) ? $"{entry.FullName} (資料夾)" : entry.FullName)
            .ToList();
    }
}
