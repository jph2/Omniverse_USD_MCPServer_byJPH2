# Contributing to Omniverse USD MCP Server

Thank you for your interest in contributing to the Omniverse USD MCP Server! This document provides guidelines and information to help you contribute effectively.

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

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/omniverse-usd-mcp-server.git
   cd omniverse-usd-mcp-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

3. Install development dependencies:
   ```bash
   pip install flake8 black pytest
   ```

## Development Workflow

1. **Create a branch**: Always create a branch for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**: Implement your feature or fix

3. **Run tests**: Make sure all tests pass
   ```bash
   pytest
   ```

4. **Check code style**: Ensure your code follows the project's style guidelines
   ```bash
   flake8 usd_mcp_server
   black usd_mcp_server
   ```

5. **Commit changes**: Use clear commit messages that describe the changes
   ```bash
   git commit -m "feat: add new feature X"
   ```

6. **Push changes**: Push your branch to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**: Create a PR from your branch to the main repository

## Continuous Integration

The project uses GitHub Actions for CI, which automatically runs the following checks on all pull requests:

- Linting with flake8
- Code style checking with black
- Syntax checking with Python's compileall
- Running all tests with pytest

Make sure all these checks pass before submitting your PR.

## Adding New MCP Tools

When adding new MCP tools:

1. Add the new tool function in the appropriate module 
2. Register it with the `@mcp.tool()` decorator
3. Add comprehensive documentation in the function docstring
4. Update the README.md to document the new tool
5. Add tests for the new tool in the `tests/` directory

## Code Style Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) coding style
- Use type hints for function parameters and return values
- Write docstrings for all public functions, classes, and modules
- Keep functions focused on a single responsibility
- Use meaningful variable and function names

## Documentation

- Update the README.md when adding new features or changing existing functionality
- Keep the codebase and documentation in sync at all times
- Document any known limitations or edge cases

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

Thank you for your contributions! 