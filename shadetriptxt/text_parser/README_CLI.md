# TextParser — CLI

Command-line interface for text parsing, normalization, extraction, and locale-aware processing.

## Quick Start

```bash
# Run as module
python -m shadetriptxt.text_parser.cli normalize "  José García-López  "

# With locale
python -m shadetriptxt.text_parser.cli extract "+34 600 123 456 email@test.com" --type all --locale es_ES

# With response file (arguments from file)
python -m shadetriptxt.text_parser.cli @params.txt
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

---

## Subcommands

### `normalize` (alias: `norm`)

Normalize text — lowercase, remove accents, collapse whitespace, strip punctuation.

```bash
python -m shadetriptxt.text_parser.cli normalize "  José  García-López  " --locale es_ES
python -m shadetriptxt.text_parser.cli norm "HELLO WORLD" --keep-case --keep-accents
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text to normalize |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--keep-case` | | `false` | Preserve original case |
| `--keep-punctuation` | | `false` | Preserve punctuation |
| `--keep-accents` | | `false` | Preserve accents |
| `--remove-parentheses` | | `false` | Remove parenthesized content |

---

### `extract` (alias: `ex`)

Extract structured content (phones, emails, URLs, etc.) from text using regex.

```bash
python -m shadetriptxt.text_parser.cli extract "Call +34 600 123 456 or email me at info@test.com" --type all
python -m shadetriptxt.text_parser.cli ex "Visit https://example.com" --type urls
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text to extract from |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--type` | `-t` | `all` | Content type to extract |

**Available extraction types:**
`all`, `phones`, `emails`, `urls`, `dates`, `ids`, `ibans`, `credit_cards`, `currency`, `hashtags`, `mentions`, `ips`, `numeric`, `percentages`, `postal_codes`

---

### `validate-id` (alias: `vid`)

Validate identity documents (DNI, NIE, CIF, European NIFs).

```bash
python -m shadetriptxt.text_parser.cli validate-id "12345678Z" --locale es_ES
python -m shadetriptxt.text_parser.cli vid "X1234567L" --doc-type NIE
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | ID string to validate |
| `--input` | `-i` | | Read ID from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--doc-type` | `-d` | | Document type (e.g. `DNI`, `NIE`, `CIF`) |

---

### `fix-encoding` (alias: `fix`)

Detect and repair mojibake / encoding errors across Latin-script languages.

```bash
python -m shadetriptxt.text_parser.cli fix-encoding "Ã¡rbol" --locale es_ES
python -m shadetriptxt.text_parser.cli fix "cafÃ©" --detect
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text with encoding issues |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--detect` | | `false` | Detect issues instead of fixing |
| `--normalize-quotes` | | `false` | Convert typographic quotes to ASCII |

---

### `phonetic` (alias: `phon`)

Phonetic reduction — reduce text to its phonetic representation (language-aware).

```bash
python -m shadetriptxt.text_parser.cli phonetic "García" --locale es_ES --strength 2
python -m shadetriptxt.text_parser.cli phon "Schmidt" --locale de_DE --strength 1
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text for phonetic reduction |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strength` | `-s` | `1` | Reduction strength: `0` (none), `1` (light), `2` (medium), `3` (aggressive) |

---

### `prepare` (alias: `prep`)

Prepare text for comparison — normalizes and optionally applies phonetic reduction.

```bash
python -m shadetriptxt.text_parser.cli prepare "José García López"
python -m shadetriptxt.text_parser.cli prep "María Fernández" --aggressive
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text to prepare |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--aggressive` | `-a` | `false` | Apply phonetic reduction |

---

### `mask`

Mask sensitive text, keeping only the first/last characters visible.

```bash
python -m shadetriptxt.text_parser.cli mask "12345678Z"
python -m shadetriptxt.text_parser.cli mask "secret@email.com" --keep-first 2 --keep-last 4 --mask-char #
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Text to mask |
| `--input` | `-i` | | Read text from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--keep-first` | | `1` | Characters to keep at start |
| `--keep-last` | | `1` | Characters to keep at end |
| `--mask-char` | | `*` | Masking character |

---

### `parse-name` (alias: `pn`)

Parse and rearrange a person name — detects surname-first format, particles, etc.

```bash
python -m shadetriptxt.text_parser.cli parse-name "García López, José"
python -m shadetriptxt.text_parser.cli pn "MARTINEZ DE LA ROSA MARIA" --locale es_ES
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Name to parse |
| `--input` | `-i` | | Read name from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |

---

### `parse-company` (alias: `pc`)

Parse a company name — separates legal form from the core name.

