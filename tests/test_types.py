"""Tests for Pydantic models in types.py (FOUN-04)."""

from logseq_mcp.types import BlockEntity, BlockRef, PageEntity, PageRef


def test_blockref_from_int():
    b = BlockRef.model_validate(42)
    assert b.id == 42


def test_blockref_from_dict():
    b = BlockRef.model_validate({"id": 42})
    assert b.id == 42


def test_pageref_from_int():
    p = PageRef.model_validate(7)
    assert p.id == 7
    assert p.name == ""


def test_blockentity_compact_children_stripped():
    be = BlockEntity.model_validate({"uuid": "abc", "children": [["uuid", "somevalue"]]})
    assert be.children == []


def test_blockentity_full_children_parsed():
    be = BlockEntity.model_validate(
        {
            "uuid": "parent",
            "children": [{"uuid": "child", "content": "hello"}],
        }
    )
    assert len(be.children) == 1
    assert be.children[0].uuid == "child"


def test_blockentity_self_ref_resolves():
    # model_rebuild() must have been called — nested parsing works
    be = BlockEntity.model_validate({"uuid": "root", "children": [{"uuid": "nested"}]})
    assert isinstance(be.children[0], BlockEntity)
