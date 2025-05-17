# Contributing to Omniverse USD MCP Server

Thank you for your interest in contributing to the Omniverse USD MCP Server project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're committed to providing a welcoming and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. A clear and descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Screenshots if applicable
5. Any relevant system information (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

1. A clear description of the enhancement
2. The motivation for the change
3. How it would benefit users
4. Any implementation ideas you have

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Write tests if applicable
5. Run existing tests to ensure nothing breaks
6. Commit your changes (`git commit -m 'Add my feature'`)
7. Push to your branch (`git push origin feature/my-feature`)
8. Create a Pull Request

## Development Setup

To set up a development environment:

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/Omniverse_USD_MCPServer_byJPH2.git
cd Omniverse_USD_MCPServer_byJPH2

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Include docstrings for all functions, classes, and modules
- Keep functions focused and modular
- Comment complex sections of code

## Testing

- Add tests for new functionality
- Ensure all tests pass before submitting a pull request
- Run tests with `pytest`

## MCP Server Best Practices

When developing MCP servers, follow these best practices:

1. **Consistent Response Format**: All tools should return responses in a consistent JSON format with status, message, and data fields.
2. **Proper Error Handling**: Use custom exceptions and detailed error messages.
3. **Resource Management**: Properly clean up resources when they're no longer needed.
4. **Performance Optimization**: Use techniques like batching and caching to improve performance.
5. **Documentation**: Document all tools and resources thoroughly.
6. **Versioning**: Include version information in the server metadata.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License. 