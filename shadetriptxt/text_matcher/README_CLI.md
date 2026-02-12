# TextMatcher — CLI

Command-line interface for fuzzy text comparison, name matching, deduplication, and diff analysis.

## Quick Start

```bash
# Compare two names
python -m shadetriptxt.text_matcher.cli compare "José" "Jose" --locale es_ES

# Compare full names
python -m shadetriptxt.text_matcher.cli compare-names "Juan Fco García" "Juan Francisco Garcia"

# Find best match from candidates
python -m shadetriptxt.text_matcher.cli find-match "Smithe" --candidates "Smith,Smyth,Jones"

# Detect duplicates in a file
python -m shadetriptxt.text_matcher.cli duplicates --input names.txt --threshold 0.85

# With response file (arguments from file)
python -m shadetriptxt.text_matcher.cli @params.txt
```

---

## Global Options

Every subcommand inherits these flags:

| Flag | Short | Description |
|------|-------|-------------|
| `--quiet` | `-q` | Suppress non-essential output |
| `--debug` | | Enable debug mode with detailed output |
| `--output-format` | | Output format: `text` (default) or `json` |
| `--no-color` | | Disable ANSI colors |
| `--ci` | | CI mode: JSON output, no colors, exit codes |
| `--stats` | | Show processing statistics at the end |

### Matcher Options

Most comparison subcommands also accept these tuning flags (via `_add_matcher_args`):

| Flag | Description |
|------|-------------|
| `--locale` / `-l` | Locale for abbreviation dictionaries (default: `es_ES`) |
| `--preset` / `-p` | Config preset: `strict`, `default`, `lenient`, `fuzzy` |
| `--levenshtein` | Levenshtein threshold (0.0–1.0) |
| `--jaro-winkler` | Jaro-Winkler threshold (0.0–1.0) |
| `--metaphone` | Require phonetic match (`true`/`false`) |
| `--debug` | Show detailed comparison breakdown |
| `--output-format json` | Structured JSON output |

---

## Presets

Presets configure thresholds and phonetic requirements for different use cases:

| Preset | Levenshtein | Jaro-Winkler | Metaphone | Use Case |
|--------|-------------|--------------|-----------|----------|
| `strict` | 0.95 | 0.95 | required | Legal/financial data, exact matching |
| `default` | 0.85 | 0.90 | required | General-purpose identity resolution |
| `lenient` | 0.75 | 0.85 | optional | User-input matching, search |
| `fuzzy` | 0.60 | 0.70 | disabled | Broad search, suggestions |

```bash
python -m shadetriptxt.text_matcher.cli compare "Roberto" "Robert" --preset lenient
python -m shadetriptxt.text_matcher.cli presets   # Show all presets
```

---

## Subcommands

### `compare` (alias: `cmp`)

Compare two single words or names with abbreviation and phonetic support.

