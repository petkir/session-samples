# Chat Interface with SSE, File Upload, and Entra ID Authentication

This is a complete chat application built with .NET 9 and React 19 that includes:

- 🔐 **Entra ID Authentication** - Secure authentication using Microsoft identity platform
- 💬 **Real-time Chat** - Server-Sent Events (SSE) for streaming responses
- 📁 **File Upload** - Support for uploading files and images
- 🗂️ **Chat History** - Persistent chat sessions with message history
- 🤖 **AI Integration** - Local Ollama LLM using Semantic Kernel
- 🗄️ **Vector Database** - Qdrant for semantic search and knowledge retrieval
- 🎨 **OpenAI-like Interface** - Familiar chat interface design
- 🌓 **Light/Dark Mode** - Toggle between light and dark themes with localStorage persistence

## New Features

### UI/UX Improvements
- **Mantine Components** - Modern, accessible UI components from Mantine (htowoo from n8d)
- **SASS Styling** - All styling converted from CSS to SASS for better maintainability
- **Theme Toggle** - Light/Dark mode toggle positioned in the top-right corner
- **Theme Persistence** - User's theme preference is saved in localStorage
- **Browser Detection** - Automatically detects browser's color scheme preference if no saved preference exists
- **Responsive Design** - Fully responsive layout that works on all screen sizes

### Component Architecture
- **AppShell Layout** - Uses Mantine's AppShell component for consistent layout
- **Modern Icons** - Tabler Icons for consistent and modern iconography
- **Accessibility** - Full ARIA support and keyboard navigation
- **Type Safety** - Complete TypeScript implementation with proper typing

## Architecture

### Backend (.NET 9)
- **ASP.NET Core Web API** with minimal APIs
- **Entity Framework Core** with SQLite for data persistence
- **Semantic Kernel** for AI chat completion
- **Ollama connector** for local LLM integration
- **Qdrant** for vector database and semantic search
- **Microsoft.Identity.Web** for Entra ID authentication
- **Server-Sent Events** for real-time streaming

### Frontend (React 19 + TypeScript)
- **React 19** with TypeScript
- **Vite** for fast development and building
- **Mantine** (htowoo from n8d) for modern UI components
- **SASS** for styling instead of CSS
- **Light/Dark mode** toggle with localStorage persistence
- **MSAL React** for Entra ID authentication
- **Axios** for HTTP requests
- **Tabler Icons** for consistent iconography
- **Custom SSE implementation** for real-time chat

## Prerequisites

1. **Node.js** (v18 or higher)
2. **.NET 9 SDK**
3. **Ollama** running locally
4. **Qdrant** vector database (Docker recommended)
5. **[Azure AD App Registration](SETUP_AZURE.md)** (for Entra ID authentication)

## Quick Setup (Recommended)

We provide automated setup scripts that check for prerequisites, install missing components, and start all necessary services:

### 🍎 macOS

```bash
./setup-macos.sh
```

### 🐧 Linux

```bash
./setup-linux.sh
```

### 🪟 Windows

```batch
setup-windows.bat
```

These scripts will:

- ✅ Check and install Node.js (v18+)
- ✅ Check and install .NET 9 SDK
- ✅ Check and install Ollama
- ✅ Download the llama3.2 model
- ✅ Install frontend dependencies
- ✅ Restore backend dependencies
- ✅ Start all services

## Manual Setup Instructions

If you prefer manual setup or the automated scripts don't work for your system:

### 1. Ollama Setup

#### Linux

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (e.g., llama3.2)
ollama pull llama3.2

# Start Ollama server
ollama serve
```

#### macOS

```bash
# Install via Homebrew
brew install ollama

# Pull a model (e.g., llama3.2)
ollama pull llama3.2

# Start Ollama server
ollama serve
```

#### Windows

```powershell
# Install via WinGet or download from https://ollama.com
winget install Ollama.Ollama

# Pull a model (e.g., llama3.2)
ollama pull llama3.2

# Start Ollama server
ollama serve
```

### 2. Qdrant Vector Database Setup

#### Using Docker (Recommended)

```bash
# Start Qdrant server with Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

#### Alternative: Local Installation

**Linux/macOS:**
```bash
# Download and run Qdrant binary
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
./qdrant
```

**Windows:**
```powershell
# Download from GitHub releases or use Docker
# https://github.com/qdrant/qdrant/releases
```

The Qdrant server will be available at:
- REST API: `http://localhost:6333`
- gRPC API: `http://localhost:6334`

### 3. Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: Chat App
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: `https://localhost:54375` (SPA)
5. After creation, note down:
   - **Application (client) ID**
   - **Directory (tenant) ID**
6. Configure **Authentication**:
   - Add `http://localhost:5173` as another redirect URI (for development)
   - Enable **Access tokens** and **ID tokens**
7. Configure **API permissions**:
   - Add `User.Read` permission
   - Grant admin consent

### 4. Configuration

#### Backend Configuration
Update `appsettings.json` and `appsettings.Development.json`:

