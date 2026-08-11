"""Tests for app.text_extraction."""

from app.text_extraction import extract_years_statement


def test_extract_years_statement_finds_explicit_statement():
    assert extract_years_statement("Looking for someone with 3+ years of experience.") == 3.0


def test_extract_years_statement_takes_the_largest_match():
    text = "Junior role (1 year of experience) but we'd love 5+ years of experience too."
    assert extract_years_statement(text) == 5.0


def test_extract_years_statement_returns_none_when_absent():
    assert extract_years_statement("No experience requirement mentioned here.") is None
