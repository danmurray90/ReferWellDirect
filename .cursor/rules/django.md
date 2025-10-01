# Django Rules for ReferWell Direct

## Project Structure

- Follow Django best practices with apps organized by domain
- Keep models, views, serializers, and URLs in separate files
- Use Django's built-in admin interface for data management
- Follow the 12-factor app methodology for configuration

## Models

- Use descriptive field names and help_text for all fields
- Add proper validation using Django's field validators
- Use related_name for foreign keys to avoid conflicts
- Implement **str** methods for all models
- Use UUIDs for primary keys where appropriate
- Add created_at and updated_at timestamps to all models

## Views

- Use class-based views (CBV) for complex logic
- Use function-based views for simple operations
- Implement proper permission checks using Django's permission system
- Use Django's built-in pagination for list views
- Handle exceptions gracefully with appropriate error messages

## Serializers

- Use Django REST Framework serializers for API endpoints
- Implement proper validation in serializers
- Use nested serializers for related objects
- Add proper error handling and custom error messages

## URLs

- Use namespaced URLs for better organization
- Follow RESTful URL patterns
- Use include() for app-specific URL patterns
- Add trailing slashes to URLs

## Settings

- Use environment variables for sensitive configuration
- Separate settings for development, testing, and production
- Use Django's built-in security features
- Configure proper CORS settings for API endpoints

## Database

- Use PostgreSQL with PostGIS extension for geospatial data
- Use pgvector for vector similarity search
- Create proper database indexes for performance
- Use database migrations for schema changes

## Testing

- Write tests for all models, views, and serializers
- Use Django's TestCase for database tests
- Use pytest for more complex testing scenarios
- Mock external API calls in tests
- Test both success and failure scenarios

## Security

- Use Django's built-in CSRF protection
- Implement proper authentication and authorization
- Use Django's built-in password hashing
- Sanitize user input to prevent XSS attacks
- Use Django's built-in SQL injection protection

## Performance

- Use select_related() and prefetch_related() for database queries
- Implement proper caching strategies
- Use database indexes for frequently queried fields
- Monitor database query performance

## Code Quality

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Use meaningful variable and function names
- Keep functions small and focused on single responsibility
