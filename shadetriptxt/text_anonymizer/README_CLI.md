# TextAnonymizer — CLI

Command-line interface for PII detection & anonymization (7 strategies, 15 PII types, 12 locales).

## Quick Start

```bash
# Anonymize text with default strategy (redact)
python -m shadetriptxt.text_anonymizer.cli anonymize "DNI: 12345678Z, email: juan@test.com"

# Detect PII without anonymizing
python -m shadetriptxt.text_anonymizer.cli detect "Call 612345678 or email info@test.com"

# Anonymize a text file
python -m shadetriptxt.text_anonymizer.cli anonymize-file input.txt -o output.txt --strategy mask

# Anonymize CSV columns
python -m shadetriptxt.text_anonymizer.cli anonymize-csv data.csv --columns name,email,phone -o clean.csv

# With response file (arguments from file)
python -m shadetriptxt.text_anonymizer.cli @params.txt
```

---

## Global Options

Every subcommand inherits these flags:

| Flag | Short | Description |
|------|-------|-------------|
| `--quiet` | `-q` | Suppress non-essential output |
| `--verbose` | `-v` | Increase verbosity (-v INFO, -vv DEBUG) |
| `--output-format` | | Output format: `summary` (default), `json`, `csv`, `table`, `quiet` |
| `--no-color` | | Disable ANSI colors |
| `--ci` | | CI mode: JSON output, no colors, exit codes |
| `--dry-run` | | Simulate only |
| `--log-file` | | Write logs to file |
| `--config-file` | | Load settings from JSON config file |

---

## Subcommands

### `anonymize` (alias: `anon`)

Anonymize text provided as argument or piped from stdin.

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize "DNI: 12345678Z, email: juan@test.com"
echo "sensitive text" | python -m shadetriptxt.text_anonymizer.cli anonymize
python -m shadetriptxt.text_anonymizer.cli anon "Call 612345678" --strategy mask --locale es_ES
python -m shadetriptxt.text_anonymizer.cli anon "My SSN is 123-45-6789" --locale en_US -o output.txt
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional, optional)* | Text to anonymize (or pipe from stdin) |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strategy` | `-s` | `redact` | Anonymization strategy |
| `--seed` | | | Random seed for reproducible output |
| `--output` | `-o` | | Write result to file |
| `--use-spacy` | | `false` | Enable spaCy NER detection |
| `--use-nltk` | | `false` | Enable NLTK NER detection |
| `--min-confidence` | | `0.0` | Minimum confidence threshold (0.0–1.0) |
| `--pii-types` | | | Comma-separated PII types to detect (e.g. `NAME,EMAIL,PHONE`) |

---

### `detect` (alias: `scan`)

Detect PII entities in text without anonymizing.

```bash
python -m shadetriptxt.text_anonymizer.cli detect "DNI: 12345678Z, tel: 612345678"
python -m shadetriptxt.text_anonymizer.cli detect "email: bob@example.com" --output-format json
python -m shadetriptxt.text_anonymizer.cli scan "My SSN is 123-45-6789" --locale en_US
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `text` | | *(positional, optional)* | Text to scan (or pipe from stdin) |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strategy` | `-s` | `redact` | Strategy (used for context) |
| `--seed` | | | Random seed |
| `--output` | `-o` | | Write result to file |
| `--use-spacy` | | `false` | Enable spaCy NER detection |
| `--use-nltk` | | `false` | Enable NLTK NER detection |
| `--min-confidence` | | `0.0` | Minimum confidence threshold |
| `--pii-types` | | | Comma-separated PII types to filter |

---

### `anonymize-file` (alias: `file`)

Anonymize a text file line by line.

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize-file input.txt -o output.txt
python -m shadetriptxt.text_anonymizer.cli file log.txt --strategy mask -o log_clean.txt
python -m shadetriptxt.text_anonymizer.cli file notes.txt --use-spacy --locale en_US
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `input` | | *(positional, required)* | Input text file path |
| `--output` | `-o` | | Output file path |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strategy` | `-s` | `redact` | Anonymization strategy |
| `--seed` | | | Random seed |
| `--use-spacy` | | `false` | Enable spaCy NER detection |
| `--use-nltk` | | `false` | Enable NLTK NER detection |
| `--min-confidence` | | `0.0` | Minimum confidence threshold |

