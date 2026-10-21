/**
 * backend/modules/ai.js
 * origin_signature: "MrLiouWord"
 *
 * 不依賴外部 AI，全部走本地 FlowCoreLoop → Ollama
 */

const axios = require("axios");

// Base URL for the local FlowCoreLoop service (no trailing slash)
const FLOWCORE_URL = process.env.FLOWCORE_BASE_URL || "http://127.0.0.1:8787";

const TIMEOUT_SUBMIT = 60000; // 60s — allow time for model inference on task submission
const TIMEOUT_DEFAULT = 10000; // 10s — standard timeout for result/billing endpoints

/**
 * 分析問題（提交任務，取得 partial_result）
 * @param {string} problemText
 * @param {string} category
 * @returns {{ success, partial, task_id } | { success, error }}
 */
async function analyze(problemText, category = "general") {
  try {
    const res = await axios.post(
      `${FLOWCORE_URL}/task/submit`,
      {
        prompt: problemText,
        category,
        user_id: "mrl_local",
        source: "mrl_product",
      },
      { timeout: TIMEOUT_SUBMIT }
    );

    return {
      success: true,
      partial: res.data.partial_result,
      task_id: res.data.task_id,
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
    };
  }
}

/**
 * 取得 partial_result
 * @param {string} taskId
 */
async function getPartial(taskId) {
  try {
    const res = await axios.post(
      `${FLOWCORE_URL}/result/partial`,
      { task_id: taskId },
      { timeout: TIMEOUT_DEFAULT }
    );
    return { success: true, data: res.data };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * 確認付款並解鎖
 * @param {string} taskId
 * @param {string} paymentId
 * @param {number} amount
 */
async function confirmBilling(taskId, paymentId, amount = 299) {
  try {
    const res = await axios.post(
      `${FLOWCORE_URL}/billing/confirm`,
      {
        task_id: taskId,
        payment_id: paymentId,
        amount,
        currency: "TWD",
        status: "paid",
      },
      { timeout: TIMEOUT_DEFAULT }
    );
    return { success: true, data: res.data };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * 取得完整結果（需付款後）
 * @param {string} taskId
 */
async function getFullResult(taskId) {
  try {
    const res = await axios.post(
      `${FLOWCORE_URL}/result/full`,
      { task_id: taskId },
      { timeout: TIMEOUT_DEFAULT }
    );
    return { success: true, data: res.data };
  } catch (err) {
    if (err.response?.data?.error === "payment_required") {
      return { success: false, error: "payment_required" };
    }
    return { success: false, error: err.message };
  }
}

module.exports = {
  analyze,
  getPartial,
  confirmBilling,
  getFullResult,
};
