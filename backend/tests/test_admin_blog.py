"""Blog admin console — admin bypass on post/comment ownership, the
moderation dashboard, and comment hide/edit. Runs fully on the Mac (no GPU)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import User


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


def _make_admin(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.is_superuser = True
    db_session.commit()


def _create_post(client, headers, **overrides):
    payload = {
        "title": "My First Post",
        "category": "tutorials",
        "body_html": "<h2>Hello</h2><p>World body text here.</p>",
        "status": "published",
        **overrides,
    }
    return client.post("/api/v1/blog/posts", json=payload, headers=headers)


# --------------------------------- post CRUD -------------------------------- #
def test_admin_can_edit_any_post(client: TestClient, db_session):
    h_author = _register(client, "bauthor1@example.com")
    post = _create_post(client, h_author).json()

    h_admin = _register(client, "badmin1@example.com")
    _make_admin(db_session, "badmin1@example.com")

    res = client.patch(
        f"/api/v1/blog/posts/{post['id']}",
        json={"title": "Edited by admin"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Edited by admin"


def test_admin_can_delete_any_post(client: TestClient, db_session):
    h_author = _register(client, "bauthor2@example.com")
    post = _create_post(client, h_author).json()

    h_admin = _register(client, "badmin2@example.com")
    _make_admin(db_session, "badmin2@example.com")

    res = client.delete(f"/api/v1/blog/posts/{post['id']}", headers=h_admin)
    assert res.status_code == 204


def test_non_admin_still_blocked_from_others_posts(client: TestClient, db_session):
    h_author = _register(client, "bauthor3@example.com")
    post = _create_post(client, h_author).json()

    h_other = _register(client, "bintruder3@example.com")
    res = client.patch(
        f"/api/v1/blog/posts/{post['id']}", json={"title": "hijack"}, headers=h_other
    )
    assert res.status_code == 403


def test_admin_can_view_others_drafts(client: TestClient, db_session):
    h_author = _register(client, "bauthor4@example.com")
    post = _create_post(client, h_author, status="draft").json()

    h_admin = _register(client, "badmin4@example.com")
    _make_admin(db_session, "badmin4@example.com")

    res = client.get(f"/api/v1/blog/posts/{post['slug']}", headers=h_admin)
    assert res.status_code == 200


# ------------------------------ moderation dashboard ------------------------ #
def test_admin_posts_dashboard_lists_across_authors(client: TestClient, db_session):
    h1 = _register(client, "bauthor5@example.com")
    h2 = _register(client, "bauthor6@example.com")
    _create_post(client, h1, title="Post A", status="published")
    _create_post(client, h2, title="Post B", status="draft")

    h_admin = _register(client, "badmin5@example.com")
    _make_admin(db_session, "badmin5@example.com")

    res = client.get("/api/v1/admin/blog/posts", headers=h_admin)
    assert res.status_code == 200
    titles = [p["title"] for p in res.json()["items"]]
    assert "Post A" in titles
    assert "Post B" in titles  # draft included


def test_admin_posts_dashboard_filters_by_status_and_author(
    client: TestClient, db_session
):
    h1 = _register(client, "bauthor7@example.com")
    user1 = db_session.scalar(select(User).where(User.email == "bauthor7@example.com"))
    _create_post(client, h1, title="Draft One", status="draft")
    _create_post(client, h1, title="Published One", status="published")

    h_admin = _register(client, "badmin6@example.com")
    _make_admin(db_session, "badmin6@example.com")

    drafts = client.get("/api/v1/admin/blog/posts?status=draft", headers=h_admin).json()
    assert all(p["status"] == "draft" for p in drafts["items"])

    by_author = client.get(
        f"/api/v1/admin/blog/posts?author_id={user1.id}", headers=h_admin
    ).json()
    assert len(by_author["items"]) == 2


def test_non_admin_gets_403_on_admin_blog_routes(client: TestClient, db_session):
    h = _register(client, "bregular@example.com")
    assert client.get("/api/v1/admin/blog/posts", headers=h).status_code == 403


# -------------------------------- comments ----------------------------------- #
def test_admin_can_delete_any_comment(client: TestClient, db_session):
    h_author = _register(client, "bauthor8@example.com")
    post = _create_post(client, h_author).json()
    h_commenter = _register(client, "bcommenter8@example.com")
    comment = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "Nice post!"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "badmin7@example.com")
    _make_admin(db_session, "badmin7@example.com")

    res = client.delete(f"/api/v1/blog/comments/{comment['id']}", headers=h_admin)
    assert res.status_code == 204


def test_admin_can_hide_and_unhide_comment(client: TestClient, db_session):
    h_author = _register(client, "bauthor9@example.com")
    post = _create_post(client, h_author).json()
    h_commenter = _register(client, "bcommenter9@example.com")
    comment = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "Spam link here"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "badmin8@example.com")
    _make_admin(db_session, "badmin8@example.com")

    hidden = client.patch(
        f"/api/v1/admin/blog/comments/{comment['id']}",
        json={"is_hidden": True},
        headers=h_admin,
    )
    assert hidden.status_code == 200
    assert hidden.json()["is_hidden"] is True

    # Public comment list no longer shows it, and comment_count drops.
    public_comments = client.get(f"/api/v1/blog/posts/{post['slug']}/comments").json()
    assert not any(c["id"] == comment["id"] for c in public_comments)
    post_after = client.get(f"/api/v1/blog/posts/{post['slug']}").json()
    assert post_after["comment_count"] == 0

    # Admin's own moderation view still shows it (marked hidden).
    admin_comments = client.get(
        f"/api/v1/admin/blog/posts/{post['id']}/comments", headers=h_admin
    ).json()
    assert any(c["id"] == comment["id"] and c["is_hidden"] for c in admin_comments)

    unhidden = client.patch(
        f"/api/v1/admin/blog/comments/{comment['id']}",
        json={"is_hidden": False},
        headers=h_admin,
    )
    assert unhidden.json()["is_hidden"] is False
    post_restored = client.get(f"/api/v1/blog/posts/{post['slug']}").json()
    assert post_restored["comment_count"] == 1


def test_admin_can_edit_comment_body(client: TestClient, db_session):
    h_author = _register(client, "bauthor10@example.com")
    post = _create_post(client, h_author).json()
    h_commenter = _register(client, "bcommenter10@example.com")
    comment = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "original text"},
        headers=h_commenter,
    ).json()

    h_admin = _register(client, "badmin9@example.com")
    _make_admin(db_session, "badmin9@example.com")

    res = client.patch(
        f"/api/v1/admin/blog/comments/{comment['id']}",
        json={"body": "[redacted]"},
        headers=h_admin,
    )
    assert res.status_code == 200
    assert res.json()["body"] == "[redacted]"


def test_deleting_hidden_comment_does_not_double_decrement(
    client: TestClient, db_session
):
    h_author = _register(client, "bauthor11@example.com")
    post = _create_post(client, h_author).json()
    h_commenter = _register(client, "bcommenter11@example.com")
    c1 = client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "one"},
        headers=h_commenter,
    ).json()
    client.post(
        f"/api/v1/blog/posts/{post['id']}/comments",
        json={"body": "two"},
        headers=h_commenter,
    )

    h_admin = _register(client, "badmin10@example.com")
    _make_admin(db_session, "badmin10@example.com")
    client.patch(
        f"/api/v1/admin/blog/comments/{c1['id']}",
        json={"is_hidden": True},
        headers=h_admin,
    )
    assert client.get(f"/api/v1/blog/posts/{post['slug']}").json()["comment_count"] == 1

    client.delete(f"/api/v1/blog/comments/{c1['id']}", headers=h_admin)
    # Was already excluded from the visible count when hidden — deleting it
    # must not decrement an already-correct count a second time.
    assert client.get(f"/api/v1/blog/posts/{post['slug']}").json()["comment_count"] == 1
