import re

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None

UNIVERSAL_STOP_WORDS = {
    "experience", "work", "team", "role", "ability", "skill", "skills",
    "knowledge", "understanding", "strong", "good", "excellent", "great",
    "year", "years", "candidate", "position", "company", "organization",
    "using", "based", "including", "include", "required", "require",
    "preferred", "responsibility", "responsibilities", "requirement",
    "requirements", "qualification", "qualifications", "job", "employment",
    "type", "familiarity", "field", "fields", "discipline", "related",
    "basic", "level", "sample", "jd", "description", "tailored", "resume",
    "cv", "entry", "trainee", "opportunity", "environment", "detail",
    "details", "task", "tasks", "duty", "duties", "looking", "seeking",
    "join", "plus", "bonus", "must", "nice", "have", "able", "proven",
    "track", "record", "demonstrated", "equivalent", "minimum", "degree",
    "ats", "keyword", "keywords", "key", "ideal", "fresher", "freshers",
    "b.e", "b.tech", "bca", "mca", "m.tech", "b.sc", "m.sc", "bachelor", "master",
    "junior", "senior", "lead", "intern", "associate", "support", "help", "use",
    "perform", "create", "write", "identify", "collect", "present", "understand",
    "involve", "activity", "activities", "concept", "concepts", "cycle", "title",
    "update", "updates", "maintain", "participate", "resolve", "conduct", "ensure",
}

LEMMA_NORMALIZATION = {
    "datum": "data",
    "analytic": "analytics",
    "analyzing": "analysis",
    "analyze": "analysis",
    "preprocessing": "preprocess",
    "reporting": "report",
    "cleaning": "clean",
    "projects": "project",
    "skills": "skill",
    "systems": "system",
    "applications": "application",
    "defects": "defect",
    "bugs": "bug",
    "cases": "case",
}


def _clean_lemma(raw_lemma: str) -> str:
    lemma = raw_lemma.lower().strip().strip(".")
    return LEMMA_NORMALIZATION.get(lemma, lemma)


def _normalize_raw_text(text: str) -> str:
    text = re.sub(r"[\r\n()\[\]:;]+", " . ", text)
    text = re.sub(r"[/|•·]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _canonical_bigram(w1: str, w2: str) -> str:
    return " ".join(sorted([w1, w2]))


def extract_all_terms(text: str) -> tuple[dict[str, int], dict[str, int], set[str], set[str]]:
    if not text:
        return {}, {}, set(), set()

    cleaned_text = _normalize_raw_text(text)
    phrase_freq: dict[str, int] = {}
    word_freq: dict[str, int] = {}
    all_lemmas: set[str] = set()
    canonical_bigrams: set[str] = set()

    if _NLP is not None:
        doc = _NLP(cleaned_text[:25000])
        content_tokens = []

        for token in doc:
            if token.is_punct or token.is_space:
                content_tokens.append(None)
                continue

            lemma = _clean_lemma(token.lemma_)
            if (
                not token.is_stop
                and len(lemma) >= 2
                and re.match(r"^[a-z][a-z0-9+#-]*$", lemma)
                and lemma not in UNIVERSAL_STOP_WORDS
                and token.pos_ in {"NOUN", "PROPN", "ADJ", "VERB"}
            ):
                content_tokens.append((lemma, token.pos_))
                if token.pos_ in {"NOUN", "PROPN", "ADJ"}:
                    all_lemmas.add(lemma)
            else:
                content_tokens.append(None)

        for i in range(len(content_tokens) - 1):
            t1, t2 = content_tokens[i], content_tokens[i + 1]
            if t1 is None or t2 is None:
                continue
            w1, pos1 = t1
            w2, pos2 = t2

            if w1 != w2 and (pos1 in {"NOUN", "PROPN"} or pos2 in {"NOUN", "PROPN"}):
                canonical_bigrams.add(_canonical_bigram(w1, w2))
                if pos2 in {"NOUN", "PROPN"}:
                    phrase = f"{w1} {w2}"
                    phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 2

        for item in content_tokens:
            if item is None:
                continue
            word, pos = item
            if pos in {"NOUN", "PROPN"} and len(word) >= 3:
                word_freq[word] = word_freq.get(word, 0) + 1
    else:
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#-]{1,}\b", cleaned_text.lower())
        filtered = [_clean_lemma(t) for t in tokens if _clean_lemma(t) not in UNIVERSAL_STOP_WORDS]
        all_lemmas.update(filtered)
        for tok in filtered:
            if len(tok) >= 3:
                word_freq[tok] = word_freq.get(tok, 0) + 1
        for i in range(len(filtered) - 1):
            if filtered[i] != filtered[i + 1]:
                phrase = f"{filtered[i]} {filtered[i + 1]}"
                phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 2
                canonical_bigrams.add(_canonical_bigram(filtered[i], filtered[i + 1]))

    return phrase_freq, word_freq, all_lemmas, canonical_bigrams


def extract_keywords(
    text: str,
    top_n: int | None = 18,
    exclude_terms: set[str] | None = None,
) -> list[str]:
    exclude = {t.lower().strip() for t in (exclude_terms or set())}
    phrase_freq, word_freq, all_lemmas, canonical_bigrams = extract_all_terms(text)

    if top_n is None:
        all_terms = set(phrase_freq.keys()) | set(word_freq.keys()) | all_lemmas | canonical_bigrams
        return sorted(all_terms - exclude)

    ranked_phrases = sorted(phrase_freq.items(), key=lambda x: (-x[1], x[0]))
    kept_phrases = []
    seen_canonical = set()

    for phrase, _ in ranked_phrases:
        if phrase in exclude:
            continue
        parts = phrase.split()
        canon = _canonical_bigram(parts[0], parts[1]) if len(parts) == 2 else phrase
        stem_pair = tuple(sorted(p[:6] for p in parts))
        if canon in seen_canonical or stem_pair in seen_canonical:
            continue
        seen_canonical.add(canon)
        seen_canonical.add(stem_pair)
        kept_phrases.append(phrase)
        if len(kept_phrases) >= max(1, int(top_n * 0.65)):
            break

    covered_words = {w for phrase in kept_phrases for w in phrase.split()} | exclude
    prefixes = {w[:6] for w in covered_words if len(w) >= 6}

    ranked_words = sorted(word_freq.items(), key=lambda x: (-x[1], x[0]))
    kept_words = []
    for word, _ in ranked_words:
        if word in covered_words:
            continue
        if len(word) >= 6 and word[:6] in prefixes:
            continue
        kept_words.append(word)
        if len(kept_phrases) + len(kept_words) >= top_n:
            break

    return list(dict.fromkeys(kept_phrases + kept_words))[:top_n]