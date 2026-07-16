# MRL_AGI Web UI

**Origin Signature**: MrLiouWord
**Version**: 1.0
**Status**: P0-1 Complete ✅

---

## Overview

Production-ready web interface for MRL_AI_SYSTEM. This single-page application provides a complete chat interface with session management, task orchestration, and settings configuration.

## Features

### ✅ Implemented (P0-1 Complete)

1. **Chat Interface**
   - Large input box for user messages
   - Real-time message display with role indicators (User/Assistant/System)
   - Message metadata display (model, engine, runtime_mode, trace_id)
   - Auto-scrolling messages area

2. **Session Management**
   - Create new chat sessions
   - View session history in sidebar
   - Switch between active sessions
   - Display turn count per session
   - Clear current chat

3. **Settings Panel**
   - API URL configuration
   - Authentication token (Bearer token)
   - Model selection (GPT-4o, Claude, Local, Mock)
   - Persistent settings in localStorage

4. **Task Submission**
   - Agent task interface
   - Task type selection (simple/agent/multi_agent)
   - Agent list configuration
   - Task result display

5. **Runtime Information**
   - Runtime mode display (production/development/test)
   - Origin signature display
   - Status bar with real-time updates
   - Error handling and display

6. **Security**
   - Optional Bearer token authentication
   - No hardcoded credentials
   - CORS-compatible requests

---

## Quick Start

### Prerequisites

1. API Gateway running on `http://localhost:7771`
2. Modern web browser (Chrome, Firefox, Safari, Edge)
3. Local web server (for development) OR direct file access

### Method 1: Direct File Access

```bash
# Navigate to UI directory
cd /home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/ui/mrl_app

# Open in browser
open index.html
# Or on Linux:
xdg-open index.html
```

**Note**: Some browsers restrict local file access. Use Method 2 if CORS errors occur.

### Method 2: Python HTTP Server (Recommended)

```bash
# Navigate to UI directory
cd /home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/ui/mrl_app

# Start simple HTTP server
python3 -m http.server 8000

# Open browser
open http://localhost:8000
```

### Method 3: Node.js HTTP Server

```bash
# Install http-server globally
npm install -g http-server

# Navigate to UI directory
cd /home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/ui/mrl_app

# Start server
http-server -p 8000

# Open browser
open http://localhost:8000
```

---

## Configuration

### Initial Setup

1. **Start API Gateway**
   ```bash
   # Ensure API gateway is running
   python 09_workflow/api_gateway.py --host 0.0.0.0 --port 7771
   ```

2. **Open Web UI**
   - Access via one of the methods above
   - Default: `http://localhost:8000`

3. **Configure Settings (Optional)**
   - Click ⚙️ Settings button
   - Enter API URL (default: `http://localhost:7771`)
   - Enter Bearer token if authentication enabled
   - Select preferred model
   - Click "Save Settings"

### Settings

**API URL**
- Default: `http://localhost:7771`
- Change if API gateway is on different host/port
- Format: `http://hostname:port` (no trailing slash)

**Authentication Token**
- Optional if `MRL_API_REQUIRE_AUTH=false`
- Required if `MRL_API_REQUIRE_AUTH=true`
- Format: Enter token value only (without "Bearer " prefix)
- Stored in browser localStorage

**Model Selection**
- Default: Uses config default
- GPT-4o: OpenAI (requires OPENAI_API_KEY)
- Claude 3.5 Sonnet: Anthropic (requires ANTHROPIC_API_KEY)
- Llama 2: Local model (Ollama/llama.cpp)
- Mock: Development only (blocked in production mode)

---

## Usage

### Starting a Chat

1. Click "+ New Chat" in sidebar
2. Type message in input box
3. Press Enter or click "Send"
4. View response from AI assistant

**Keyboard Shortcuts**:
- `Enter`: Send message
- `Shift+Enter`: New line in message

### Session Management

**Create New Session**:
- Click "+ New Chat" button
- System prompt automatically added
- Session saved immediately

**Switch Sessions**:
- Click any session in sidebar
- Messages load automatically
- Continue previous conversation

**Clear Chat**:
- Click "🗑️ Clear" button
- Clears current display (session persists on server)

### Submitting Agent Tasks

1. Click "Run Task" button (if available)
2. Enter task goal/objective
3. Select task type:
   - **Simple**: Single function execution
   - **Agent**: Single agent with ReAct
   - **Multi-Agent**: Multiple coordinated agents
4. For multi-agent: Enter agent names (comma-separated)
5. Click "Submit Task"
6. View result in panel

**Example Tasks**:
- "Analyze the repository structure"
- "Write a summary of the codebase"
- "Generate test cases for module X"

---

## Response Metadata

Every assistant response includes trace information:

- **Model**: LLM model used (e.g., "gpt-4o", "llama2")
- **Engine**: Adapter type (e.g., "LocalAdapter", "OpenAIAdapter")
- **Mode**: Runtime mode (production/development/test)
- **Trace**: Trace ID for debugging (truncated in UI)

**Example**:
```
Model: gpt-4o | Engine: OpenAIAdapter | Mode: production | Trace: 123e4567...
```

---

## Troubleshooting

### Cannot Connect to API

**Symptom**: "Failed to connect" in status bar

**Solutions**:
1. Verify API gateway is running:
   ```bash
   curl http://localhost:7771/health
   ```

2. Check API URL in settings
3. Verify CORS is enabled in API config
4. Check browser console for errors (F12)

