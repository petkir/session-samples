# OpenAPI Specification for elat Local LLM Chat API

This directory contains the OpenAPI specification for the elat Local LLM Chat API built with .NET 9.

## Files

- `openapi.yaml` - OpenAPI 3.1.0 specification in YAML format
- `openapi.json` - OpenAPI 3.1.0 specification in JSON format
- `README.md` - This file

## API Overview

The API provides a modern chat application with the following features:

### Core Features
- **Chat Sessions Management**: Create, retrieve, and manage chat sessions
- **Real-time AI Streaming**: Server-Sent Events (SSE) for streaming AI responses
- **File Upload Support**: Upload and attach files to messages
- **Azure AD Authentication**: Secure authentication using Azure Active Directory
- **Message History**: Persistent storage of chat history

### Technology Stack
- .NET 9 Web API
- Entity Framework Core with SQLite
- Semantic Kernel for AI integration
- Ollama LLM for local language model
- Azure AD (Entra ID) for authentication

## Endpoints

### Chat Operations
- `GET /api/chat/sessions` - Get all chat sessions
- `POST /api/chat/sessions` - Create a new chat session
- `GET /api/chat/sessions/{sessionId}` - Get a specific chat session
- `POST /api/chat/sessions/{sessionId}/messages` - Send a message (SSE response)
- `GET /api/chat/attachments/{attachmentId}` - Get an attachment

### Demo Endpoints
- `GET /WeatherForecast` - Sample weather forecast endpoint

## Authentication

The API uses Azure AD (Entra ID) for authentication. All chat endpoints require authentication.

### Security Schemes
- **BearerAuth**: JWT token from Azure AD
- **AzureAD**: OAuth2 with Azure AD

### Required Scopes
- `openid` - OpenID Connect scope
- `profile` - Access to user profile information
- `User.Read` - Read user profile

## Server-Sent Events (SSE)

The `/api/chat/sessions/{sessionId}/messages` endpoint uses Server-Sent Events to stream AI responses in real-time.

### SSE Response Format
```
data: {"type":"chunk","content":"Hello","messageId":"uuid"}

data: {"type":"chunk","content":" there!","messageId":"uuid"}

data: {"type":"complete","content":"","messageId":"uuid"}
```

### SSE Event Types
- `chunk` - Partial response content
- `complete` - Response completed
- `error` - Error occurred

## File Upload

The API supports file uploads via multipart/form-data on the message endpoint:

```
POST /api/chat/sessions/{sessionId}/messages
Content-Type: multipart/form-data

content: "Your message"
files: [binary file data]
```

## Usage Examples

### Create a Chat Session
```bash
curl -X POST "https://localhost:7154/api/chat/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My New Chat"}'
```

### Send a Message
```bash
curl -X POST "https://localhost:7154/api/chat/sessions/{sessionId}/messages" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "content=Hello, how are you?" \
  -F "files=@document.pdf"
```

### Get Chat Sessions
```bash
curl -X GET "https://localhost:7154/api/chat/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Development Server URLs

- **HTTPS**: `https://localhost:7154`
- **HTTP**: `http://localhost:5154`

## Tools and Viewers

You can use the OpenAPI specification with various tools:

### Online Viewers
- [Swagger Editor](https://editor.swagger.io/) - Load the YAML/JSON file
- [Redoc](https://redoc.ly/redoc/) - Generate documentation
- [Postman](https://www.postman.com/) - Import for API testing

### Local Tools
- **Swagger UI**: Can be integrated into the .NET application
- **Insomnia**: Import OpenAPI spec for testing
- **Bruno**: Modern API client with OpenAPI support

## Integration

To add Swagger UI to your .NET project:

1. Install the NuGet package:
   ```bash
   dotnet add package Swashbuckle.AspNetCore
   ```

2. Add to `Program.cs`:
   ```csharp
   builder.Services.AddSwaggerGen();
   
   // In the app configuration
   if (app.Environment.IsDevelopment())
   {
       app.UseSwagger();
       app.UseSwaggerUI();
   }
   ```

## Contributing

When updating the API, please ensure the OpenAPI specification is updated accordingly to maintain accurate documentation.
