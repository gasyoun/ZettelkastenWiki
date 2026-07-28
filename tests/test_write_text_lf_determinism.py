"""write_text() must emit LF-only bytes regardless of build host.

Path.write_text()'s default newline handling applies universal-newline
translation (CRLF on Windows, LF elsewhere), which makes a sha256 of the
generated output a property of the build platform. Reads back in byte mode
(no ``encoding=``) so no read-side translation could mask the defect.
"""

from zettelkastenwiki.site import write_text


def test_write_text_emits_lf_only(tmp_path):
    target = tmp_path / "out" / "note.html"
    write_text(target, "line one\nline two\nline three\n")

    raw = target.read_bytes()

    assert b"\r\n" not in raw
    assert b"\r" not in raw
    assert raw.count(b"\n") == 3
