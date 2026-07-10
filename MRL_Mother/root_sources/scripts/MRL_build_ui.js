#!/usr/bin/env node
// MRL_build_ui — 單一來源產生 worker 可 import 的產品 UI 模組
// origin_signature: MrLiouWord
//
// 來源：src/mrl_app.html (MRL_Product_Entry_UI · canonical)
// 產物：src/mrl_app_ui.js  (export const APP_HTML = "...";)
// Cloudflare Worker 與本機 Python 伺服器共用同一份 HTML，避免兩份走鐘。
// 用法：node scripts/MRL_build_ui.js

const fs = require("fs");
const path = require("path");

const repo = path.resolve(__dirname, "..");
const srcHtml = path.join(repo, "src", "mrl_app.html");
const outJs = path.join(repo, "src", "mrl_app_ui.js");

const html = fs.readFileSync(srcHtml, "utf8");
const banner =
  "// AUTO-GENERATED from src/mrl_app.html by scripts/MRL_build_ui.js — 勿手改\n" +
  "// origin_signature: MrLiouWord\n";
fs.writeFileSync(outJs, banner + "export const APP_HTML = " + JSON.stringify(html) + ";\n", "utf8");

console.log("MRL_build_ui: wrote " + path.relative(repo, outJs) + " (" + html.length + " bytes from mrl_app.html)");
