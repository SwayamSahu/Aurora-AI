"""Community blog (B1) — posts, ownership, likes, comments, sanitization.

Runs fully on the Mac (no GPU). Exercises the auth/persistence stack via the
TestClient against the isolated SQLite test DB.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": email.split("@")[0],
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "supersecret1"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_post(client, headers, **overrides):
    payload = {
        "title": "My First Post",
        "category": "tutorials",
        "body_html": "<h2>Hello</h2><p>World body text here.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers)


def test_create_generates_slug_and_readtime(client: TestClient):
    h = _register(client, "author@example.com")
    res = _create_post(client, h)
    assert res.status_code == 201
    post = res.json()
    assert post["slug"] == "my-first-post"
    assert post["read_minutes"] >= 1
    assert post["author"]["full_name"] == "author"


def test_body_html_is_sanitized(client: TestClient):
    h = _register(client, "xss@example.com")
    res = _create_post(
        client,
        h,
        body_html="<p>ok</p><script>alert(1)</script><img src=x onerror=alert(2)>",
    )
    body = res.json()["body_html"]
    assert "<script" not in body
    assert "onerror" not in body
    assert "<p>ok</p>" in body


def test_published_post_is_public_and_slugs_are_unique(client: TestClient):
    h = _register(client, "pub@example.com")
    a = _create_post(client, h).json()
    b = _create_post(client, h).json()  # same title → deduped slug
    assert a["slug"] != b["slug"]

    # Public read without auth.
    res = client.get(f"/api/v1/blog/posts/{a['slug']}")
    assert res.status_code == 200
    assert res.json()["liked_by_me"] is False


def test_draft_hidden_from_others(client: TestClient):
    author = _register(client, "drafter@example.com")
    draft = _create_post(client, author, status="draft").json()
    # Anonymous → 404
    assert client.get(f"/api/v1/blog/posts/{draft['slug']}").status_code == 404
    # Author → visible
    res = client.get(f"/api/v1/blog/posts/{draft['slug']}", headers=author)
    assert res.status_code == 200


def test_only_author_can_edit_and_delete(client: TestClient):
    author = _register(client, "owner@example.com")
    other = _register(client, "intruder@example.com")
    post = _create_post(client, author).json()

    # Other user cannot edit or delete.
    assert (
        client.patch(
            f"/api/v1/blog/posts/{post['id']}",
            json={"title": "Hacked"},
            headers=other,
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/api/v1/blog/posts/{post['id']}", headers=other).status_code
        == 403
    )

    # Author can edit then delete.
    edited = client.patch(
        f"/api/v1/blog/posts/{post['id']}",
        json={"title": "Updated Title"},
        headers=author,
    )
    assert edited.status_code == 200
    assert edited.json()["slug"] == "updated-title"
    assert (
        client.delete(f"/api/v1/blog/posts/{post['id']}", headers=author).status_code
        == 204
    )


def test_like_toggle_is_idempotent_and_counts(client: TestClient):
    author = _register(client, "likeauthor@example.com")
    liker = _register(client, "liker@example.com")
    post = _create_post(client, author).json()

    r1 = client.post(
        f"/api/v1/blog/posts/{post['id']}/like", json={"liked": True}, headers=liker
    ).json()
    assert r1["like_count"] == 1 and r1["liked_by_me"] is True
    # Liking again stays at 1 (unique constraint / idempotent).
    r2 = client.post(
        f"/api/v1/blog/posts/{post['id']}/like", json={"liked": True}, headers=liker
    ).json()
    assert r2["like_count"] == 1
    # Unlike → 0.
    r3 = client.post(
        f"/api/v1/blog/posts/{post['id']}/like", json={"liked": False}, headers=liker
    ).json()
    assert r3["like_count"] == 0

    # Anonymous like is rejected.
    assert (
        client.post(
            f"/api/v1/blog/posts/{post['id']}/like", json={"liked": True}
        ).status_code
        == 401
    )


def test_comments_add_list_and_author_only_delete(client: TestClient):
    author = _register(client, "cauthor@example.com")
    commenter = _register(client, "commenter@example.com")
    other = _register(client, "cother@example.com")
    post = _create_post(client, author).json()

    c = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "Great post!"},
        headers=commenter,
    )
    assert c.status_code == 201
    comment_id = c.json()["id"]

    listing = client.get(f"/api/v1/blog/posts/{post['slug']}/comments")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["author"]["full_name"] == "commenter"

    # Non-author can't delete someone else's comment.
    assert (
        client.delete(f"/api/v1/blog/comments/{comment_id}", headers=other).status_code
        == 403
    )
    # Comment author can.
    assert (
        client.delete(
            f"/api/v1/blog/comments/{comment_id}", headers=commenter
        ).status_code
        == 204
    )


def test_list_filter_and_category_counts(client: TestClient):
    h = _register(client, "lister@example.com")
    _create_post(client, h, title="Tut One", category="tutorials")
    _create_post(client, h, title="Prompt One", category="prompts")
    _create_post(client, h, title="Prompt Two", category="prompts")

    counts = client.get("/api/v1/blog/categories").json()
    assert counts.get("prompts") == 2
    assert counts.get("tutorials") == 1

    only_prompts = client.get("/api/v1/blog/posts?category=prompts").json()
    assert only_prompts["total"] == 2
    assert all(p["category"] == "prompts" for p in only_prompts["items"])

    search = client.get("/api/v1/blog/posts?q=Tut").json()
    assert search["total"] == 1


def test_media_upload_public_read_and_cover_attach(client: TestClient):
    author = _register(client, "mediauthor@example.com")

    # The route only validates content_type, not real PNG structure.
    png = b"\x89PNG\r\n\x1a\nfake-but-good-enough-for-storage-round-trip"
    up = client.post(
        "/api/v1/blog/media",
        files={"file": ("cover.png", png, "image/png")},
        headers=author,
    )
    assert up.status_code == 201
    media = up.json()
    assert media["url"].endswith(f"/blog/media/{media['id']}")

    # Publicly readable, no auth required.
    got = client.get(media["url"].replace("/api/v1", "/api/v1"))
    assert got.status_code == 200
    assert got.headers["content-type"] == "image/png"
    assert got.content == png

    # Attach as a post cover; cover_url resolves in the API response.
    post = _create_post(client, author, cover_media_id=media["id"]).json()
    assert post["cover_media_id"] == media["id"]
    assert post["cover_url"] == media["url"]


def test_media_upload_rejects_non_image_and_requires_auth(client: TestClient):
    author = _register(client, "badupload@example.com")
    rejected = client.post(
        "/api/v1/blog/media",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=author,
    )
    assert rejected.status_code == 422

    anon = client.post(
        "/api/v1/blog/media",
        files={"file": ("cover.png", b"\x89PNG", "image/png")},
    )
    assert anon.status_code == 401


def test_media_not_found_returns_404(client: TestClient):
    assert client.get("/api/v1/blog/media/does-not-exist").status_code == 404