```json
{
  "AzureAd": {
    "Instance": "https://login.microsoftonline.com/",
    "Domain": "your-domain.onmicrosoft.com",
    "TenantId": "your-tenant-id",
    "ClientId": "your-client-id"
  },
  "Ollama": {
    "Endpoint": "http://localhost:11434",
    "ModelId": "llama3.2"
  },
  "Qdrant": {
    "Endpoint": "http://localhost:6333",
    "CollectionName": "knowledge_base"
  }
}
```

#### Frontend Configuration
Create a `.env` file in the `elat.local.llm.client` directory (copy from `.env.example`):

```bash
# Azure AD Configuration
VITE_AZURE_CLIENT_ID=your-client-id-here
VITE_AZURE_TENANT_ID=your-tenant-id-here
VITE_AZURE_DOMAIN=your-domain.onmicrosoft.com

# API Configuration
VITE_API_BASE_URL=http://localhost:5227/api
```

The `src/authConfig.ts` file is already configured to read these environment variables automatically.

### 4. Running the Application

#### Start Backend
```bash
cd elat.local.llm/elat.local.llm.Server
dotnet run
```

#### Start Frontend (Development)
```bash
cd elat.local.llm/elat.local.llm.client
npm run dev
```

#### Start Both (Production)
```bash
cd elat.local.llm/elat.local.llm.Server
dotnet run
# The backend will serve the React app at https://localhost:5001
# frontend will be served at  https://localhost:54375/

```

## Features

### Chat Interface
- **Multiple chat sessions** - Create and manage multiple conversations
- **Real-time streaming** - AI responses stream in real-time using SSE
- **File upload support** - Upload images, documents, and other files
- **Message history** - All conversations are saved and persisted
- **Responsive design** - Works on desktop and mobile devices

### File Upload
- **Multiple file types** - Images, PDFs, documents, text files
- **File size display** - Shows file size and type
- **Preview attachments** - View uploaded files in chat
- **Drag and drop** - Easy file upload interface

### Authentication
- **Entra ID integration** - Enterprise-grade authentication
- **Token management** - Automatic token refresh
- **Secure API calls** - All API calls are authenticated
- **Role-based access** - Can be extended for role-based permissions

### AI Integration
- **Local LLM** - Uses Ollama for privacy and control
- **Semantic Kernel** - Microsoft's AI orchestration framework
- **Streaming responses** - Real-time AI response generation
- **Context awareness** - Maintains conversation context

## API Endpoints

### Authentication Required
All endpoints require a valid Bearer token from Entra ID.

### Chat Endpoints
- `GET /api/chat/sessions` - Get all chat sessions
- `POST /api/chat/sessions` - Create a new chat session
- `GET /api/chat/sessions/{id}` - Get specific chat session
- `POST /api/chat/sessions/{id}/messages` - Send message (with files)
- `GET /api/chat/attachments/{id}` - Get attachment file

### Response Format
All responses follow standard JSON format with proper error handling.

## Database Schema

### ChatSession
- `Id` (Guid) - Primary key
- `UserId` (string) - User identifier from Entra ID
- `Title` (string) - Chat session title
- `CreatedAt` (DateTime) - Creation timestamp
- `UpdatedAt` (DateTime) - Last update timestamp

### ChatMessage
- `Id` (Guid) - Primary key
- `ChatSessionId` (Guid) - Foreign key to ChatSession
- `Role` (string) - "user" or "assistant"
- `Content` (string) - Message content
- `CreatedAt` (DateTime) - Creation timestamp

### ChatAttachment
- `Id` (Guid) - Primary key
- `ChatMessageId` (Guid) - Foreign key to ChatMessage
- `FileName` (string) - Original file name
- `ContentType` (string) - MIME type
- `FilePath` (string) - Server file path
- `FileSize` (long) - File size in bytes
- `CreatedAt` (DateTime) - Creation timestamp

## Security Considerations

1. **Authentication**: All API endpoints require valid Entra ID tokens
2. **File Upload**: File types and sizes are validated
3. **SQL Injection**: Uses parameterized queries via Entity Framework
4. **XSS Protection**: React automatically escapes content
5. **CORS**: Configured for specific origins only
6. **File Storage**: Uploaded files are stored securely on server

## Development Notes

- Uses SQLite for development (easily replaceable with SQL Server/PostgreSQL)
- Hot reload enabled for both frontend and backend
- Comprehensive error handling and logging
- TypeScript for type safety
- ESLint for code quality
- SASS for modern CSS preprocessing
- Mantine components for consistent UI/UX
- Light/Dark mode with system preference detection
- localStorage for theme persistence
- Responsive design with mobile-first approach

## Deployment

This application can be deployed to:
- **Azure App Service** (recommended)
- **Azure Container Apps**
- **Docker containers**
- **Traditional hosting**

For production deployment, update connection strings and authentication URLs accordingly.

## Troubleshooting

### Common Issues

1. **Ollama not responding**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is available: `ollama list`

2. **Authentication failures**
   - Verify Azure AD configuration
   - Check redirect URIs match exactly
   - Ensure proper permissions are granted

3. **File upload issues**
   - Check file size limits
   - Verify upload directory permissions
   - Ensure supported file types

4. **Database issues**
   - Database is created automatically on first run
   - Check connection string in appsettings.json
   - Verify write permissions for SQLite file

## Contributing

Feel free to submit issues and enhancement requests!