### Authentication Failed (403)

**Symptom**: "Runtime error: Adapter 'mock' is PROHIBITED" or "Unauthorized"

**Solutions**:
1. Check `MRL_RUNTIME_MODE` environment variable
2. If production mode, use real model (not "mock")
3. Enter correct Bearer token in Settings
4. Verify `MRL_API_REQUIRE_AUTH` setting

### CORS Errors

**Symptom**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solutions**:
1. Ensure API gateway has CORS enabled
2. Use Python/Node HTTP server (not direct file://)
3. Check `MRL_API_CORS_ORIGINS` includes your UI origin
4. Add wildcard in development: `MRL_API_CORS_ORIGINS=*`

### Session Not Loading

**Symptom**: Empty message list or "Session not found"

**Solutions**:
1. Verify session exists: `curl http://localhost:7771/sessions`
2. Check session ID is valid UUID
3. Refresh session list (reload page)
4. Create new session

---

## Development

### File Structure

```
ui/mrl_app/
├── index.html      # Main HTML structure
├── styles.css      # UI styling (CSS)
├── app.js          # Application logic (JavaScript)
└── README.md       # This file
```

### Technology Stack

- **HTML5**: Semantic structure
- **CSS3**: Modern styling (flexbox, grid, variables)
- **JavaScript ES6+**: Application logic
- **Fetch API**: HTTP requests
- **localStorage**: Settings persistence

### No Dependencies

- Pure HTML/CSS/JavaScript
- No build step required
- No npm packages
- No framework required
- Works in any modern browser

### Customization

**Change Colors**:
Edit CSS variables in `styles.css`:
```css
:root {
    --primary-color: #2563eb;  /* Blue */
    --success: #10b981;        /* Green */
    --error: #ef4444;          /* Red */
}
```

**Add New Features**:
1. Add UI elements to `index.html`
2. Add styles to `styles.css`
3. Add logic to `app.js` (`UIController` class)

**API Integration**:
- All API calls in `APIClient` class
- Add new methods for new endpoints
- Follow existing pattern

---

## Production Deployment

### nginx Configuration

```nginx
server {
    listen 80;
    server_name mrl-app.your-domain.com;

    root /opt/MRL_AI_SYSTEM/ui/mrl_app;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests
    location /api/ {
        proxy_pass http://localhost:7771/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Apache Configuration

```apache
<VirtualHost *:80>
    ServerName mrl-app.your-domain.com
    DocumentRoot /opt/MRL_AI_SYSTEM/ui/mrl_app

    <Directory /opt/MRL_AI_SYSTEM/ui/mrl_app>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    # Proxy API requests
    ProxyPass /api/ http://localhost:7771/
    ProxyPassReverse /api/ http://localhost:7771/
</VirtualHost>
```

### Security Checklist

- [ ] Enable HTTPS (SSL certificate)
- [ ] Set proper CORS origins (not wildcard)
- [ ] Enable authentication (`MRL_API_REQUIRE_AUTH=true`)
- [ ] Use strong Bearer tokens
- [ ] Rate limit API endpoint
- [ ] Monitor access logs
- [ ] Regular security updates

---

## Browser Compatibility

✅ **Fully Supported**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

⚠️ **Partial Support**:
- IE 11: Not supported (use modern browser)
- Older browsers: May lack ES6+ features

---

## API Endpoints Used

The UI integrates with the following API gateway endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API status and runtime mode |
| `/sessions` | GET | List all conversation sessions |
| `/sessions` | POST | Create new session |
| `/sessions/{id}` | GET | Get session history |
| `/sessions/{id}` | DELETE | Delete session |
| `/chat` | POST | Send message to AI |
| `/agent/run` | POST | Submit agent task |

**Full API documentation**: See `docs/P0_PRODUCTION_CORE.md`

---

## Future Enhancements (Post-P0)

### P1 Features (Operations)
- [ ] User registration/login UI
- [ ] Payment integration UI
- [ ] Result unlock flow (full vs partial)
- [ ] User profile management

### P2 Features (UX)
- [ ] Streaming responses (SSE)
- [ ] File upload interface
- [ ] Task template selector
- [ ] Conversation export (MD/JSON)
- [ ] Dark mode toggle

### P3 Features (Advanced)
- [ ] Admin dashboard
- [ ] Analytics/metrics display
- [ ] Multi-language support
- [ ] Voice input/output

---

## Testing

### Manual Testing Checklist

- [ ] Open UI in browser
- [ ] Create new session
- [ ] Send message, receive response
- [ ] Verify metadata displayed
- [ ] Switch between sessions
- [ ] Configure settings
- [ ] Test with different models
- [ ] Test with authentication
- [ ] Test error handling (invalid token)
- [ ] Test in production mode

### Automated Testing

Currently no automated tests. Future implementation:
- Unit tests (Jest)
- E2E tests (Playwright/Cypress)
- Visual regression tests

---

## License & Attribution

**Origin Signature**: MrLiouWord
**Copyright**: As per repository LICENSE file
**Attribution**: MRL_AI_SYSTEM Project

---

## Support

For issues or questions:
1. Check this README
2. See `docs/DEPLOYMENT.md`
3. See `docs/P0_PRODUCTION_CORE.md`
4. Open issue in repository

---

**Status**: P0-1 Complete ✅
**Ready for**: Production deployment
**Last Updated**: 2026-05-04