"""test_MRL_messageguard_models.py (origin: MrLiouWord)

回收自外部映射模型 ALML(spam=NaiveBayes / toxic=LogReg,皆 TF-IDF)。
驗證母體自主純 stdlib 實作真的會訓練+正確分類。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_MessageGuard_Models_v1 import (
    MRL_SpamGuard, MRL_ToxicGuard, MRL_TfidfVectorizer,
    MRL_MultinomialNB, MRL_LogisticRegression,
)


def test_tfidf_l2_normalized():
    vec = MRL_TfidfVectorizer()
    X = vec.fit_transform(["free money cash", "meet you tomorrow"])
    for x in X:
        norm2 = sum(v * v for v in x.values())
        assert abs(norm2 - 1.0) < 1e-6 or norm2 == 0.0  # L2 normalized


def test_spamguard_separates():
    g = MRL_SpamGuard(); g.train()
    spam = g.predict("Free money click now win prize claim cash")
    ham = g.predict("Lets meet tomorrow for lunch")
    assert spam["spam_probability"] > ham["spam_probability"]
    assert spam["label"] == "spam" and ham["label"] == "ham"
    assert 0.0 <= spam["spam_probability"] <= 1.0


def test_toxicguard_separates():
    g = MRL_ToxicGuard(); g.train()
    tox = g.predict("You are stupid and worthless idiot")
    clean = g.predict("Have a great day my friend")
    assert tox["toxicity_probability"] > clean["toxicity_probability"]
    assert tox["label"] == "toxic" and clean["label"] == "clean"
    assert 0.0 <= clean["toxicity_probability"] <= 1.0


def test_nb_predict_proba_sums_to_one():
    vec = MRL_TfidfVectorizer()
    X = vec.fit_transform(["free cash prize", "see you tomorrow"])
    nb = MRL_MultinomialNB().fit(X, [1, 0])
    p = nb.predict_proba(vec.transform(["free cash prize"])[0])
    assert abs(sum(p.values()) - 1.0) < 1e-9


def test_origin_signature():
    assert MRL_SpamGuard().origin_signature == "MrLiouWord"
    assert MRL_ToxicGuard().origin_signature == "MrLiouWord"
    assert MRL_LogisticRegression().origin_signature == "MrLiouWord"
