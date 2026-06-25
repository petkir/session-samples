# Swagger UI Integration

This document explains how to use the Swagger UI that has been added to the elat Local LLM Chat API.

## Access Swagger UI

When running the application in development mode, you can access the Swagger UI at:

**URL**: `https://localhost:7154/swagger` or `http://localhost:5154/swagger`

## Features

### 🔧 API Documentation
- Complete API documentation with descriptions for all endpoints
- Request and response schemas
- Parameter details and examples
- HTTP status codes and their meanings

### 🔐 Authentication Support
- JWT Bearer token authentication integrated
- Click the "Authorize" button in the top-right corner
- Enter your JWT token in the format: `Bearer YOUR_TOKEN_HERE`
- All authenticated endpoints will automatically include the token

### 📝 Interactive Testing
- Test API endpoints directly from the browser
- Fill in parameters and request bodies
- Send real requests to your API
- View responses in real-time

### 🎯 Enhanced Features
- XML documentation comments for detailed endpoint descriptions
- Request/response examples
- Model schemas with property descriptions
- Expandable request/response details

## How to Use

### 1. Start the Application
```bash
cd elat.local.llm.Server
dotnet run
```

### 2. Open Swagger UI
Navigate to `https://localhost:7154/swagger` in your browser

### 3. Authenticate (for protected endpoints)
1. Click the "Authorize" button (🔒 icon)
2. Enter your JWT token: `Bearer YOUR_JWT_TOKEN`
3. Click "Authorize"
4. Click "Close"

### 4. Test Endpoints
1. Expand any endpoint section
2. Click "Try it out"
3. Fill in required parameters
4. Click "Execute"
5. View the response below

## Available Endpoints

### Chat Operations
- **GET** `/api/chat/sessions` - Get all chat sessions
- **POST** `/api/chat/sessions` - Create a new chat session
- **GET** `/api/chat/sessions/{sessionId}` - Get specific chat session
- **POST** `/api/chat/sessions/{sessionId}/messages` - Send message (SSE)
- **GET** `/api/chat/attachments/{attachmentId}` - Get attachment

### Demo
- **GET** `/WeatherForecast` - Sample weather forecast

## Special Notes

### Server-Sent Events (SSE)
The `/api/chat/sessions/{sessionId}/messages` endpoint uses Server-Sent Events for streaming responses. While you can test this endpoint in Swagger UI, the streaming nature is best experienced in the actual chat application.

### File Uploads
The message endpoint supports file uploads via multipart/form-data. You can test file uploads directly in Swagger UI by using the file upload control.

### Authentication Tokens
To get a JWT token for testing:
1. Use the React frontend to authenticate with Azure AD
2. Extract the token from the browser's developer tools
3. Use it in Swagger UI's Authorization header

## Configuration

The Swagger UI configuration is located in `Program.cs`:

```csharp
builder.Services.AddSwaggerGen(options =>
{
    // Configuration for API info, security, XML documentation
});

app.UseSwagger();
app.UseSwaggerUI(options =>
{
    // UI configuration
});
```

## XML Documentation

The project generates XML documentation automatically. To add documentation to your endpoints:

```csharp
/// <summary>
/// Brief description of the endpoint
/// </summary>
/// <param name="parameter">Parameter description</param>
/// <returns>Return value description</returns>
/// <response code="200">Success response description</response>
/// <response code="400">Bad request description</response>
[HttpGet("endpoint")]
[ProducesResponseType(StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status400BadRequest)]
public async Task<ActionResult> YourEndpoint(string parameter)
{
    // Implementation
}
```

## Production Considerations

- Swagger UI is only enabled in Development environment
- For production, consider using a separate documentation site
- Ensure sensitive information is not exposed in documentation
- Consider API versioning for future updates

## Troubleshooting

### Swagger UI Not Loading
- Ensure you're running in Development mode
- Check that the application is running on the correct port
- Verify the URL: `https://localhost:7154/swagger`

### Authentication Issues
- Ensure your JWT token is valid and not expired
- Check that the token includes the required scopes
- Verify the token format: `Bearer YOUR_TOKEN_HERE`

### Missing Documentation
- Ensure XML documentation is enabled in the project file
- Check that XML comments are properly formatted
- Rebuild the project after adding documentation
