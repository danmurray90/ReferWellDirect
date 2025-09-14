# Testing Rules for ReferWell Direct

## Test Structure
- Use pytest as the primary testing framework
- Use pytest-django for Django-specific testing
- Organize tests in test_*.py files within each app
- Use descriptive test function names

## Test Categories
- Unit tests for individual functions and methods
- Integration tests for component interactions
- End-to-end tests for complete user workflows
- Performance tests for critical paths

## Model Testing
- Test model creation and validation
- Test model methods and properties
- Test model relationships and constraints
- Test model string representations

## View Testing
- Test view responses and status codes
- Test view permissions and authentication
- Test view data and context
- Test view error handling

## API Testing
- Test API endpoints and responses
- Test API authentication and permissions
- Test API data validation
- Test API error responses

## Service Testing
- Test service layer functions
- Test business logic and calculations
- Test external service integrations (mocked)
- Test error handling and edge cases

## Test Data
- Use factory_boy for test data generation
- Create realistic test fixtures
- Use freezegun for time-based testing
- Mock external API calls

## Test Coverage
- Aim for high test coverage on critical paths
- Focus on business logic and edge cases
- Don't test Django's built-in functionality
- Use coverage.py for coverage reporting

## Test Performance
- Keep tests fast and focused
- Use database transactions for test isolation
- Mock expensive operations
- Use test-specific settings

## Test Documentation
- Write clear test descriptions
- Document test setup and teardown
- Explain complex test scenarios
- Keep tests maintainable

## Continuous Integration
- Run tests on every commit
- Use different test environments
- Test against multiple Python versions
- Test database migrations

## Test Best Practices
- Write tests before or alongside code
- Test both success and failure scenarios
- Use descriptive assertions
- Keep tests independent and isolated
- Refactor tests when refactoring code