```bash
python -m shadetriptxt.text_parser.cli parse-company "ATRESMEDIA CORPORACION S.A."
python -m shadetriptxt.text_parser.cli pc "Google LLC" --locale en_US
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional)* | Company name to parse |
| `--input` | `-i` | | Read company name from file |
| `--output` | `-o` | | Write result to file |
| `--locale` | `-l` | `es_ES` | Locale |

---

### `locale`

Show locale information or list all supported locales.

```bash
python -m shadetriptxt.text_parser.cli locale --locale pt_BR
python -m shadetriptxt.text_parser.cli locale --list-all
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--locale` | `-l` | `es_ES` | Locale to inspect |
| `--list-all` | | `false` | List all supported locales |

---

### `batch`

Process a file line by line — applies a chosen operation to every line of an input file.

```bash
python -m shadetriptxt.text_parser.cli batch --input data.txt --operation normalize --output clean.txt
python -m shadetriptxt.text_parser.cli batch -i names.txt --operation phonetic --strength 2 -o phonetic.txt
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--input` | `-i` | *(required)* | Input file (one text per line) |
| `--output` | `-o` | | Output file |
| `--locale` | `-l` | `es_ES` | Locale |
| `--encoding` | | `utf-8` | Input file encoding |
| `--operation` | | `normalize` | Operation to apply |
| `--strength` | `-s` | `1` | Phonetic strength (for `phonetic` operation) |
| `--aggressive` | `-a` | `false` | Aggressive mode (for `prepare` operation) |

**Available operations:** `normalize`, `fix-encoding`, `phonetic`, `prepare`, `remove-articles`

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

### Normalize + Extract pipeline

```bash
# Normalize a file, then extract emails from the result
python -m shadetriptxt.text_parser.cli batch -i raw.txt --operation normalize -o clean.txt
python -m shadetriptxt.text_parser.cli extract "$(cat clean.txt)" --type emails
```

### JSON output for scripting

```bash
python -m shadetriptxt.text_parser.cli extract "Tel: +34 600 123 456" --type phones --output-format json
```

### Using a response file

Create `params.txt`:
```
normalize
"José García-López"
--locale
es_ES
--keep-accents
```

```bash
python -m shadetriptxt.text_parser.cli @params.txt
```

---

## CI Integration

Use `--ci` flag for CI/CD pipelines:

```bash
# Forces JSON output, disables colors, returns proper exit codes
python -m shadetriptxt.text_parser.cli normalize "José García" --ci
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
  text-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install shadetriptxt

      - name: Normalize input file
        run: |
          python -m shadetriptxt.text_parser.cli batch \
            -i data/raw_names.txt --operation normalize \
            --locale es_ES --ci -o data/clean_names.txt

      - name: Validate ID documents
        run: |
          python -m shadetriptxt.text_parser.cli validate-id "12345678Z" \
            --locale es_ES --ci

      - uses: actions/upload-artifact@v4
        with:
          name: clean-data
          path: data/clean_names.txt
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
                sh 'pip install shadetriptxt'
            }
        }
        stage('Normalize Data') {
            steps {
                sh '''
                    python -m shadetriptxt.text_parser.cli batch \
                        -i data/raw_names.txt --operation normalize \
                        --locale es_ES --ci \
                        -o data/clean_names.txt
                '''
                archiveArtifacts artifacts: 'data/clean_names.txt'
            }
        }
        stage('Fix Encoding') {
            steps {
                sh '''
                    python -m shadetriptxt.text_parser.cli batch \
                        -i data/legacy_export.txt --operation fix-encoding \
                        --ci -o data/fixed_encoding.txt
                '''
                archiveArtifacts artifacts: 'data/fixed_encoding.txt'
            }
        }
        stage('Extract Emails') {
            steps {
                sh '''
                    python -m shadetriptxt.text_parser.cli extract \
                        --input data/contacts.txt --type emails \
                        --ci -o data/emails.json
                '''
                archiveArtifacts artifacts: 'data/emails.json'
            }
        }
    }
    post {
        failure {
            echo 'Text processing pipeline failed — check logs'
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
  - script: pip install shadetriptxt
    displayName: Install shadetriptxt

  - script: |
      python -m shadetriptxt.text_parser.cli batch \
        -i $(Build.SourcesDirectory)/data/raw_names.txt \
        --operation normalize --locale es_ES --ci \
        -o $(Build.ArtifactStagingDirectory)/clean_names.txt
    displayName: Normalize names

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)/clean_names.txt
      artifactName: clean-data
```

---

## Programmatic API

Invoke the CLI from Python code without subprocess:

```python
from shadetriptxt.text_parser.cli import run_api, CLIResult

# Normalize text
result: CLIResult = run_api(["normalize", "  José García-López  "])
if result.ok:
    print(result.data)   # "jose garcia lopez"
    print(result.stats)  # {"normalized": 1}

# Extract emails
result = run_api(["extract", "Contact: juan@test.com", "--type", "emails"])
if result.ok:
    print(result.data)   # ["juan@test.com"]
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