---

### `anonymize-csv` (alias: `csv`)

Anonymize specific columns in a CSV file.

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize-csv data.csv --columns name,email,phone -o clean.csv
python -m shadetriptxt.text_anonymizer.cli csv clients.csv -c name,email --strategy mask -o masked.csv
python -m shadetriptxt.text_anonymizer.cli csv data.tsv --delimiter "\t" --columns notes -o clean.tsv
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `input` | | *(positional, required)* | Input CSV file path |
| `--output` | `-o` | | Output CSV file path |
| `--columns` | `-c` | | Comma-separated columns to anonymize (default: auto-detect) |
| `--delimiter` | `-d` | `,` | CSV delimiter |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strategy` | `-s` | `redact` | Anonymization strategy |
| `--seed` | | | Random seed |

---

### `anonymize-dict` (alias: `dict`)

Anonymize a JSON record (object or array) from argument or stdin.

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize-dict '{"name": "Juan", "email": "j@test.com"}'
echo '[{"name": "Ana"}, {"name": "Luis"}]' | python -m shadetriptxt.text_anonymizer.cli dict
python -m shadetriptxt.text_anonymizer.cli dict '{"phone": "+34612345678"}' --fields phone --strategy mask
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `json_input` | | *(positional, optional)* | JSON string (or pipe from stdin) |
| `--output` | `-o` | | Write result to file |
| `--fields` | `-f` | | Comma-separated fields to anonymize (default: auto-detect) |
| `--locale` | `-l` | `es_ES` | Locale |
| `--strategy` | `-s` | `redact` | Anonymization strategy |
| `--seed` | | | Random seed |

---

### `locales`

List all supported locales with details.

```bash
python -m shadetriptxt.text_anonymizer.cli locales
```

---

### `strategies`

List all available anonymization strategies with descriptions.

```bash
python -m shadetriptxt.text_anonymizer.cli strategies
```

---

### `pii-types` (alias: `types`)

List all detectable PII types.

```bash
python -m shadetriptxt.text_anonymizer.cli pii-types
```

---

## Anonymization Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| `mask` | Replace characters with `*` | `J*** D**`, `****@****.***` |
| `replace` | Replace with realistic fake data | `María López`, `fake@email.com` |
| `hash` | Replace with truncated SHA-256 hash | `a1b2c3d4` |
| `redact` | Replace with `[TYPE]` label | `[NAME]`, `[EMAIL]` |
| `generalize` | Reduce precision | age 34 → `30-40` |
| `pseudonymize` | Consistent replacement (same input → same output) | `Person_1` |
| `suppress` | Remove completely (empty string) | *(empty)* |

---

## Detectable PII Types

| PII Type | Examples |
|----------|---------|
| `NAME` | Juan García, John Smith |
| `EMAIL` | user@example.com |
| `PHONE` | +34 612 345 678, 555-1234 |
| `ADDRESS` | Calle Mayor 10, 28001 Madrid |
| `ID_DOCUMENT` | DNI 12345678Z, SSN 123-45-6789 |
| `CREDIT_CARD` | 4111 1111 1111 1111 |
| `IBAN` | ES91 2100 0418 4502 0005 1332 |
| `IP_ADDRESS` | 192.168.1.1 |
| `DATE` | 15/03/1990 |
| `URL` | https://example.com |
| `ORGANIZATION` | Acme Corp |
| `LOCATION` | Madrid, Spain |
| `NUMBER` | 12345678 |
| `CURRENCY` | €1,500.00 |
| `CUSTOM` | User-defined patterns |

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

### Anonymize customer data file

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize-file customer_notes.txt \
    --strategy mask --locale es_ES -o customer_notes_clean.txt
```

