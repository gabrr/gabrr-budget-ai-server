"""Compatibility wrapper for parsing tools."""

from app.agents.tools.parsing.pdf_docling import *  # noqa: F403

from app.agents.tools.parsing.pdf_docling import parse_pdf, parse_pdf_text

__all__ = ["parse_pdf", "parse_pdf_text"]
