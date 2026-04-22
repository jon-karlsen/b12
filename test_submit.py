"""Tests for the canonicalization and signing primitives in submit.py."""
import hashlib
import hmac
import os
import unittest
from datetime import datetime, timezone
from unittest import mock

from submit import SIGNING_SECRET, build_payload, canonical_json, main, sign


class CanonicalJsonTests(unittest.TestCase):
    def test_keys_are_sorted(self):
        self.assertEqual(canonical_json({"b": "2", "a": "1"}), b'{"a":"1","b":"2"}')

    def test_no_extra_whitespace(self):
        self.assertEqual(canonical_json({"a": "1", "b": "2"}), b'{"a":"1","b":"2"}')

    def test_utf8_encoding_preserves_non_ascii(self):
        body = canonical_json({"name": "Jón"})
        self.assertEqual(body.decode("utf-8"), '{"name":"Jón"}')
        self.assertNotIn(b"\\u", body)


class SignTests(unittest.TestCase):
    def test_matches_stdlib_hmac(self):
        body = b'{"hello":"world"}'
        expected = hmac.new(SIGNING_SECRET, body, hashlib.sha256).hexdigest()
        self.assertEqual(sign(body), f"sha256={expected}")

    def test_header_format(self):
        self.assertTrue(sign(b"").startswith("sha256="))

    def test_signs_raw_bytes_not_text(self):
        utf8 = canonical_json({"name": "Jón"})
        self.assertEqual(
            sign(utf8),
            f"sha256={hmac.new(SIGNING_SECRET, utf8, hashlib.sha256).hexdigest()}",
        )


class BuildPayloadTests(unittest.TestCase):
    def _payload(self, **overrides):
        defaults = dict(
            name="Test Applicant",
            email="applicant@example.com",
            resume_link="https://example.com/resume.pdf",
            repository_link="https://github.com/example/repo",
            action_run_link="https://github.com/example/repo/actions/runs/1",
            now=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        defaults.update(overrides)
        return build_payload(**defaults)

    def test_required_keys_present(self):
        self.assertEqual(
            set(self._payload()),
            {
                "action_run_link",
                "email",
                "name",
                "repository_link",
                "resume_link",
                "timestamp",
            },
        )

    def test_timestamp_is_iso8601_utc(self):
        self.assertEqual(self._payload()["timestamp"], "2026-01-01T12:00:00+00:00")


class DryRunTests(unittest.TestCase):
    def test_dry_run_exits_cleanly_without_posting(self):
        env = {
            "APPLICANT_NAME": "Jane",
            "APPLICANT_EMAIL": "jane@example.com",
            "RESUME_LINK": "https://example.com/resume.pdf",
            "REPOSITORY_LINK": "https://github.com/example/repo",
            "ACTION_RUN_LINK": "https://github.com/example/repo/actions/runs/1",
            "DRY_RUN": "1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("urllib.request.urlopen") as urlopen:
                exit_code = main()
        urlopen.assert_not_called()
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
