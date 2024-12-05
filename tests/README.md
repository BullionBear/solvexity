# Tests Directory

This directory contains all the unit tests and integration tests for the project. The tests are organized by module, ensuring a clear and maintainable structure.

## Running Tests

We use `pytest` as the testing framework. Below are some common commands to run tests:

### 1. Run All Tests in the Project
To execute all tests in the `tests/` directory:
```bash
pytest
```

### 2. Run Tests by Module
To run all tests within a specific module (e.g., `trader`):
```bash
pytest tests/trader/
```

### 3. Run Tests by File
To run tests from a specific file (e.g., `test_spot_trade.py`):
```bash
pytest tests/trader/context/test_spot_trade.py
```

### 4. Run a Specific Test Function
To run a specific test function within a file (e.g., `test_balance_retrieval` in `test_spot_trade.py`):
```bash
pytest tests/trader/context/test_spot_trade.py::test_balance_retrieval
```

### 5. Run Tests with Logging Output
To enable logging output (e.g., `INFO` or `DEBUG` level) during test runs:
```bash
pytest --log-cli-level=INFO
```

Example:
```bash
pytest --log-cli-level=DEBUG tests/trader/context/test_spot_trade.py
```

### 6. Run Tests with Detailed Output
For verbose output to see more details about the tests being executed:
```bash
pytest -v
```

### 7. Run Tests with Coverage
To measure test coverage and generate a report:
```bash
pytest --cov=solvexity --cov-report=term-missing
```

### 8. Run Tests and Generate an HTML Coverage Report
To generate an HTML report for coverage:
```bash
pytest --cov=solvexity --cov-report=html
```
The report will be saved in the `htmlcov/` directory.

## Tips for Writing Tests
- Place test files in the appropriate module directory.
- Test file names should start with `test_` (e.g., `test_spot_trade.py`).
- Use fixtures for reusable test setup code.
- Follow naming conventions for test functions: `test_<functionality>`.

---

Happy testing! 🚀