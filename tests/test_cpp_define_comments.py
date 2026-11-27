"""A block comment in a backslash-continued C++ ``#define`` is not a syntax error (#5551)."""
import pytest

from graphify.extract import _normalize_cpp_define_comments, extract_cpp

pytest.importorskip("tree_sitter_cpp")

_MACRO = (
    "#pragma once\n"
    "\n"
    "#define RUN_ONCE(x)                 \\\n"
    "    do                              \\\n"
    "    {                               \\\n"
    "        run(x); /* the comment */   \\\n"
    "    } while(0)\n"
    "\n"
    "inline void real_function() {}\n"
)


def test_block_comment_in_multiline_define_is_not_a_syntax_error(tmp_path):
    p = tmp_path / "c.hpp"
    p.write_text(_MACRO)
    result = extract_cpp(p)
    assert result.get("parse_errors") is None
    assert "real_function()" in [n["label"] for n in result["nodes"]]


def test_symbols_match_the_comment_free_control(tmp_path):
    with_comment = tmp_path / "c.hpp"
    with_comment.write_text(_MACRO)
    control = tmp_path / "c_control.hpp"
    control.write_text(_MACRO.replace("/* the comment */", " " * len("/* the comment */")))

    def labels(p):
        return sorted(n["label"] for n in extract_cpp(p)["nodes"] if n.get("file_type") == "code" and "(" in n["label"])

    assert labels(with_comment) == labels(control)


def test_normalization_preserves_offsets_and_only_touches_defines():
    src = (
        b"#define M(x) \\\n"
        b"  f(x); /* c */ \\\n"
        b"  g()\n"
        b"#define ONE_LINE 1 /* single-line define, left alone */\n"
        b"int a; /* keep */\n"
    )
    out = _normalize_cpp_define_comments(src)
    assert len(out) == len(src)
    assert out.count(b"\n") == src.count(b"\n")
    assert b"/* c */" not in out
    assert b"/* single-line define, left alone */" in out
    assert b"/* keep */" in out


def test_source_without_a_multiline_define_is_unchanged():
    src = b"int f() { return 1; } /* c */\n#define X 1\n"
    assert _normalize_cpp_define_comments(src) == src
