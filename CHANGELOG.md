# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.0.2] — 2026-04-20

### Fixed

#### Code Quality
- Remove 125+ dead code lines from `names_parser.py` — commented-out `__main__` block with undefined function calls (`create_login_string`, `string_findings`, `email_belongs_toname`)
- Fix ambiguous variable name `l` → `avg_letters`/`avg_sentences` in `text_readability.py` `coleman_liau_index()`
- Fix ambiguous variable name `l` → `l_value` in `text_anonymizer.py` `apply_l_diversity()`
- Remove unused variable `uppers` in `string_validation.py` `has_mixed_case_anomaly()`
- Fix `Faker` forward reference in `text_dummy.py` using `TYPE_CHECKING` import
- Remove f-string without placeholders in `text_matcher.py` (2 occurrences)
- Fix membership test syntax `not X in Y` → `X not in Y` in `names_parser.py`

#### Security
- Add `os.path.realpath()` path sanitization to `text_anonymizer` CLI (`run_anonymize_file`, `run_anonymize_csv`)
- Add `os.path.realpath()` path sanitization to `cli_base.py` `write_output()`

#### text_parser
- Fixed smart quote removal in `normalize_text()` — curly quotes (`\u201c`, `\u201d`, `\u2018`, `\u2019`) are now properly stripped when `strip_quotes=True`

#### Security
- Added `os.path.realpath()` path sanitization to all CLI file I/O in `text_parser`, `text_matcher`, `text_dummy`, and `text_anonymizer` — prevents path traversal via `..` components or symlinks

### Changed

#### Code Quality
- Move imports to top of file in all 6 language parsers (`spanish_parser.py`, `english_parser.py`, `portuguese_parser.py`, `french_parser.py`, `german_parser.py`, `italian_parser.py`) — fixes E402 violations
- Fix all trailing whitespace and blank-line whitespace across 43 files
- Fix all invalid escape sequences (W605)
- Apply `ruff format` to all Python files for consistent formatting

#### Infrastructure
- Add `[tool.ruff]` configuration to `pyproject.toml` — target Python 3.10, line length 150, per-file-ignores for `__init__.py` re-exports, legacy modules, and test files
- Add PyPI classifiers and `[project.scripts]` CLI entry points to `pyproject.toml`
- Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` community files
- Add `.github/workflows/ci.yml` — GitHub Actions CI with lint + test matrix (Python 3.10–3.13)

### Added

#### Tests
- `test_text_matcher.py` — 19 tests for `MatcherConfig`, `TextMatcher` init, `compare_names`, `find_best_match`, `detect_duplicates`, `batch_compare`, `compare_phrases`
- `test_text_parser.py` — 16 tests for `TextParser` init, `normalize`, `extract_emails`, `extract_phones`, `extract_urls`, `extract_ips`, `remove_articles`, `fix_encoding`, `validate_id`, `prepare_for_comparison`
- `test_text_dummy.py` — 14 tests for `TextDummy` init, seed reproducibility, `name`, `email`, `phone`, `address`, `iban`, `credit_card_number`, `fake_batch`

### Changed

#### Structure
- Added `__init__.py` with public API exports for `text_matcher`, `text_parser`, `text_dummy`, and `utils` subpackages — consistent with `text_anonymizer`
- Unified locale profiles: `LocaleProfile`, `ParserLocaleProfile`, and `AnonymizerLocaleProfile` now inherit from shared `BaseLocaleProfile` in `utils/_locale.py`
- Added `py.typed` marker (PEP 561) for typed package support

#### Performance
- Hoisted `_SOUNDEX_MAP` dict from inside `soundex()` to module level in `string_similarity.py` — avoids dict recreation per call
- Hoisted `_COMMON_BIGRAMS` and `_PLACEHOLDERS` sets from inside `is_gibberish()` and `is_placeholder_text()` to module-level `frozenset` constants in `text_readability.py`
- Pre-compiled 10 regex patterns at module level in `text_normalizer.py` — `normalize_text()` no longer recompiles on each call
- Pre-compiled date, email, and URL regex patterns at module level in `string_validation.py` — `data_type_inference()` no longer recompiles on each call

### Added

#### Tests
- `test_string_ops_core.py` — 30 tests for `flat_vowels`, `normalize_spaces`, `erase_allspaces`, `normalize_symbols`, `erase_specialchar`, `fix_spanish`, `string_filter`, `string_aZ`, `string_aZ09`, `reorder_comma_fullname`, `split_all`
- `test_string_similarity_core.py` — 27 tests for `levenshtein_score`, `jaro_winkler_score`, `jaccard_similarity`, `sorensen_dice_coefficient`, `ratcliff_obershelp_score`, `lcs_score`, `mra_similarity`
- `test_text_normalizer.py` — 24 tests for `normalize_text`, `normalize_whitespace`, `remove_punctuation_marks`, `remove_special_characters`, `remove_parentheses_and_content`, `strip_quotes`, `prepare_for_comparison`, `mask_text`

---

### Added

#### text_parser
- `TextParser` — Unified locale-aware API for text parsing across 6 languages and 12 locales
- `TextExtractor` — 25+ regex extractors for emails, phones, URLs, dates, IBANs, NIFs, etc.
- `normalize_text()`, `prepare_for_comparison()` — Text normalization pipeline
- `NamesParser` — Person and company name parsing
- `IdCardParser` — Spanish/European NIF validation (28 countries)
- `LanguageNormalizer` — Abbreviation expansion + language detection
- `EncodingFixer` — Universal mojibake repair
- Language-specific phonetic reduction: Spanish, English, Portuguese, French, German, Italian
- `TextReadability` — Flesch Reading Ease, Flesch-Kincaid, Gunning Fog, Coleman-Liau, ARI, complexity score

#### text_matcher
- `TextMatcher` — Multi-algorithm fuzzy matching (Levenshtein, Jaro-Winkler, Soundex, Metaphone, Double Metaphone, MRA, LCS, Sørensen-Dice)
- `AlgorithmSelector` — Use-case-based algorithm recommendation
- `MatchResult` — Structured match result dataclass
- `MLSimilarityAdapter` — ML model integration for similarity scoring

#### text_dummy
- `TextDummy` — Fake data generation for 60+ data types with Pydantic model auto-filling
- `DummyField`, `LocaleProfile` — Configuration for locale-aware fake data
- CLI interface for batch fake data generation

#### text_anonymizer
- `TextAnonymizer` — PII detection and anonymization with 7 strategies (redact, mask, replace, hash, generalize, pseudonymize, suppress)
- `PiiType`, `Strategy` enums — 12 PII types, 7 anonymization strategies
- `obfuscate_email()` — Email-specific anonymization
- CLI interface for file and CSV anonymization

#### utils
- `string_ops` — Low-level text utilities + phone normalization
- `string_similarity` — Similarity algorithms + WordSimilarity class + Hamming distance
- `string_validation` — Checksum validation (Luhn, IBAN, ISBN, EAN, VAT, SWIFT/BIC) + data type inference

#### Infrastructure
- Project scaffold with Hatchling build system
- Copilot agentic stack: 4 instructions, 7 skills, 4 agents, 20 prompts, 4 hooks
- Test suite with pytest
- `llms.txt` for AI agent context

---

[Unreleased]: https://github.com/jrodriguezgar/ShadeTripTxt/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/jrodriguezgar/ShadeTripTxt/compare/v0.0.1...v0.0.2
