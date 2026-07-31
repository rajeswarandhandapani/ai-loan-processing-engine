"""Tests for the ingestion pipeline in app/rag/ingestion.py."""

from pathlib import Path

import pytest

from app.core.config import Settings
from app.rag.ingestion import (
    CHUNK_SIZE,
    POLICY_TITLE,
    SAMPLE_POLICY_TEXT,
    chunk_ids,
    extract_pdf_text,
    load_policy_text,
    resolve_pdf_parser,
    split_policy_text,
)

SAMPLE_PDF = Path(__file__).parent / "sample_data/policy/sample_lending_policy.pdf"


def make_settings(**overrides) -> Settings:
    """Settings built from explicit values only, ignoring the developer's .env."""
    return Settings(_env_file=None, **overrides)


def test_split_tags_every_chunk_with_title_and_index():
    docs = split_policy_text(SAMPLE_POLICY_TEXT)

    assert len(docs) > 1
    assert all(doc.metadata["title"] == POLICY_TITLE for doc in docs)
    assert [doc.metadata["chunk_id"] for doc in docs] == list(range(len(docs)))


def test_split_respects_chunk_size():
    docs = split_policy_text(SAMPLE_POLICY_TEXT)
    assert all(len(doc.page_content) <= CHUNK_SIZE for doc in docs)


def test_chunk_ids_are_stable_across_runs():
    first = chunk_ids(split_policy_text(SAMPLE_POLICY_TEXT))
    second = chunk_ids(split_policy_text(SAMPLE_POLICY_TEXT))

    assert first == second
    assert first[0] == "policy-chunk-0"
    # Stable, unique ids are what make re-ingestion an update instead of a duplicate.
    assert len(set(first)) == len(first)


def test_resolve_parser_auto_prefers_document_intelligence_when_configured():
    settings = make_settings(
        POLICY_PDF_PARSER="auto",
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://example.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="key",
    )
    assert resolve_pdf_parser(settings) == "azure_di"


def test_resolve_parser_auto_falls_back_to_pypdf_without_credentials():
    assert resolve_pdf_parser(make_settings(POLICY_PDF_PARSER="auto")) == "pypdf"


def test_resolve_parser_rejects_azure_di_without_credentials():
    settings = make_settings(POLICY_PDF_PARSER="azure_di")
    with pytest.raises(ValueError, match="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"):
        resolve_pdf_parser(settings)


def test_resolve_parser_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unknown POLICY_PDF_PARSER"):
        resolve_pdf_parser(make_settings(POLICY_PDF_PARSER="tesseract"))


def test_pypdf_extraction_runs_on_the_sample_pdf():
    """The bundled sample is a scan, so pypdf legitimately finds no text layer."""
    text = extract_pdf_text(SAMPLE_PDF, make_settings(POLICY_PDF_PARSER="pypdf"))
    assert isinstance(text, str)


def test_load_policy_text_falls_back_when_pdf_has_no_text_layer():
    text = load_policy_text(SAMPLE_PDF, make_settings(POLICY_PDF_PARSER="pypdf"))
    assert text == SAMPLE_POLICY_TEXT


def test_load_policy_text_falls_back_when_pdf_is_missing(tmp_path):
    text = load_policy_text(tmp_path / "nope.pdf", make_settings(POLICY_PDF_PARSER="pypdf"))
    assert text == SAMPLE_POLICY_TEXT


def test_load_policy_text_uses_real_extraction_when_there_is_a_text_layer(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.rag.ingestion.extract_pdf_text", lambda path, settings: "REAL POLICY TEXT " * 50
    )
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    text = load_policy_text(pdf, make_settings(POLICY_PDF_PARSER="pypdf"))
    assert text.startswith("REAL POLICY TEXT")
