"Tag autosuggest ranking + language-scope tests."

from lute.db import db
from lute.models.term import Term as DBTerm, TermTag
from lute.term.model import Repository


def _add_tagged_term(lang, text, tag_texts):
    t = DBTerm()
    t.language = lang
    t.text = text
    t.status = 1
    for tag in tag_texts:
        existing = db.session.query(TermTag).filter(TermTag.text == tag).first()
        t.term_tags.append(existing or TermTag(tag))
    db.session.add(t)
    db.session.commit()
    return t


def test_global_ranked_by_usage(spanish, english, app_context):
    _add_tagged_term(spanish, "uno", ["food", "verb"])
    _add_tagged_term(spanish, "dos", ["food"])
    _add_tagged_term(english, "one", ["food"])
    repo = Repository(db.session)
    ranked = repo.get_term_tags_with_counts()
    assert ranked.index("food") < ranked.index("verb"), "food (3 uses) before verb (1)"


def test_language_scope_filters_by_language(spanish, english, app_context):
    _add_tagged_term(spanish, "uno", ["spanish_only"])
    _add_tagged_term(english, "one", ["english_only"])
    repo = Repository(db.session)
    sp = repo.get_term_tags_with_counts(spanish.id)
    en = repo.get_term_tags_with_counts(english.id)
    assert "spanish_only" in sp
    assert "english_only" not in sp
    assert "english_only" in en
    assert "spanish_only" not in en


def test_falls_back_to_global_when_lang_has_no_tagged_terms(
    spanish, english, app_context
):
    _add_tagged_term(spanish, "uno", ["food", "verb"])
    repo = Repository(db.session)
    # English has no tagged terms; should fall back to global ranking.
    en = repo.get_term_tags_with_counts(english.id)
    assert "food" in en, "fallback should expose global tags"
    assert en.index("food") <= en.index("verb")


def test_empty_returns_empty_list(spanish, app_context):
    repo = Repository(db.session)
    assert repo.get_term_tags_with_counts(spanish.id) == []
