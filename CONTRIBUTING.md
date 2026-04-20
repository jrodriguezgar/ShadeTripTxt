# Contributing to ShadeTripTxt

Thank you for your interest in contributing to ShadeTripTxt!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```
   git clone https://github.com/<your-user>/ShadeTripTxt.git
   cd ShadeTripTxt
   ```
3. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # Linux/macOS
   pip install -e ".[anonymizer]"
   pip install pytest ruff pre-commit
   pre-commit install
   ```

## Development Workflow

1. Create a feature branch:
   ```
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run the test suite:
   ```
   python -m pytest --tb=short -q
   ```
4. Run the linter:
   ```
   ruff check shadetriptxt/ tests/
   ruff format shadetriptxt/ tests/
   ```
5. Commit and push:
   ```
   git add .
   git commit -m "feat: description of your change"
   git push origin feature/your-feature-name
   ```
6. Open a Pull Request

## Code Style

- Follow PEP 8 (enforced by ruff)
- Line length: 150 characters
- Type hints for public API functions
- Docstrings for public classes and methods

## Tests

- All new public functions must have tests in 	ests/
- Tests use pytest — run with python -m pytest
- Maintain existing test coverage (currently 367+ tests)

## Reporting Issues

Use [GitHub Issues](https://github.com/jrodriguezgar/ShadeTripTxt/issues) with:
- Clear title and description
- Steps to reproduce (if bug)
- Python version and OS
