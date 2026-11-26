"""
Юнит-тесты AGP (идея C19).

Запуск:
    python -m unittest discover -s tests
    pytest tests        # если установлен pytest
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agp_cli
from agp_core import build_numbers, generate_seed, pick, split_by_option_biased


class TestGenerateSeed(unittest.TestCase):
    def test_hex_sha256(self):
        seed = generate_seed()
        self.assertEqual(len(seed), 64)
        int(seed, 16)  # валидный hex

    def test_unique(self):
        self.assertNotEqual(generate_seed(), generate_seed())


class TestBuildNumbers(unittest.TestCase):
    def test_count_and_range(self):
        numbers = build_numbers("seed", count=100)
        self.assertEqual(len(numbers), 100)
        self.assertTrue(all(1 <= x <= 10 ** 6 for x in numbers))

    def test_same_seed_same_numbers(self):
        self.assertEqual(build_numbers("s", 50), build_numbers("s", 50))

    def test_bad_count_raises(self):
        with self.assertRaises(ValueError):
            build_numbers("s", 0)


class TestSplitBiased(unittest.TestCase):
    def test_all_numbers_placed(self):
        numbers = build_numbers("seed", 500)
        buckets = split_by_option_biased(numbers, 4)
        self.assertEqual(len(buckets), 4)
        self.assertEqual(sum(len(b) for b in buckets), 500)

    def test_bad_n_raises(self):
        with self.assertRaises(ValueError):
            split_by_option_biased([1, 2, 3], 0)


class TestPick(unittest.TestCase):
    def test_winner_in_elements(self):
        elements = ["a", "b", "c"]
        winner, seed, buckets = pick(elements)
        self.assertIn(winner, elements)
        self.assertEqual(len(seed), 64)
        self.assertEqual(sum(len(b) for b in buckets), 10000)

    def test_single_element(self):
        winner, _, buckets = pick(["only"])
        self.assertEqual(winner, "only")
        self.assertEqual(len(buckets), 1)
        self.assertEqual(len(buckets[0]), 10000)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            pick([])


class TestHelpers(unittest.TestCase):
    def test_duplicates_of(self):
        self.assertEqual(agp_cli.duplicates_of(["a", "b", "a", "c", "b"]), {"a", "b"})
        self.assertEqual(agp_cli.duplicates_of(["x", "y"]), set())

    def test_detect_lang(self):
        self.assertEqual(agp_cli.detect_lang([]), "ru")
        self.assertEqual(agp_cli.detect_lang(["--lang", "en"]), "en")
        self.assertEqual(agp_cli.detect_lang(["--lang=nope"]), "ru")

    def test_append_history(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "history.jsonl")
            agp_cli.append_history(path, {"winner": "Матрица"})
            agp_cli.append_history(path, {"winner": "Начало"})
            with open(path, encoding="utf-8") as f:
                lines = f.read().strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["winner"], "Матрица")


class TestMain(unittest.TestCase):
    def _run(self, argv, stdin_side_effect=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch("builtins.input", side_effect=stdin_side_effect):
            code = agp_cli.main(argv=argv)
        return code, out.getvalue(), err.getvalue()

    def test_cli_elements_and_history(self):
        with tempfile.TemporaryDirectory() as d:
            hist = os.path.join(d, "h.jsonl")
            code, out, _ = self._run(["--history", hist, "Матрица", "Интерстеллар"])
            self.assertEqual(code, 0)
            self.assertIn("Победитель", out)
            with open(hist, encoding="utf-8") as f:
                record = json.loads(f.readline())
            self.assertEqual(record["elements"], ["Матрица", "Интерстеллар"])
            self.assertEqual(record["source"], "cli")
            self.assertEqual(len(record["bucket_sizes"]), 2)
            self.assertEqual(len(record["seed"]), 64)

    def test_count_mode(self):
        code, out, _ = self._run(["--no-history"], ["2", "a", "b"])
        self.assertEqual(code, 0)
        self.assertIn("Победитель", out)

    def test_count_retry_on_bad_input(self):
        code, out, _ = self._run(["--no-history"], ["abc", "-3", "2", "x", "y"])
        self.assertEqual(code, 0)
        self.assertIn("Победитель", out)

    def test_zero_mode(self):
        code, out, _ = self._run(["--zero", "--no-history"], ["a", "b", "0"])
        self.assertEqual(code, 0)
        self.assertIn("Победитель", out)

    def test_file_mode(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "variants.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("Матрица\n\nИнтерстеллар\n")
            code, out, _ = self._run(["--file", path, "--no-history"])
            self.assertEqual(code, 0)
            self.assertIn("Пустая строка пропущена", out)
            self.assertIn("Победитель", out)

    def test_duplicate_warning(self):
        code, out, _ = self._run(["--no-history", "a", "a", "b"])
        self.assertEqual(code, 0)
        self.assertIn("уже есть", out)

    def test_eof_fails_cleanly(self):
        code, out, _ = self._run(["--no-history"], EOFError)
        self.assertEqual(code, 1)
        self.assertIn("ни одного", out)

    def test_keyboard_interrupt(self):
        code, out, _ = self._run(["--no-history"], KeyboardInterrupt)
        self.assertEqual(code, 1)
        self.assertIn("Прервано", out)

    def test_english_mode(self):
        code, out, _ = self._run(["--lang", "en", "--no-history", "a", "b"])
        self.assertEqual(code, 0)
        self.assertIn("Winner", out)


if __name__ == "__main__":
    unittest.main()
