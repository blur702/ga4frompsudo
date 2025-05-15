# Development Guide

This document provides guidelines and best practices for developers working on the GA4 Analytics Dashboard application.

## Development Environment Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd ga4-analytics-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file for local configuration:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file to configure your development environment.

## Development Workflow

The project follows a Test-Driven Development (TDD) approach:

1. **Plan the Component**: Define the functionality and requirements
2. **Write Tests**: Create tests for the component before implementation
3. **Implement the Component**: Write the minimal code needed to pass the tests
4. **Review and Refine**: Refactor the code while maintaining test coverage
5. **Document**: Add comprehensive docstrings and update documentation

## Project Structure

The application follows the Model-View-Controller (MVC) pattern:

```
app/
├── models/       # Data models and database interactions
├── views/        # Templates and static files
├── controllers/  # Route handlers and request processing
├── services/     # Business logic and external API interactions
├── plugins/      # Modular, extensible functionality
├── utils/        # Helper functions and utilities
├── __init__.py   # Application factory
└── config.py     # Configuration classes
```

## Coding Standards

### Python Style Guidelines

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use meaningful variable and function names
- Add type hints where applicable

### Documentation

- All modules, classes, and functions should have docstrings
- Use Google-style docstrings format
- Include parameter descriptions and return types
- Document exceptions that may be raised

### Error Handling

- Use appropriate exception handling
- Log exceptions with contextual information
- Provide user-friendly error messages
- Avoid catching generic exceptions without re-raising

### Logging

- Use the Python logging module
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include context information in log messages
- Avoid logging sensitive information

## Testing

### Running Tests

Run the test suite using pytest:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/unit/models/test_database.py
```

Run with coverage:
```bash
pytest --cov=app tests/
```

### Test Types

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete user flows

### Test Coverage

Aim for high test coverage, especially for critical paths. The coverage report can be generated with:
```bash
coverage report
```

## Git Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with descriptive messages:
   ```bash
   git commit -m "Add: description of what was added"
   git commit -m "Fix: description of what was fixed"
   ```

3. Push your branch and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. After review and approval, merge the pull request into `main`

## Building and Running

Start the development server:
```bash
flask run
# or
python run.py
```

The application will be available at `http://127.0.0.1:5000` (or the configured host/port).

## Plugin Development

To create a new analytics plugin:

1. Create a new module in the `app/plugins` directory:
   ```python
   # app/plugins/my_plugin.py
   from app.plugins.base_plugin import BasePlugin
   
   class MyPlugin(BasePlugin):
       NAME = "my_plugin"
       DESCRIPTION = "Description of my plugin"
       
       def process_data(self, data):
           # Process data and return results
           return processed_data
   ```

2. Register your plugin by updating the plugins initialization:
   ```python
   # app/plugins/__init__.py
   from app.plugins.my_plugin import MyPlugin
   
   AVAILABLE_PLUGINS = {
       MyPlugin.NAME: MyPlugin,
       # other plugins...
   }
   ```

## API Development

When adding new API endpoints:

1. Create a new route in the appropriate controller:
   ```python
   @api_bp.route('/endpoint', methods=['GET'])
   def my_endpoint():
       # Handle request
       return jsonify(result)
   ```

2. Document the endpoint in the API documentation (`docs/api.md`)
3. Add tests for the endpoint

## Troubleshooting

If you encounter issues during development:

1. Check the application logs
2. Verify your environment variables
3. Ensure database migrations are up-to-date
4. Check for conflicting package versions