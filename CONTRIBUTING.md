# Contributing

1. Fork the repository and create a feature branch.
2. Install the development dependencies: `pip install -e ".[dev]"`.
3. Add or update tests for behaviour changes.
4. Run `pytest` and `ruff check app tests scripts` before opening a pull request.
5. Never commit `.env`, credentials, database files, GeoIP databases, or Terraform state.