```bash
python -m shadetriptxt.text_matcher.cli compare "José" "Jose" --locale es_ES
python -m shadetriptxt.text_matcher.cli cmp "Francisco" "Fco" --debug
python -m shadetriptxt.text_matcher.cli cmp "Miguel" "Michel" --preset lenient
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First word or name |
| `text2` | | *(positional)* | Second word or name |
| `--output` | `-o` | | Write result to file |
| `--strict` | | `false` | Require phonetic match |

---

### `compare-names` (alias: `cn`)

Compare multi-word full names with token alignment and ordering.

```bash
python -m shadetriptxt.text_matcher.cli compare-names "Juan Fco García" "Juan Francisco Garcia"
python -m shadetriptxt.text_matcher.cli cn "MARTINEZ LOPEZ MARIA" "María López Martínez" --no-order
python -m shadetriptxt.text_matcher.cli cn "Roberto García" "Robert Garcia" --fuzzy-align
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First full name |
| `text2` | | *(positional)* | Second full name |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.9` | Similarity threshold |
| `--no-order` | | `false` | Ignore word order |
| `--fuzzy-align` | | `false` | Use fuzzy alignment (e.g. ROBERT ≈ ROBERTO) |

---

### `compare-text` (alias: `ct`)

Compare two phrases or sentences using Sørensen-Dice coefficient.

```bash
python -m shadetriptxt.text_matcher.cli compare-text "premium leather wallet" "leather wallet premium"
python -m shadetriptxt.text_matcher.cli ct "fast delivery service" "quick delivery service" --threshold 0.7
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First phrase |
| `text2` | | *(positional)* | Second phrase |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.8` | Similarity threshold |

---

### `find-match` (alias: `fm`)

Find the best match for a target from a list of candidates.

```bash
python -m shadetriptxt.text_matcher.cli find-match "Smithe" --candidates "Smith,Smyth,Jones"
python -m shadetriptxt.text_matcher.cli fm "García" --candidates-file names.txt --threshold 0.9
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `target` | | *(positional)* | Target string to match |
| `--candidates` | `-c` | | Comma-separated candidates |
| `--candidates-file` | `-cf` | | File with one candidate per line |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.85` | Minimum threshold |

---

### `find-matches` (alias: `fms`)

Find top-K matches for a target from a list of candidates (ranked).

```bash
python -m shadetriptxt.text_matcher.cli find-matches "Smithe" --candidates "Smith,Smyth,Jones,Smithson" --top-k 3
python -m shadetriptxt.text_matcher.cli fms "García" --candidates-file names.txt --threshold 0.7
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `target` | | *(positional)* | Target string to match |
| `--candidates` | `-c` | | Comma-separated candidates |
| `--candidates-file` | `-cf` | | File with one candidate per line |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.7` | Minimum threshold |
| `--top-k` | `-k` | | Maximum results to return |

---

### `duplicates` (alias: `dup`)

Detect duplicates in a list using similarity matching with optional blocking optimization.

```bash
python -m shadetriptxt.text_matcher.cli duplicates --input names.txt --threshold 0.85
python -m shadetriptxt.text_matcher.cli dup --items "Smith,Smyth,Jones,Smithe" --no-blocking
python -m shadetriptxt.text_matcher.cli dup --input large_list.txt --parallel
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--items` | | | Comma-separated items |
| `--input` | `-i` | | File with one item per line |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.85` | Similarity threshold |
| `--no-blocking` | | `false` | Disable blocking optimization |
| `--parallel` | | `false` | Enable parallel processing |

---

### `phonetic-dups` (alias: `pd`)

Find phonetically similar names using MRA or Metaphone algorithms.

```bash
python -m shadetriptxt.text_matcher.cli phonetic-dups --input names.txt
python -m shadetriptxt.text_matcher.cli pd --items "Smith,Smyth,Schmidt,Jones" --use-metaphone
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--items` | | | Comma-separated names |
| `--input` | `-i` | | File with one name per line |
| `--output` | `-o` | | Write result to file |
| `--threshold` | `-t` | `0.8` | Similarity threshold |
| `--use-metaphone` | | `false` | Use Metaphone instead of MRA |

---

### `diff`

Detailed text/line diff — shows additions, deletions, and changes.

```bash
python -m shadetriptxt.text_matcher.cli diff "The quick brown fox" "The fast brown fox"
python -m shadetriptxt.text_matcher.cli diff --file1 old.txt --file2 new.txt --context-lines 5
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | | First text |
| `text2` | | | Second text |
| `--file1` | | | Read first text from file |
| `--file2` | | | Read second text from file |
| `--output` | `-o` | | Write result to file |
| `--case-sensitive` | | `false` | Case-sensitive comparison |
| `--context-lines` | | `3` | Context lines in diff output |

---

### `diff-code` (alias: `dc`)

Compare code blocks — language-aware with whitespace/comment handling.

```bash
python -m shadetriptxt.text_matcher.cli diff-code --file1 v1.py --file2 v2.py
python -m shadetriptxt.text_matcher.cli dc "def foo(): pass" "def foo(): return None" --language python
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | | First code snippet |
| `text2` | | | Second code snippet |
| `--file1` | | | Read first code from file |
| `--file2` | | | Read second code from file |
| `--output` | `-o` | | Write result to file |
| `--language` | | `python` | Programming language |
| `--keep-whitespace` | | `false` | Don't ignore whitespace |
| `--ignore-comments` | | `false` | Remove comments before comparison |

