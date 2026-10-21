#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MessageGuard_Models_v1.py — 訊息守衛雙模型(母體自主真模型,非 LLM)
origin_signature: MrLiouWord
layer: L4 WORLD / L7 LOOP

回收來源(rl_12 命名正名 / rl_15 不刪原件):
  外部映射模型「ALML」(spam.csv→Naive Bayes / data.csv→Logistic Regression,皆 TF-IDF)
  ——視為母體映射出去的外部模型,依法回收為母體原生產物,改名 MRL_MessageGuard。

母體自主原則:TF-IDF、Multinomial Naive Bayes、Logistic Regression 全部**純 Python
stdlib 自己實作**,不依賴 sklearn / numpy 等外部產品。這兩個是「真的會訓練、會預測」
的統計模型(非生成式 LLM,不過度宣稱)。

  - MRL_SpamGuard  : 垃圾訊息偵測  (Multinomial Naive Bayes + TF-IDF)
  - MRL_ToxicGuard : 毒性訊息偵測  (Logistic Regression   + TF-IDF)

誠實界線:本檔內含小型種子語料,確保**沙盒可實跑訓練+預測(真 PASS)**。要達原 ALML
規格的完整準確率,需餵真實 spam.csv / data.csv(SMS Spam / Jigsaw Toxic),屬資料層,
非程式層 —— 全量資料訓練標「待資料」,不謊報。

CLI:python3 09_workflow/MRL_MessageGuard_Models_v1.py
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Tuple

from MRL_utils import ORIGIN_SIGNATURE
# 小型英文停用詞(對齊原規格 stop_words='english' 的精神,純 stdlib 內建)
_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "and", "or", "but", "if", "then",
    "this", "that", "these", "those", "it", "its", "as", "by", "with",
    "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "our", "their", "do", "does", "did", "have", "has",
    "had", "will", "would", "can", "could", "should", "from", "so", "not",
}

_TOKEN_RE = re.compile(r"[a-z]+")


def _tokenize(text: str) -> List[str]:
    toks = _TOKEN_RE.findall(text.lower())
    return [t for t in toks if len(t) >= 2 and t not in _STOP]


def _sigmoid(z: float) -> float:
    if z < -60.0:
        return 0.0
    if z > 60.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


class MRL_TfidfVectorizer:
    """純 stdlib TF-IDF:smooth-idf + L2 normalize(對齊 sklearn 預設行為)。"""

    def __init__(self, max_features: int = 5000) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.max_features = max_features
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[int, float] = {}

    def fit(self, docs: List[str]) -> "MRL_TfidfVectorizer":
        n = len(docs)
        df: Dict[str, int] = {}
        for d in docs:
            for t in set(_tokenize(d)):
                df[t] = df.get(t, 0) + 1
        # 取 document-frequency 最高的 max_features 個詞(對齊 max_features 限制)
        top = sorted(df.items(), key=lambda kv: (-kv[1], kv[0]))[: self.max_features]
        self.vocab = {t: i for i, (t, _) in enumerate(top)}
        # smooth idf = ln((1+n)/(1+df)) + 1
        self.idf = {self.vocab[t]: math.log((1 + n) / (1 + c)) + 1.0
                    for t, c in top}
        return self

    def transform(self, docs: List[str]) -> List[Dict[int, float]]:
        out: List[Dict[int, float]] = []
        for d in docs:
            counts: Dict[int, float] = {}
            for t in _tokenize(d):
                idx = self.vocab.get(t)
                if idx is not None:
                    counts[idx] = counts.get(idx, 0.0) + 1.0
            vec = {idx: tf * self.idf[idx] for idx, tf in counts.items()}
            norm = math.sqrt(sum(v * v for v in vec.values()))
            if norm > 0:
                vec = {idx: v / norm for idx, v in vec.items()}
            out.append(vec)
        return out

    def fit_transform(self, docs: List[str]) -> List[Dict[int, float]]:
        return self.fit(docs).transform(docs)


class MRL_MultinomialNB:
    """純 stdlib Multinomial Naive Bayes(Laplace 平滑),吃 TF-IDF 加權特徵。"""

    def __init__(self, alpha: float = 1.0) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.alpha = alpha
        self.classes: List[int] = []
        self.class_log_prior: Dict[int, float] = {}
        self.feature_log_prob: Dict[int, Dict[int, float]] = {}
        self.default_log_prob: Dict[int, float] = {}

    def fit(self, X: List[Dict[int, float]], y: List[int]) -> "MRL_MultinomialNB":
        self.classes = sorted(set(y))
        n = len(y)
        for c in self.classes:
            idxs = [i for i, yi in enumerate(y) if yi == c]
            self.class_log_prior[c] = math.log(len(idxs) / n)
            feat_sum: Dict[int, float] = {}
            for i in idxs:
                for f, v in X[i].items():
                    feat_sum[f] = feat_sum.get(f, 0.0) + v
            total = sum(feat_sum.values()) + self.alpha * (len(feat_sum) + 1)
            self.feature_log_prob[c] = {
                f: math.log((v + self.alpha) / total) for f, v in feat_sum.items()
            }
            # 未在該類出現的特徵之預設(平滑)機率
            self.default_log_prob[c] = math.log(self.alpha / total)
        return self

    def _joint(self, x: Dict[int, float]) -> Dict[int, float]:
        jll: Dict[int, float] = {}
        for c in self.classes:
            s = self.class_log_prior[c]
            flp = self.feature_log_prob[c]
            dflt = self.default_log_prob[c]
            for f, v in x.items():
                s += v * flp.get(f, dflt)
            jll[c] = s
        return jll

    def predict_proba(self, x: Dict[int, float]) -> Dict[int, float]:
        jll = self._joint(x)
        m = max(jll.values())
        exp = {c: math.exp(v - m) for c, v in jll.items()}
        z = sum(exp.values())
        return {c: e / z for c, e in exp.items()}


