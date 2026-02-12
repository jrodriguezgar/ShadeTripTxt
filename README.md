# shadetriptxt

> A Python library for text validation, data cleaning, fuzzy matching, and fake data generation.

![Version](https://img.shields.io/badge/version-0.0.1-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Table of Contents

- [Installation](#installation)
- [Modules](#modules)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation

### Prerequisites

- Python >= 3.10

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/DatamanEdge/shadetriptxt.git
   cd shadetriptxt
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\Activate
   # macOS / Linux
   source .venv/bin/activate
   ```
3. Install the package:
   ```bash
   pip install .
   ```
   Or install with anonymizer features:
   ```bash
   pip install ".[anonymizer]"
   ```

### Dependencies

| Package | Min Version | Purpose |
|---------|-------------|---------|
| `email-validator` | 2.0.0 | Email validation |
| `flashtext` | 2.7 | Keyword processing |
| `faker` | 20.0.0 | Fake data generation |

## Modules

| Module | Description |
|--------|-------------|
| `text_matcher` | Fuzzy text comparison, best-match finding, duplicate detection. See [TextMatcher docs](shadetriptxt/text_matcher/README.md) |
| `text_parser` | Text normalization, name parsing, NIF/DNI validation, structured content extraction. See [TextParser docs](shadetriptxt/text_parser/README.md) |
| `text_dummy` | Locale-aware fake data generation (60+ data types, 12 locales, custom types). See [TextDummy docs](shadetriptxt/text_dummy/README.md) |
| `text_anonymizer` | PII detection & anonymization with 7 strategies. See [TextAnonymizer docs](shadetriptxt/text_anonymizer/README_TextAnonymizer.md) |

## Usage

### Locale-Aware Parsing

```python
from shadetriptxt.text_parser.text_parser import TextParser

parser = TextParser("es_ES")
parser.normalize("Ma. P. García")      # "maria pilar garcia"
parser.extract_ids("DNI 12345678Z")    # ['12345678Z']
```

### Text Matching

```python
from shadetriptxt.text_matcher.text_matcher import TextMatcher

matcher = TextMatcher()
score = matcher.compare("John Smith", "Jon Smyth")
```

### ID Validation (Spanish / US / Brazil)

```python
from shadetriptxt.text_parser.idcard_parser import nif_parse, is_valid_cpf, is_valid_ssn

# Spanish DNI
nif_parse("12345678Z")    # "12345678Z"

# Brazil CPF
is_valid_cpf("123.456.789-09")  # True

# US SSN
is_valid_ssn("123-45-6789")     # True
```

### Fake Data Generation

```python
from shadetriptxt.text_dummy.text_dummy import TextDummy

# Spanish data (default)
gen = TextDummy("es_ES")
gen.name()              # "María García López"
gen.id_document()       # "45678123P"
gen.iban()              # "ES9121000418450200051332"
gen.product_name()      # "Premium Keyboard"

# US data
gen_us = TextDummy("en_US")
gen_us.id_document()    # "456-78-1234"
gen_us.credit_card_number()

# Batch generation
gen.generate_batch("email", count=5)

# Custom types
gen.register_custom_type("priority", ["Low", "Medium", "High", "Critical"])
gen.generate_batch("priority", count=10)
```

### Text Extraction

```python
from shadetriptxt.text_parser.text_extract import TextExtractor

extractor = TextExtractor()
extractor.extract_emails("Contact us at info@example.com or sales@example.com")
extractor.extract_phones("Call +34 612 345 678")
```

## Configuration

shadetriptxt works out of the box with no configuration files required. Module behavior is controlled through constructor parameters and method arguments:

| Parameter | Module | Description | Default |
|-----------|--------|-------------|---------|
| `locale` | `text_dummy` | Language/country code for fake data | `es_ES` |
| `algorithm` | `text_matcher` | Similarity algorithm to use | Auto-selected |

## Testing

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

MIT © 2025 DatamanEdge. See [LICENSE](LICENSE).

## Contact

- **Author**: [DatamanEdge](https://github.com/DatamanEdge)
- **Issues**: [GitHub Issues](https://github.com/DatamanEdge/shadetriptxt/issues)
