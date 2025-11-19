# Tests

This directory contains unit tests for the core module of the document upload system.

## Test Structure

```
tests/
├── __init__.py              # Tests package initialization
├── conftest.py             # Pytest configuration and shared fixtures
├── test_schema.py          # Tests for core.schema dataclasses
├── test_file_api.py        # Tests for core.file.api.DocFile
├── test_kminio.py          # Tests for MinIO client wrappers
├── test_knowledge.py       # Tests for core.manager.knowledge.Knowledge
├── test_word_spliter.py    # Tests for Word document splitter
└── README.md               # This file
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=core --cov-report=html
```

### Run Tests for Specific Module

```bash
# Run schema tests
pytest tests/test_schema.py

# Run DocFile API tests
pytest tests/test_file_api.py

# Run MinIO client tests
pytest tests/test_kminio.py

# Run Knowledge manager tests
pytest tests/test_knowledge.py

# Run WordSpliter tests
pytest tests/test_word_spliter.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Tests and Stop on First Failure

```bash
pytest -x
```

## Test Coverage

### core.schema

Tests for dataclasses:
- `TagDomain` - Tag domain with name and optional display name
- `Tag` - Document tag with serialization methods
- `DocumentMetadata` - Document metadata with file information
- `Document` - Document object with storage information

Coverage includes:
- Object creation with all required and optional fields
- Serialization to/from dictionaries
- Round-trip serialization tests
- DateTime handling

### core.file.api

Tests for `DocFile` class:
- Client initialization with MinIO backend
- Error handling for unsupported backends
- Client state management
- Bucket name configuration

Coverage includes:
- Initialization with various parameters
- Error cases (unsupported backend, uninitialized client)
- Client getter/setter behavior

### core.file.client.kminio

Tests for async MinIO client wrappers:
- `AsyncMinioClient` - Asynchronous MinIO client
- `KMinIOBucket` - Default bucket client

Coverage includes:
- All async methods (upload, download, list, etc.)
- Thread pool executor usage
- Context manager support
- Default bucket handling

### core.manager.knowledge

Tests for `Knowledge` class:
- Knowledge base initialization
- File listing and structure
- Upload/download operations
- Async operations

Coverage includes:
- Directory scanning and file listing
- Structure generation
- Async file operations with mocked clients
- Error handling for missing files/directories

### core.manager.spliter.word

Tests for `WordSpliter` class:
- Document parsing and splitting
- Table processing
- Image extraction
- Markdown generation

**Note:** WordSpliter tests require additional dependencies:
- `python-docx` - For Word document parsing
- `Pillow` - For image processing
- `tiktoken` - For token counting

Due to complexity and external dependencies, WordSpliter tests include:
1. Mock-based unit tests for individual methods
2. Integration test examples (marked as skipped)
3. Documentation of what tests should exist

## Fixtures

The `conftest.py` file provides several shared fixtures:

- `temp_dir` - Temporary directory for test files
- `temp_file` - Temporary file for testing
- `mock_async_minio_client` - Mock async MinIO client
- `sample_knowledge_base` - Sample knowledge base structure
- `sample_document_metadata` - Sample document metadata
- `sample_document` - Sample document object
- `mock_docfile_client` - Mock DocFile client

## Test Markers

Tests use the following pytest markers:

- `@pytest.mark.asyncio` - Asynchronous tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests

## Best Practices

### Writing Tests

1. **Test naming**: Use descriptive test names that explain what is being tested
2. **Test structure**: Use Arrange-Act-Assert pattern
3. **Fixtures**: Use fixtures for common setup/teardown
4. **Mocks**: Mock external dependencies (databases, APIs, filesystems)
5. **Coverage**: Aim for high code coverage, especially for edge cases

### Test Organization

1. **One test file per module**: Each module should have a corresponding test file
2. **One test class per class**: Group tests by the class being tested
3. **Descriptive test names**: Use `test_<method>_<scenario>` naming

### Async Testing

Tests for async code should:
1. Use `@pytest.mark.asyncio` decorator
2. Use `pytest-asyncio` for auto-detection
3. Mock async methods with `AsyncMock`

## Continuous Integration

To run tests in CI/CD:

```bash
# Install dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
pytest --cov=core --cov-report=xml

# Fail if coverage is below threshold
pytest --cov=core --cov-fail-under=80
```

## Troubleshooting

### Import Errors

If you encounter import errors:
```bash
# Ensure you're in the project root directory
cd /data/home/solgeo/projects/doc-upload

# Install package in development mode
pip install -e .
```

### Async Test Failures

If async tests fail:
1. Ensure `pytest-asyncio` is installed
2. Check that async methods are properly mocked
3. Use `await` in async test functions

### WordSpliter Tests

If WordSpliter tests fail:
1. Install optional dependencies: `pip install python-docx Pillow tiktoken`
2. Or skip WordSpliter tests if dependencies are not available