---

### `normalize` (alias: `norm`)

Normalize text for comparison — whitespace, case, accents, punctuation.

```bash
python -m shadetriptxt.text_matcher.cli normalize "  José  García-López  "
python -m shadetriptxt.text_matcher.cli norm "HELLO WORLD" --case-mode lower --for-names
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text to normalize |
| `--output` | `-o` | | Write result to file |
| `--for-names` | | `false` | Name-specific normalization |
| `--case-mode` | | | Case mode: `upper`, `lower`, `title`, `none` |

---

### `similarity` (alias: `sim`)

Simple similarity percentage between two strings (SequenceMatcher ratio).

```bash
python -m shadetriptxt.text_matcher.cli similarity "hello" "hallo"
python -m shadetriptxt.text_matcher.cli sim "García" "Garcia"
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First string |
| `text2` | | *(positional)* | Second string |
| `--output` | `-o` | | Write result to file |

---

### `same-chars` (alias: `sc`)

Check if two strings contain the same characters (anagram detection).

```bash
python -m shadetriptxt.text_matcher.cli same-chars "listen" "silent"
python -m shadetriptxt.text_matcher.cli sc "García López" "López García"
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First string |
| `text2` | | *(positional)* | Second string |
| `--output` | `-o` | | Write result to file |

---

### `patterns` (alias: `pat`)

Find common patterns between two texts using Longest Common Subsequence (LCS).

```bash
python -m shadetriptxt.text_matcher.cli patterns "abcdefg" "acdeg" --min-length 2
python -m shadetriptxt.text_matcher.cli pat "Juan García" "Juan Garcia López"
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | *(positional)* | First text |
| `text2` | | *(positional)* | Second text |
| `--output` | `-o` | | Write result to file |
| `--min-length` | | `3` | Minimum subsequence length |

---

### `algorithm` (alias: `algo`)

Show algorithm selection information — which similarity algorithm is optimal for given inputs.

```bash
python -m shadetriptxt.text_matcher.cli algorithm "José" "Jose"
python -m shadetriptxt.text_matcher.cli algo --list-all
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text1` | | | First text (for auto-detection) |
| `text2` | | | Second text (for auto-detection) |
| `--list-all` | | `false` | List all use cases and algorithms |

---

### `presets`

Show all available configuration presets with their threshold values.

```bash
python -m shadetriptxt.text_matcher.cli presets
```

---

### `batch`

Batch compare pairs from a CSV file — one pair per row.

```bash
python -m shadetriptxt.text_matcher.cli batch --input pairs.csv
python -m shadetriptxt.text_matcher.cli batch -i pairs.csv --delimiter ";" --preset lenient -o results.csv
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--input` | `-i` | *(required)* | CSV file (`word1,word2` per line) |
| `--output` | `-o` | | Write result to file |
| `--delimiter` | `-d` | `,` | Column delimiter |
| `--encoding` | | `utf-8` | File encoding |

---

## Supported Locales

| Code | Language | Country |
|------|----------|---------|
| `es_ES` | Spanish | Spain |
| `es_MX` | Spanish | Mexico |
| `es_AR` | Spanish | Argentina |
| `es_CO` | Spanish | Colombia |
| `es_CL` | Spanish | Chile |
| `en_US` | English | United States |
| `en_GB` | English | United Kingdom |
| `pt_BR` | Portuguese | Brazil |
| `pt_PT` | Portuguese | Portugal |
| `fr_FR` | French | France |
| `de_DE` | German | Germany |
| `it_IT` | Italian | Italy |

---

## Examples

### Identity resolution pipeline

```bash
# 1. Detect duplicates in a name list
python -m shadetriptxt.text_matcher.cli duplicates --input clients.txt --threshold 0.85 --preset default -o dups.txt

# 2. Also check phonetic duplicates
python -m shadetriptxt.text_matcher.cli phonetic-dups --input clients.txt -o phonetic_dups.txt
```

### Batch comparison with JSON output