### Clean a CSV before sharing

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize-csv clients.csv \
    --columns name,email,phone,address \
    --strategy replace --locale es_ES \
    -o clients_anonymized.csv
```

### Detect PII in a document (JSON output for scripting)

```bash
python -m shadetriptxt.text_anonymizer.cli detect \
    "Contact Juan García at juan@corp.com or call +34 612 345 678" \
    --output-format json
```

### Pseudonymize with reproducible results

```bash
python -m shadetriptxt.text_anonymizer.cli anonymize \
    "Juan García emailed María López" \
    --strategy pseudonymize --seed 42
```

### Using a response file

Create `params.txt`:
```
anonymize-csv
clients.csv
--columns
name,email,phone
--strategy
mask
--locale
es_ES
-o
clients_clean.csv
```

```bash
python -m shadetriptxt.text_anonymizer.cli @params.txt
```

---

## CI Integration

Use `--ci` flag for CI/CD pipelines:

```bash
# Forces JSON output, disables colors, returns proper exit codes
python -m shadetriptxt.text_anonymizer.cli anonymize "DNI: 12345678Z" --ci
echo $?  # 0 = success, 1 = user error, 2 = unexpected error
```

### Exit Codes

| Code | Meaning |
|------|---------|
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
  anonymize-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install shadetriptxt

      - name: Detect PII in test data
        run: |
          python -m shadetriptxt.text_anonymizer.cli detect \
            "$(cat test_data.txt)" \
            --locale es_ES --ci

      - name: Anonymize CSV dataset
        run: |
          python -m shadetriptxt.text_anonymizer.cli anonymize-csv \
            raw_data.csv --columns name,email,phone \
            --strategy mask --locale es_ES --ci \
            -o anonymized_data.csv

      - uses: actions/upload-artifact@v4
        with:
          name: anonymized-data
          path: anonymized_data.csv
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
        stage('Anonymize Customer Data') {
            steps {
                sh '''
                    python -m shadetriptxt.text_anonymizer.cli anonymize-csv \
                        customer_data.csv \
                        --columns name,email,phone,address \
                        --strategy replace --locale es_ES --ci \
                        -o customer_data_clean.csv
                '''
                archiveArtifacts artifacts: 'customer_data_clean.csv'
            }
        }
        stage('Detect PII in Logs') {
            steps {
                sh '''
                    python -m shadetriptxt.text_anonymizer.cli detect \
                        "$(cat app.log)" \
                        --locale es_ES --ci \
                        -o pii_report.json
                '''
                archiveArtifacts artifacts: 'pii_report.json'
            }
        }
    }
    post {
        failure {
            echo 'Anonymization pipeline failed — check logs'
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
      python -m shadetriptxt.text_anonymizer.cli anonymize-csv \
        raw_data.csv --columns name,email,phone \
        --strategy mask --locale es_ES --ci \
        -o $(Build.ArtifactStagingDirectory)/anonymized.csv
    displayName: Anonymize dataset

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)/anonymized.csv
      artifactName: anonymized-data
```

---

## Programmatic API

Invoke the CLI from Python code without subprocess:

```python
from shadetriptxt.text_anonymizer.cli import run_api, CLIResult

# Anonymize text
result: CLIResult = run_api(["anonymize", "DNI: 12345678Z, email: juan@test.com", "--locale", "es_ES"])
if result.ok:
    print(result.data["anonymized"])
    print(result.stats)  # {"texts_anonymized": 1, "entities_found": 2}

# Detect PII
result = run_api(["detect", "Call +34 612 345 678", "--locale", "es_ES"])
if result.ok:
    for entity in result.data:
        print(f"{entity['pii_type']}: {entity['text']}")
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
