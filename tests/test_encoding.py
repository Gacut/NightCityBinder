from pathlib import Path

from nightcity.i18n import TEXT


def test_translations_are_not_mojibake():
    for language, messages in TEXT.items():
        for key, text in messages.items():
            assert "\ufffd" not in text, (language, key)
            for encoding in ("cp1250", "cp1252", "latin1"):
                try:
                    repaired = text.encode(encoding).decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                assert repaired == text, (language, key, text, repaired)


def test_scanner_source_is_utf8():
    source = Path(__file__).resolve().parents[1] / "android/src/org/nightcitybinder/ScannerActivity.java"
    text = source.read_text(encoding="utf-8")
    assert "Recognizing…" in text
    assert "Recognizingâ" not in text
