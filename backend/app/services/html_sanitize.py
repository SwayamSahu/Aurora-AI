"""Server-side HTML sanitization for user-authored blog bodies.

Blog posts are user-generated and shown to other users, so their HTML must be
sanitized to prevent stored XSS. We use `nh3` (Rust `ammonia` bindings) with a
strict allow-list covering the editor's formatting set. The frontend also
sanitizes on render (DOMPurify) for defense in depth.
"""

from __future__ import annotations

import nh3

# Tags the rich-text editor can produce.
_ALLOWED_TAGS = {
    "p",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "del",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "a",
    "img",
    "span",
    "div",
}

_ALLOWED_ATTRS = {
    # Note: don't list "rel" here — nh3 adds it via `link_rel` below and
    # panics if both are set.
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title"},
    "span": {"class"},
    "div": {"class"},
    "code": {"class"},
    "pre": {"class"},
}


def sanitize_html(html: str) -> str:
    """Return a safe subset of *html*. Scripts, event handlers and disallowed
    tags/attributes are stripped; links are forced to safe schemes."""
    if not html:
        return ""
    return nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        link_rel="noopener noreferrer nofollow",
        url_schemes={"http", "https", "mailto"},
    )


def html_to_text(html: str) -> str:
    """Strip all tags → plain text (for excerpts / read-time / search)."""
    if not html:
        return ""
    return nh3.clean(html, tags=set(), attributes={}).strip()
