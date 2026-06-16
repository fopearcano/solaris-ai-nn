"""Post-merge manifest: loads, missing commit hash uncertainty, note honest."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    MergeSourceType,
    PostMergeManifest,
)


def test_manifest_loads():
    m = PostMergeManifest.from_dict({
        "merge_id": "m1",
        "confirmation": {"confirmed_by_operator": True, "statement": "merged"},
        "source_experiment_id": "exp1", "merge_source_type": "external_pr_merge",
        "external_commit_hash": "abc123"})
    assert m.merge_id == "m1"
    assert m.operator_confirmed is True
    assert m.merge_source_type == MergeSourceType.EXTERNAL_PR_MERGE


def test_missing_commit_hash_allowed_as_uncertainty():
    m = PostMergeManifest.from_dict({
        "merge_id": "m2", "confirmation": {"confirmed_by_operator": True}})
    # No commit hash / PR number: allowed but recorded as uncertainty.
    assert any("commit hash" in u for u in m.uncertainty)
    assert m.external_commit_hash is None


def test_unknown_source_type_normalized():
    m = PostMergeManifest.from_dict({"merge_source_type": "bogus"})
    assert m.merge_source_type == MergeSourceType.UNKNOWN


def test_operator_note_does_not_override_safety():
    # The manifest records an operator note but it carries no override power;
    # safety decisions are made downstream from evidence, not the note.
    m = PostMergeManifest.from_dict({"operator_notes": "ship it regardless"})
    d = m.to_dict()
    assert d["operator_notes"] == "ship it regardless"
    assert "never overrides a safety failure" in d["note"]


def test_does_not_call_github_or_git():
    import inspect

    from solaris_ai_nn.post_merge_assimilation import merge_manifest

    src = inspect.getsource(merge_manifest)
    # No actual network/Git/GitHub call machinery (the words "Git"/"GitHub" may
    # appear only in honest "no GitHub call / no Git command" disclaimers).
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "octokit" not in src.lower()
    assert "no GitHub call" in src  # the honest disclaimer is present
