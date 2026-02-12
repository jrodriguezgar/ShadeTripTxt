# TextDummy — CLI

Command-line interface for locale-aware fake data generation (65+ data types, 12 locales).

## Quick Start

```bash
# Generate 10 Spanish names
python -m shadetriptxt.text_dummy.cli generate name --locale es_ES

# Generate 50 rows of contacts as CSV
python -m shadetriptxt.text_dummy.cli batch "name,email,phone,city" --count 50 -o contacts.csv

# Generate 5 complete profiles
python -m shadetriptxt.text_dummy.cli profile --count 5

# With response file (arguments from file)
python -m shadetriptxt.text_dummy.cli @params.txt
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

### `generate` (alias: `gen`)

Generate fake data of a single type.

```bash
python -m shadetriptxt.text_dummy.cli generate email --count 5 --locale en_US
python -m shadetriptxt.text_dummy.cli gen phone --count 20 --locale pt_BR -o phones.txt
python -m shadetriptxt.text_dummy.cli gen address --count 3
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `data_type` | | *(positional, required)* | Type of data to generate (see [Available Types](#available-types)) |
| `--count` | `-n` | `10` | Number of items |
| `--locale` | `-l` | `es_ES` | Locale |
| `--output` | `-o` | | Write result to file |

---

### `batch`

Generate multiple columns of fake data — output as CSV or JSON.

```bash
python -m shadetriptxt.text_dummy.cli batch "name,email,phone,city" --count 50 -o contacts.csv
python -m shadetriptxt.text_dummy.cli batch "name,dni,email" --count 100 --output-format json -o data.json
python -m shadetriptxt.text_dummy.cli batch "first_name,last_name,company" --delimiter ";"
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `types` | | *(positional, required)* | Comma-separated data types (e.g. `name,email,phone`) |
| `--count` | `-n` | `10` | Number of rows |
| `--locale` | `-l` | `es_ES` | Locale |
| `--output` | `-o` | | Write result to file |
| `--delimiter` | | `,` | CSV delimiter |

---

### `profile` (alias: `prof`)

Generate complete fake personal profiles with name, email, phone, address, etc.

```bash
python -m shadetriptxt.text_dummy.cli profile --count 5 --locale pt_BR
python -m shadetriptxt.text_dummy.cli prof --count 1 --output-format json
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `1` | Number of profiles |
| `--locale` | `-l` | `es_ES` | Locale |
| `--output` | `-o` | | Write result to file |

---

### `product` (alias: `prod`)

Generate complete fake product records.

```bash
python -m shadetriptxt.text_dummy.cli product --count 10 --locale de_DE
python -m shadetriptxt.text_dummy.cli prod --count 3 --output-format json -o products.json
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `1` | Number of products |
| `--locale` | `-l` | `es_ES` | Locale |
| `--output` | `-o` | | Write result to file |

---

### `id-doc` (alias: `id`)

Generate fake identity documents (DNI, NIE, RFC, CPF, CNPJ, etc.).

```bash
python -m shadetriptxt.text_dummy.cli id-doc --locale es_ES --doc-type NIE --count 10
python -m shadetriptxt.text_dummy.cli id --locale pt_BR --count 5
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `10` | Number of documents |
| `--locale` | `-l` | `es_ES` | Locale |
| `--doc-type` | `-d` | | Document type (e.g. `NIE`, `RFC`, `CNPJ`) |
| `--output` | `-o` | | Write result to file |

---

### `number` (alias: `num`)

Generate random numbers — integers or floats with configurable ranges.

```bash
python -m shadetriptxt.text_dummy.cli number --number-type float --min-val 0 --max-val 1000 --count 20
python -m shadetriptxt.text_dummy.cli num --digits 4 --count 10
python -m shadetriptxt.text_dummy.cli num --number-type float --decimals 4 --currency
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `10` | Number of values |
| `--locale` | `-l` | `es_ES` | Locale |
| `--number-type` | | `integer` | `integer` or `float` |
| `--digits` | | `6` | Significant digits |
| `--decimals` | | `2` | Decimal places (for float) |
| `--min-val` | | | Minimum value |
| `--max-val` | | | Maximum value |
| `--currency` | | `false` | Format with currency symbol |
| `--output` | `-o` | | Write result to file |

---

### `date`

Generate random dates within a range.

```bash
python -m shadetriptxt.text_dummy.cli date --start 2020-01-01 --end 2025-12-31 --count 10
python -m shadetriptxt.text_dummy.cli date --pattern "%d/%m/%Y" --count 5
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `10` | Number of dates |
| `--locale` | `-l` | `es_ES` | Locale |
| `--start` | | `1970-01-01` | Start date (`YYYY-MM-DD`) |
| `--end` | | today | End date (`YYYY-MM-DD`) |
| `--pattern` | | | Output date format (strftime) |
| `--output` | `-o` | | Write result to file |

---

### `key`

Generate unique keys — alphanumeric, hex, UUID, etc.

```bash
python -m shadetriptxt.text_dummy.cli key --key-type hex --length 12 --separator - --segment-length 4 --count 5
python -m shadetriptxt.text_dummy.cli key --key-type uuid --count 10
python -m shadetriptxt.text_dummy.cli key --prefix-str "USR-" --length 6
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--count` | `-n` | `10` | Number of keys |
| `--locale` | `-l` | `es_ES` | Locale |
| `--length` | | `8` | Key length |
| `--key-type` | | `alphanumeric` | Key type: `alphanumeric`, `alpha`, `numeric`, `hex`, `uuid` |
| `--prefix-str` | | `""` | Key prefix |
| `--separator` | | `""` | Segment separator |
| `--segment-length` | | `0` | Characters per segment (0 = no segmentation) |
| `--output` | `-o` | | Write result to file |

---

### `types`

List all available data types for the `generate` and `batch` subcommands.

```bash
python -m shadetriptxt.text_dummy.cli types
```

---

### `locale`

Show locale information or list all supported locales.

```bash
python -m shadetriptxt.text_dummy.cli locale --locale pt_BR
python -m shadetriptxt.text_dummy.cli locale --list-all
```

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--locale` | `-l` | `es_ES` | Locale to inspect |
| `--list-all` | | `false` | List all supported locales |

---

## Available Types

The `generate` and `batch` commands accept any of the 65+ types listed by `types`. Common categories:

| Category | Types |
|----------|-------|
| **Identity** | `name`, `first_name`, `last_name`, `prefix`, `suffix`, `dni`, `nie`, `nif`, `ssn` |
| **Contact** | `email`, `phone`, `phone_number`, `safe_email`, `free_email`, `company_email` |
| **Address** | `address`, `street_address`, `city`, `state`, `country`, `postcode`, `building_number` |
| **Internet** | `url`, `domain_name`, `ipv4`, `ipv6`, `mac_address`, `user_agent`, `user_name` |
| **Financial** | `iban`, `credit_card_number`, `credit_card_provider`, `cryptocurrency_code` |
| **Text** | `text`, `sentence`, `paragraph`, `word`, `catch_phrase`, `bs` |
| **Date/Time** | `date`, `date_of_birth`, `time`, `date_time`, `year`, `month`, `day_of_week` |
| **Misc** | `uuid4`, `color`, `hex_color`, `license_plate`, `job`, `company`, `boolean` |

Run `python -m shadetriptxt.text_dummy.cli types` for the complete list.

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

### Generate test dataset

```bash
python -m shadetriptxt.text_dummy.cli batch "first_name,last_name,email,phone,city" --count 1000 --locale es_ES -o dataset.csv
```

### Generate keys with segments

```bash
python -m shadetriptxt.text_dummy.cli key --key-type hex --length 16 --separator - --segment-length 4 --count 5
# Output: a1b2-c3d4-e5f6-7890
```

### JSON output for scripting

```bash
python -m shadetriptxt.text_dummy.cli profile --count 3 --output-format json -o profiles.json
```

### Using a response file

Create `params.txt`:
```
batch
name,email,phone
--count
100
--locale
en_US
-o
data.csv
```

```bash
python -m shadetriptxt.text_dummy.cli @params.txt
```

---

## CI Integration

Use `--ci` flag for CI/CD pipelines:

```bash
# Forces JSON output, disables colors, returns proper exit codes
python -m shadetriptxt.text_dummy.cli generate email --count 5 --ci
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
  generate-test-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install shadetriptxt

      - name: Generate test dataset
        run: |
          python -m shadetriptxt.text_dummy.cli batch \
            "name,email,phone,city" --count 500 \
            --locale es_ES --ci -o test_data.csv

      - name: Generate fake profiles
        run: |
          python -m shadetriptxt.text_dummy.cli profile \
            --count 50 --locale en_US --ci -o profiles.json

      - uses: actions/upload-artifact@v4
        with:
          name: test-data
          path: |
            test_data.csv
            profiles.json
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
        stage('Generate Test Data') {
            steps {
                sh '''
                    python -m shadetriptxt.text_dummy.cli batch \
                        "name,email,phone,dni,city" --count 1000 \
                        --locale es_ES --ci \
                        -o test_data.csv
                '''
                archiveArtifacts artifacts: 'test_data.csv'
            }
        }
        stage('Generate ID Documents') {
            steps {
                sh '''
                    python -m shadetriptxt.text_dummy.cli id-doc \
                        --locale es_ES --doc-type NIE \
                        --count 100 --ci \
                        -o fake_ids.json
                '''
                archiveArtifacts artifacts: 'fake_ids.json'
            }
        }
        stage('Generate Profiles') {
            steps {
                sh '''
                    python -m shadetriptxt.text_dummy.cli profile \
                        --count 50 --locale pt_BR --ci \
                        -o profiles.json
                '''
                archiveArtifacts artifacts: 'profiles.json'
            }
        }
    }
    post {
        failure {
            echo 'Test data generation failed — check logs'
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
      python -m shadetriptxt.text_dummy.cli batch \
        "name,email,phone" --count 500 \
        --locale es_ES --ci \
        -o $(Build.ArtifactStagingDirectory)/test_data.csv
    displayName: Generate test dataset

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)/test_data.csv
      artifactName: test-data
```

---

## Programmatic API

Invoke the CLI from Python code without subprocess:

```python
from shadetriptxt.text_dummy.cli import run_api, CLIResult

# Generate emails
result: CLIResult = run_api(["generate", "email", "--count", "10", "--locale", "en_US"])
if result.ok:
    print(result.data)   # List of 10 fake emails
    print(result.stats)  # {"generated": 10}

# Generate profiles
result = run_api(["profile", "--count", "3"])
if result.ok:
    for profile in result.data:
        print(profile["name"])
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