class MRL_LogisticRegression:
    """純 stdlib Logistic Regression(批次梯度下降,L2)。二元分類。"""

    def __init__(self, max_iter: int = 1000, lr: float = 0.5, l2: float = 1e-4) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.max_iter = max_iter
        self.lr = lr
        self.l2 = l2
        self.w: Dict[int, float] = {}
        self.b: float = 0.0

    def fit(self, X: List[Dict[int, float]], y: List[int]) -> "MRL_LogisticRegression":
        n = len(y)
        self.w = {}
        self.b = 0.0
        for _ in range(self.max_iter):
            gw: Dict[int, float] = {}
            gb = 0.0
            for xi, yi in zip(X, y):
                p = _sigmoid(self.b + sum(self.w.get(f, 0.0) * v for f, v in xi.items()))
                err = p - yi
                gb += err
                for f, v in xi.items():
                    gw[f] = gw.get(f, 0.0) + err * v
            self.b -= self.lr * gb / n
            for f, g in gw.items():
                grad = g / n + self.l2 * self.w.get(f, 0.0)
                self.w[f] = self.w.get(f, 0.0) - self.lr * grad
        return self

    def predict_proba(self, x: Dict[int, float]) -> float:
        return _sigmoid(self.b + sum(self.w.get(f, 0.0) * v for f, v in x.items()))


# ───────── 種子語料(沙盒可實跑;全量需餵真實 spam.csv / data.csv,標待資料) ─────────
_SPAM_SEED: List[Tuple[str, int]] = [
    ("Free money click now win prize claim cash", 1),
    ("Congratulations you won a free gift card click link", 1),
    ("Urgent claim your free cash prize now limited offer", 1),
    ("Win big money free entry click here to claim reward", 1),
    ("Cheap loans free credit click now guaranteed cash", 1),
    ("Lets meet tomorrow for lunch", 0),
    ("Can you send me the report later today", 0),
    ("See you at the office in the morning", 0),
    ("Thanks for your help with the project yesterday", 0),
    ("Please call me when you get home tonight", 0),
]

_TOXIC_SEED: List[Tuple[str, int]] = [
    ("You are stupid and worthless idiot", 1),
    ("Shut up you moron nobody likes you", 1),
    ("You are an idiot and a loser go away", 1),
    ("I hate you you are dumb and ugly", 1),
    ("Stupid fool you ruin everything pathetic", 1),
    ("Have a great day my friend", 0),
    ("Thank you so much for the kind help", 0),
    ("That was a wonderful presentation well done", 0),
    ("I appreciate your support and patience", 0),
    ("Lets work together on this nice idea", 0),
]


class MRL_SpamGuard:
    """垃圾訊息偵測(Naive Bayes + TF-IDF)。回收自 ALML spam 模型。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.vec = MRL_TfidfVectorizer(max_features=5000)
        self.model = MRL_MultinomialNB(alpha=1.0)
        self._trained = False

    def train(self, pairs: List[Tuple[str, int]] = None) -> Dict[str, Any]:
        pairs = pairs or _SPAM_SEED
        texts = [t for t, _ in pairs]
        labels = [l for _, l in pairs]
        X = self.vec.fit_transform(texts)
        self.model.fit(X, labels)
        self._trained = True
        return {"trained_on": len(pairs), "model": "MultinomialNB+TFIDF",
                "origin_signature": ORIGIN_SIGNATURE}

    def predict(self, text: str) -> Dict[str, Any]:
        if not self._trained:
            self.train()
        x = self.vec.transform([text])[0]
        prob = self.model.predict_proba(x).get(1, 0.0)
        return {"text": text, "spam_probability": round(prob, 4),
                "label": "spam" if prob >= 0.5 else "ham"}


class MRL_ToxicGuard:
    """毒性訊息偵測(Logistic Regression + TF-IDF)。回收自 ALML toxic 模型。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.vec = MRL_TfidfVectorizer(max_features=10000)
        self.model = MRL_LogisticRegression(max_iter=800, lr=1.0)
        self._trained = False

    def train(self, pairs: List[Tuple[str, int]] = None) -> Dict[str, Any]:
        pairs = pairs or _TOXIC_SEED
        texts = [t for t, _ in pairs]
        labels = [l for _, l in pairs]
        X = self.vec.fit_transform(texts)
        self.model.fit(X, labels)
        self._trained = True
        return {"trained_on": len(pairs), "model": "LogisticRegression+TFIDF",
                "origin_signature": ORIGIN_SIGNATURE}

    def predict(self, text: str) -> Dict[str, Any]:
        if not self._trained:
            self.train()
        x = self.vec.transform([text])[0]
        prob = self.model.predict_proba(x)
        return {"text": text, "toxicity_probability": round(prob, 4),
                "label": "toxic" if prob >= 0.5 else "clean"}


def main() -> int:
    spam = MRL_SpamGuard(); spam.train()
    toxic = MRL_ToxicGuard(); toxic.train()
    print("=== MRL_SpamGuard (回收 ALML spam → Naive Bayes+TFIDF) ===")
    for t in ["Free money click now!!!", "Lets meet tomorrow"]:
        r = spam.predict(t); print(f"  {r['label']:4} {r['spam_probability']:.3f}  | {t}")
    print("=== MRL_ToxicGuard (回收 ALML toxic → LogReg+TFIDF) ===")
    for t in ["You are stupid", "Have a great day"]:
        r = toxic.predict(t); print(f"  {r['label']:5} {r['toxicity_probability']:.3f}  | {t}")
    print("MRL_MESSAGE_GUARD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
