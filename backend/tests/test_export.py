"""Export pipeline tests: render plan builder + export job via the API.

The render_to_mp4 step (real FFmpeg) is exercised in the live integration
smoke test (it runs fast with the fixture MP4) but kept out of the unit suite
so CI doesn't need a GPU or heavy media files.
"""

from __future__ import annotations

import pytest

from app.media.ffmpeg_pipeline import (
    RenderParams,
    build_render_plan,
)

P = "/api/v1/projects"
EX = "export"

# ── Render plan builder (pure, no FFmpeg) ────────────────────────────────────

def _doc_with_video_clip(asset_id: str) -> dict:
    return {
        "version": 1,
        "tracks": [
            {
                "id": "v",
                "type": "video",
                "name": "Video",
                "clips": [
                    {
                        "id": "c1",
                        "kind": "video",
                        "asset_id": asset_id,
                        "start": 0.0,
                        "duration": 4.0,
                        "trim_start": 0.0,
                    }
                ],
            },
            {"id": "t", "type": "text", "name": "Text", "clips": []},
            {"id": "a", "type": "audio", "name": "Audio", "clips": []},
        ],
    }


class TestBuildRenderPlan:
    def test_video_clip_mapped(self):
        doc = _doc_with_video_clip("a1")
        plan = build_render_plan(doc, {"a1": "/tmp/a1.mp4"}, RenderParams())
        assert len(plan.video_segments) == 1
        seg = plan.video_segments[0]
        assert seg.local_path == "/tmp/a1.mp4"
        assert seg.timeline_start == 0.0
        assert seg.source_duration == 4.0
        assert not seg.is_image

    def test_unknown_asset_skipped(self):
        doc = _doc_with_video_clip("missing")
        plan = build_render_plan(doc, {}, RenderParams())
        assert plan.video_segments == []

    def test_image_clip_flagged(self):
        doc = {
            "version": 1,
            "tracks": [
                {
                    "id": "v", "type": "video", "name": "V",
                    "clips": [{"id": "i1", "kind": "image", "asset_id": "img",
                               "start": 1.0, "duration": 3.0, "trim_start": 0}],
                }
            ],
        }
        plan = build_render_plan(doc, {"img": "/tmp/img.png"}, RenderParams())
        assert plan.video_segments[0].is_image

    def test_total_duration_from_clips(self):
        doc = _doc_with_video_clip("a1")
        params = RenderParams()
        build_render_plan(doc, {"a1": "/tmp/a.mp4"}, params)
        assert params.total_duration == pytest.approx(4.0)

    def test_text_caption_parsed(self):
        doc = {
            "version": 1,
            "tracks": [
                {"id": "v", "type": "video", "name": "V", "clips": []},
                {
                    "id": "t", "type": "text", "name": "T",
                    "clips": [
                        {
                            "id": "x1", "kind": "text",
                            "start": 0.5, "duration": 2.0, "trim_start": 0,
                            "text": "Hello world",
                            "style": {"fontSize": 60, "color": "#ff0000", "y": 80, "align": "center"},
                        }
                    ],
                },
            ],
        }
        plan = build_render_plan(doc, {}, RenderParams())
        assert len(plan.captions) == 1
        cap = plan.captions[0]
        assert cap.text == "Hello world"
        assert cap.font_size == 60
        assert cap.start == pytest.approx(0.5)
        assert cap.end == pytest.approx(2.5)
        assert cap.y_pct == 80

    def test_audio_segment_mapped(self):
        doc = {
            "version": 1,
            "tracks": [
                {"id": "v", "type": "video", "name": "V", "clips": []},
                {"id": "t", "type": "text", "name": "T", "clips": []},
                {
                    "id": "a", "type": "audio", "name": "A",
                    "clips": [{"id": "au1", "kind": "audio", "asset_id": "wav1",
                               "start": 0.0, "duration": 3.0, "trim_start": 0}],
                },
            ],
        }
        plan = build_render_plan(doc, {"wav1": "/tmp/audio.wav"}, RenderParams())
        assert len(plan.audio_segments) == 1
        assert plan.audio_segments[0].source_duration == 3.0

    def test_transition_in_carried_to_segment(self):
        doc = {
            "version": 1,
            "tracks": [
                {
                    "id": "v", "type": "video", "name": "V",
                    "clips": [
                        {"id": "c1", "kind": "video", "asset_id": "a1",
                         "start": 0.0, "duration": 4.0, "trim_start": 0.0},
                        {"id": "c2", "kind": "video", "asset_id": "a2",
                         "start": 4.0, "duration": 4.0, "trim_start": 0.0,
                         "transition_in": "fade"},
                    ],
                }
            ],
        }
        plan = build_render_plan(
            doc, {"a1": "/tmp/a1.mp4", "a2": "/tmp/a2.mp4"}, RenderParams()
        )
        assert len(plan.video_segments) == 2
        segs = sorted(plan.video_segments, key=lambda s: s.timeline_start)
        assert segs[0].transition_in is None
        assert segs[1].transition_in == "fade"

    def test_no_transition_default(self):
        doc = _doc_with_video_clip("a1")
        plan = build_render_plan(doc, {"a1": "/tmp/a1.mp4"}, RenderParams())
        assert plan.video_segments[0].transition_in is None

    def test_none_string_transition_stored(self):
        doc = {
            "version": 1,
            "tracks": [
                {
                    "id": "v", "type": "video", "name": "V",
                    "clips": [{"id": "c1", "kind": "video", "asset_id": "a1",
                               "start": 0.0, "duration": 4.0, "trim_start": 0.0,
                               "transition_in": "none"}],
                }
            ],
        }
        plan = build_render_plan(doc, {"a1": "/tmp/a1.mp4"}, RenderParams())
        # "none" string passes through unchanged; render_to_mp4 treats it as hard cut
        assert plan.video_segments[0].transition_in == "none"

    def test_zero_duration_clip_ignored(self):
        doc = {
            "version": 1,
            "tracks": [
                {
                    "id": "v", "type": "video", "name": "V",
                    "clips": [{"id": "c1", "kind": "video", "asset_id": "a1",
                               "start": 0, "duration": 0, "trim_start": 0}],
                }
            ],
        }
        plan = build_render_plan(doc, {"a1": "/tmp/a.mp4"}, RenderParams())
        assert len(plan.video_segments) == 0


