# Contributing to Kuralit

Thank you for your interest in contributing to Kuralit! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to hello@kuralit.com.

## How to Contribute

There are many ways to contribute to Kuralit:

- **Bug Reports**: Report bugs and issues
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit pull requests with bug fixes or new features
- **Documentation**: Improve documentation, examples, or tutorials
- **Testing**: Write tests or help improve test coverage
- **Examples**: Create example applications or use cases

## Getting Started

### Prerequisites

- Python 3.10+ (for Python SDK contributions)
- Dart SDK 2.17+ and Flutter 3.0+ (for Flutter SDK contributions)
- Git
- Basic understanding of the project structure

### Development Setup

#### Python SDK

1. **Clone the repository**
   ```bash
   git clone https://github.com/kuralit/kuralit.git
   cd kuralit/python-sdk
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install development dependencies
   pip install -e ".[all]"
   
   # Or install specific feature groups
   pip install -e ".[gemini,websocket,stt,vad,rest]"
   ```

4. **Install development tools**
   ```bash
   pip install pytest black mypy ruff
   ```

5. **Run tests** (if available)
   ```bash
   pytest
   ```

#### Flutter SDK

1. **Navigate to Flutter SDK directory**
   ```bash
   cd flutter-sdk
   ```

2. **Get dependencies**
   ```bash
   flutter pub get
   ```

3. **Run example apps**
   ```bash
   cd example/basic
   flutter run
   ```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use descriptive branch names:
- `feature/add-new-plugin`
- `fix/websocket-reconnection-issue`
- `docs/update-installation-guide`

### 2. Make Changes

- Write clear, readable code
- Follow the existing code style
- Add comments for complex logic
- Update documentation as needed
- Add tests for new features

### 3. Code Style

#### Python

- Follow PEP 8 style guide
- Use type hints for all functions
- Maximum line length: 100 characters
- Use `black` for formatting:
  ```bash
  black kuralit/
  ```
- Use `ruff` for linting:
  ```bash
  ruff check kuralit/
  ```

#### Dart/Flutter

- Follow the [Effective Dart](https://dart.dev/guides/language/effective-dart) style guide
- Use `dart format` for formatting:
  ```bash
  dart format lib/
  ```
- Follow Flutter conventions for widget structure

### 4. Commit Messages

Write clear, descriptive commit messages:

```
feat: Add support for OpenAI LLM plugin

- Implement OpenAI plugin class
- Add configuration options
- Update documentation
- Add example usage

Fixes #123
```

Commit message format:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### 5. Testing

- Write tests for new features
- Ensure existing tests pass
- Test edge cases and error handling
- For Python SDK, use pytest
- For Flutter SDK, use Flutter's testing framework

### 6. Documentation

- Update relevant documentation files
- Add docstrings to new functions/classes
- Update examples if API changes
- Add comments for complex logic

## Pull Request Process

### Before Submitting

1. **Ensure your code works**
   - Test your changes thoroughly
   - Run all existing tests
   - Test on different platforms if applicable

2. **Update documentation**
   - Update README if needed
   - Update API documentation
   - Add/update examples

3. **Check code style**
   - Run formatters and linters
   - Fix any style issues

4. **Write a clear PR description**
   - Describe what changes you made
   - Explain why you made them
   - Reference related issues
   - Include screenshots if UI changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

1. **Automated Checks**: CI/CD will run tests and checks
2. **Code Review**: Maintainers will review your PR
3. **Feedback**: Address any feedback or requested changes
4. **Approval**: Once approved, your PR will be merged

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python/Flutter versions, OS, etc.
- **Error Messages**: Full error messages and stack traces
- **Screenshots**: If applicable

### Feature Requests

When requesting features, please include:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions you've considered
- **Additional Context**: Any other relevant information

## Development Guidelines

### Python SDK

- **Architecture**: Follow the plugin architecture pattern
- **Type Safety**: Use type hints everywhere
- **Error Handling**: Use custom exceptions from `kuralit.exceptions`
- **Logging**: Use the logging utilities from `kuralit.utils.log`
- **Testing**: Write unit tests for new features

### Flutter SDK

- **Architecture**: Follow the event-driven architecture
- **State Management**: Use appropriate state management patterns
- **Error Handling**: Handle errors gracefully with proper error events
- **Testing**: Write widget and unit tests

### General Guidelines

- **Keep it simple**: Prefer simple solutions over complex ones
- **Documentation**: Document public APIs thoroughly
- **Backwards Compatibility**: Consider backwards compatibility
- **Performance**: Consider performance implications
- **Security**: Follow security best practices

## Project Structure

```
kuralit/
├── python-sdk/          # Python SDK
│   ├── kuralit/         # Main package
│   ├── examples/        # Example applications
│   └── tests/           # Test files
├── flutter-sdk/         # Flutter SDK
│   ├── lib/             # Source code
│   └── example/         # Example applications
└── docs/                # Documentation
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Issues**: Open a GitHub Issue
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Contact hello@kuralit.com for other inquiries

## License

By contributing, you agree that your contributions will be licensed under the same Non-Commercial License that covers the project.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (if we create one)
- Release notes for significant contributions
- Project documentation

Thank you for contributing to Kuralit!

