"""Profile similarity, duplicate detection and grade estimation.

Pure-corpus techniques (token TF-IDF cosine over title + mission +
competencies) so recommendations work with no external AI provider.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from sqlalchemy.orm import Session

from .. import models

_WORD = re.compile(r"[a-zA-Z][a-zA-Z&/+-]{1,}")
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "are", "all", "per", "etc",
    "will", "them", "their", "from", "into", "such", "have", "has", "been",
    "ensure", "provide", "support", "manage", "other", "related",
}


def tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text or "") if w.lower() not in STOPWORDS and len(w) > 2]


def profile_text(profile: models.JobProfile) -> str:
    comp_names = " ".join(pc.competency.name for pc in profile.profile_competencies if pc.competency)
    return " ".join(
        [
            (profile.job_title or "") + " " + (profile.job_title or ""),  # title weighted x2
            profile.mission or "",
            (profile.responsibilities_text or "")[:1500],
            comp_names,
        ]
    )


class SimilarityIndex:
    """In-memory TF-IDF index rebuilt lazily; invalidated on writes."""

    def __init__(self):
        self.vectors: dict[int, Counter] = {}
        self.idf: dict[str, float] = {}
        self.titles: dict[int, str] = {}
        self.dirty = True

    def build(self, db: Session):
        profiles = db.query(models.JobProfile).filter(models.JobProfile.is_active.is_(True)).all()
        docs = {p.id: Counter(tokens(profile_text(p))) for p in profiles}
        self.titles = {p.id: p.job_title for p in profiles}
        df: Counter = Counter()
        for counter in docs.values():
            df.update(counter.keys())
        n = max(len(docs), 1)
        self.idf = {term: math.log(n / (1 + freq)) + 1 for term, freq in df.items()}
        self.vectors = docs
        self.dirty = False

    def ensure(self, db: Session):
        if self.dirty or not self.vectors:
            self.build(db)

    def _weighted(self, counter: Counter) -> dict[str, float]:
        return {t: f * self.idf.get(t, 1.0) for t, f in counter.items()}

    def cosine(self, a: Counter, b: Counter) -> float:
        wa, wb = self._weighted(a), self._weighted(b)
        common = set(wa) & set(wb)
        num = sum(wa[t] * wb[t] for t in common)
        den = math.sqrt(sum(v * v for v in wa.values())) * math.sqrt(sum(v * v for v in wb.values()))
        return num / den if den else 0.0

    def similar(self, db: Session, profile_id: int | None = None, text: str | None = None, top: int = 10):
        self.ensure(db)
        query_vec = self.vectors.get(profile_id) if profile_id else Counter(tokens(text or ""))
        if not query_vec:
            return []
        scores = [
            (pid, self.cosine(query_vec, vec))
            for pid, vec in self.vectors.items()
            if pid != profile_id
        ]
        scores.sort(key=lambda x: -x[1])
        return [(pid, round(score, 4)) for pid, score in scores[:top] if score > 0.05]


INDEX = SimilarityIndex()


def find_duplicates(db: Session, threshold: float = 0.82, limit: int = 50):
    """Pairs of highly similar active profiles (potential duplicates)."""
    INDEX.ensure(db)
    ids = list(INDEX.vectors.keys())
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            # Cheap prefilter: titles share a token
            ta, tb = set(tokens(INDEX.titles.get(a, ""))), set(tokens(INDEX.titles.get(b, "")))
            if not ta & tb:
                continue
            score = INDEX.cosine(INDEX.vectors[a], INDEX.vectors[b])
            if score >= threshold:
                pairs.append({"a_id": a, "a_title": INDEX.titles[a], "b_id": b, "b_title": INDEX.titles[b], "score": round(score, 3)})
                if len(pairs) >= limit:
                    return pairs
    pairs.sort(key=lambda x: -x["score"])
    return pairs


def estimate_grade(db: Session, job_title: str, text: str = "") -> dict:
    """Estimate grade from the most similar existing profiles (k-NN vote)."""
    matches = INDEX.similar(db, text=f"{job_title} {job_title} {text}", top=12)
    votes: Counter = Counter()
    evidence = []
    for pid, score in matches:
        profile = db.get(models.JobProfile, pid)
        if profile and profile.grade:
            votes[profile.grade.code] += score
            if len(evidence) < 5:
                evidence.append({"id": pid, "title": profile.job_title, "grade": profile.grade.code, "similarity": score})
    if not votes:
        return {"grade": None, "confidence": 0, "evidence": []}
    grade, weight = votes.most_common(1)[0]
    total = sum(votes.values())
    return {"grade": grade, "confidence": round(weight / total, 2), "evidence": evidence}