# ── Export API (eager mode, real FFmpeg) ─────────────────────────────────────

class TestExportAPI:
    def _make_project_with_timeline(self, client, headers) -> str:
        """Create a project, upload fixture video, save it to the timeline."""
        pid = client.post(P, headers=headers, json={"name": "Export Test"}).json()["id"]
        # Upload the real fixture MP4 as a video asset.
        fixture = (
            __import__("pathlib").Path(__file__).parent.parent
            / "app/generators/mock/fixtures/sample.mp4"
        )
        with open(fixture, "rb") as f:
            asset = client.post(
                f"{P}/{pid}/assets",
                headers=headers,
                files={"file": ("sample.mp4", f, "video/mp4")},
            ).json()

        aid = asset["id"]
        # Save a minimal timeline document with that clip.
        doc = {
            "version": 1,
            "tracks": [
                {
                    "id": "v", "type": "video", "name": "Video",
                    "clips": [{"id": "c1", "kind": "video", "asset_id": aid,
                               "start": 0, "duration": 4, "trim_start": 0}],
                },
                {"id": "t", "type": "text", "name": "Text",
                 "clips": [{"id": "tx1", "kind": "text",
                            "start": 0.5, "duration": 3, "trim_start": 0,
                            "text": "Aurora Export Test",
                            "style": {"fontSize": 40, "color": "ffffff", "y": 85, "align": "center"}}]},
                {"id": "a", "type": "audio", "name": "Audio", "clips": []},
            ],
        }
        client.put(f"{P}/{pid}/timeline", headers=headers, json=doc)
        return pid

    def test_export_produces_mp4_asset(self, client, auth_headers):
        pid = self._make_project_with_timeline(client, auth_headers)
        res = client.post(
            f"{P}/{pid}/{EX}",
            headers=auth_headers,
            json={"width": 640, "height": 360, "fps": 24, "crf": 28},
        )
        assert res.status_code == 201, res.text
        job = res.json()
        assert job["status"] == "succeeded", job.get("error")
        assert job["result_asset"] is not None
        assert job["result_asset"]["kind"] == "video"
        assert job["result_asset"]["source"] == "derived"

    def test_export_mp4_is_valid_and_non_empty(self, client, auth_headers):
        pid = self._make_project_with_timeline(client, auth_headers)
        job = client.post(
            f"{P}/{pid}/{EX}",
            headers=auth_headers,
            json={"width": 640, "height": 360, "fps": 24, "crf": 28},
        ).json()
        assert job["status"] == "succeeded"

        # Download and verify it's a real MP4.
        content_url = f"/api/v1/assets/{job['result_asset']['id']}/content"
        mp4 = client.get(content_url, headers=auth_headers)
        assert mp4.status_code == 200
        assert mp4.headers["content-type"].startswith("video/mp4")
        # MP4 files contain 'ftyp' in the first 32 bytes.
        assert b"ftyp" in mp4.content[:32]
        # Must be non-trivial (blank renders are ~1KB; real ones are much larger).
        assert len(mp4.content) > 5000

    def test_export_requires_auth(self, client):
        assert client.post("/api/v1/projects/x/export", json={}).status_code == 401

    def test_export_missing_project_404(self, client, auth_headers):
        assert (
            client.post(
                "/api/v1/projects/does-not-exist/export",
                headers=auth_headers,
                json={},
            ).status_code == 404
        )

    def test_export_invalid_params_rejected(self, client, auth_headers):
        pid = client.post(P, headers=auth_headers, json={"name": "P"}).json()["id"]
        res = client.post(
            f"{P}/{pid}/{EX}",
            headers=auth_headers,
            json={"width": 10, "fps": 200},  # below/above limits
        )
        assert res.status_code == 422