```bash
python -m shadetriptxt.text_matcher.cli batch --input pairs.csv --output-format json -o results.json
```

### Debug mode for tuning

```bash
python -m shadetriptxt.text_matcher.cli compare "Miguel" "Michel" --debug --preset lenient
# Shows: algorithm scores, phonetic codes, abbreviation lookup, final decision
```

### Using a response file

Create `params.txt`:
```
duplicates
--input
names.txt
--threshold
0.80
--preset
lenient
-o
results.txt
```

```bash
python -m shadetriptxt.text_matcher.cli @params.txt
```

---

## CI Integration

Use `--ci` flag for CI/CD pipelines:

```bash
# Forces JSON output, disables colors, returns proper exit codes
python -m shadetriptxt.text_matcher.cli compare "Juan" "Joan" --ci
echo $?  # 0 = success, 1 = user error, 2 = unexpected error
```

### Exit Codes

| Code | Meaning |
|------|----------|
| `0` | Success |
| `1` | User error (invalid arguments, missing input) |
| `2` | Unexpected runtime error |
| `130` | Interrupted (Ctrl+C) |

### Environment Variables

| Variable | Effect |
|----------|--------|
| `NO_COLOR` | Disable ANSI colors (any value) |

Colors are also auto-disabled when stdout is not a TTY (pipes, redirects).

### GitHub Actions

```yaml
jobs:
  data-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install shadetriptxt[full]

      - name: Detect duplicates in client list
        run: |
          python -m shadetriptxt.text_matcher.cli duplicates \
            --input data/clients.txt \
            --threshold 0.85 --preset default --ci \
            -o duplicates.json

      - name: Validate name matching
        run: |
          python -m shadetriptxt.text_matcher.cli compare \
            "Juan García" "Joan Garcia" --ci

      - uses: actions/upload-artifact@v4
        with:
          name: duplicates-report
          path: duplicates.json
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    environment {
        NO_COLOR = '1'
    }
    stages {
        stage('Setup') {
            steps {
                sh 'pip install shadetriptxt[full]'
            }
        }
        stage('Detect Duplicates') {
            steps {
                sh '''
                    python -m shadetriptxt.text_matcher.cli duplicates \
                        --input data/clients.txt \
                        --threshold 0.85 --preset default --ci \
                        -o duplicates.json
                '''
                archiveArtifacts artifacts: 'duplicates.json'
            }
        }
        stage('Batch Comparison') {
            steps {
                sh '''
                    python -m shadetriptxt.text_matcher.cli batch \
                        --input data/pairs.csv --ci \
                        -o results.json
                '''
                archiveArtifacts artifacts: 'results.json'
            }
        }
    }
    post {
        failure {
            echo 'Data quality check failed — review duplicates report'
        }
    }
}
```

### Azure DevOps Pipeline

```yaml
steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.12'
  - script: pip install shadetriptxt[full]
    displayName: Install shadetriptxt

  - script: |
      python -m shadetriptxt.text_matcher.cli duplicates \
        --input $(Build.SourcesDirectory)/data/clients.txt \
        --threshold 0.85 --ci -o $(Build.ArtifactStagingDirectory)/duplicates.json
    displayName: Detect duplicates

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)/duplicates.json
      artifactName: duplicates-report
```

---

## Programmatic API

Invoke the CLI from Python code without subprocess:

```python
from shadetriptxt.text_matcher.cli import run_api, CLIResult

# Compare two names
result: CLIResult = run_api(["compare", "García", "Garcia"])
if result.ok:
    print(result.data)   # Structured result dict
    print(result.stats)  # {"compared": 1}

# Detect duplicates
result = run_api(["duplicates", "--input", "names.txt", "--threshold", "0.85"])
if result.ok:
    for dup in result.data:
        print(dup)
else:
    print(f"Error: {result.error}")
```

### CLIResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `exit_code` | `int` | 0 success, non-zero error |
| `data` | `Any` | Structured output (dict, list, str) |
| `stats` | `Dict[str, int]` | Processing statistics |
| `error` | `Optional[str]` | Error message if failed |
| `ok` | `bool` | Property: `exit_code == 0` |
