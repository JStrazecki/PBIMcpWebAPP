# MCP Connection Testing Tracker

## Current Issue Summary
**Problem**: Claude Enterprise successfully authenticates via OAuth but the connection drops and tools become unavailable.

**Root Causes Identified**:
1. Claude.ai never calls `tools/list` endpoint even when `listChanged=true` (known bug)
2. SSE (Server-Sent Events) connection appears to establish but doesn't maintain proper event stream
3. HTTP transport works for initial handshake but fails to maintain persistent connection

## Analysis Findings

### From logs.txt (Latest Session):
- ✅ OAuth flow completes successfully
- ✅ Token is properly sent in Authorization header after OAuth
- ✅ Initialize method succeeds with valid token
- ✅ Server receives `notifications/initialized` 
- ⚠️ SSE connection establishes but no tool discovery follows
- ❌ No `tools/list` request ever made by Claude

### From Previous Attempts (Git History):
1. **FastMCP Migration** - Reverted (commit 640701f)
2. **Tools in Initialize Response** - Tried but didn't work (commit 8b692da)
3. **HTTP-only Transport** - Forced HTTP but issue persists (commit 25ad1a9)
4. **SSE Retry Loop Fix** - Fixed loop but tools still not discovered (commit 1ce043c)
5. **Bearer Token Capitalization** - Fixed but not the root cause (commit 5953cb9)

## Current Server Implementation

### mcp_simple_server.py Analysis:
- Uses FastAPI with OAuth2 flow
- Supports both HTTP and SSE transports
- Has proper CORS headers for claude.ai
- Implements MCP protocol version 2024-11-05
- Tools are properly defined but Claude never requests them

## Testing History

### Test #1: Initial Deployment (Current State)
**Date**: 2025-08-03
**Configuration**:
- Server: mcp_simple_server.py
- Transport: HTTP + SSE
- OAuth: Working with client_id 5bdb10bc-bb29-4af9-8cb5-062690e6be15

**Results**:
- OAuth: ✅ Success
- Initialize: ✅ Success
- Tool Discovery: ❌ Failed (Claude never calls tools/list)
- Connection Stability: ❌ Drops after initial handshake

**Logs Evidence**:
```
✅ OAuth token received: Bearer 04jzktJbO0yLeUF90lUEUJK...
✅ Initialize successful with token
✅ SSE endpoint accessed
❌ No tools/list request follows
```

## Proposed Solutions to Test

### Solution 1: Force Tool Registration in Initialize
**Approach**: Include all tools directly in the initialize response
**Priority**: HIGH
**Implementation**:
```python
# In handle_initialize response:
"tools": [{
    "name": "health_check",
    "description": "Check server health",
    "inputSchema": {...}
}, ...]
```

### Solution 2: Implement Heartbeat/Keepalive
**Approach**: Send periodic SSE events to maintain connection
**Priority**: HIGH
**Implementation**:
- Send `event: ping` every 30 seconds
- Include timestamp in ping data

### Solution 3: WebSocket Transport
**Approach**: Replace SSE with WebSocket for more stable connection
**Priority**: MEDIUM
**Implementation**:
- Add WebSocket endpoint at /ws
- Maintain bidirectional communication

### Solution 4: Session-Based Authentication
**Approach**: Use session tokens instead of OAuth tokens in MCP requests
**Priority**: MEDIUM
**Implementation**:
- Create session after OAuth
- Use session ID in custom header

### Solution 5: Implement Tool Pre-caching
**Approach**: Send tool definitions as SSE events immediately after connection
**Priority**: HIGH
**Implementation**:
```python
# After SSE connection established:
yield f"event: tools_available\ndata: {json.dumps(tools)}\n\n"
```

## Testing Plan Template

### Pre-Deployment Checklist
- [ ] Update code with proposed solution
- [ ] Test locally if possible
- [ ] Commit with descriptive message
- [ ] Deploy to Azure

### Post-Deployment Test Steps
1. **Clear Claude.ai Cache**
   - Remove and re-add MCP server
   - Clear browser cache if needed

2. **OAuth Flow Test**
   - Click "Configure" in Claude Enterprise
   - Verify redirect to OAuth page
   - Complete authentication
   - Check logs for token generation

3. **Connection Test**
   - Monitor server logs in real-time
   - Check for initialize request
   - Look for tools/list request
   - Verify SSE connection establishment

4. **Tool Discovery Test**
   - Type "what tools are available?"
   - Check if tools appear in Claude UI
   - Try to use a tool

5. **Stability Test**
   - Wait 5 minutes
   - Try using a tool again
   - Check if connection maintained

### Results Documentation Template
```markdown
## Test #N: [Solution Name]
**Date**: YYYY-MM-DD HH:MM
**Commit**: [hash]
**Changes Made**:
- 
- 

**Test Results**:
- OAuth Flow: ✅/❌
- Initialize: ✅/❌
- Tool Discovery: ✅/❌
- Tool Usage: ✅/❌
- Connection Stability (5min): ✅/❌

**Logs**:
```
[Paste relevant log snippets]
```

**Conclusion**:
[What worked, what didn't, next steps]
```

## Test #2: Force Tool Registration in Initialize Response
**Date**: 2025-08-03
**Commit**: Pending deployment
**Changes Made**:
- Modified `handle_http_transport()` initialize response to include tools directly in capabilities
- Added `listChanged: true` flag to signal tools are available
- Included tools at multiple levels for compatibility (in capabilities.tools.available and at root)
- Enhanced SSE stream to send `tools_available` event immediately after connection
- Reduced heartbeat interval from 30s to 15s for better connection stability
- Added detailed logging for tool registration and heartbeat counts
- Updated health endpoint version to "2.1.0-force-tools"

**Code Changes Summary**:
```python
# In initialize response:
"capabilities": {
    "tools": {
        "listChanged": True,
        "available": tools  # Tools included directly
    }
},
"tools": tools  # Also at root level

# In SSE stream:
- Send tools_available event immediately after connection
- Heartbeat every 15s instead of 30s
- Track heartbeat count for debugging
```

**Expected Behavior**:
- Claude should see tools immediately without calling tools/list
- SSE connection should be more stable with frequent heartbeats
- Tools should be available for use right after OAuth completion

**Testing in Progress**: Waiting for deployment (~10 minutes)

## Next Immediate Steps

1. **Deploy and Monitor** (IN PROGRESS)
   - Commit changes
   - Deploy to Azure
   - Monitor logs for tool registration

2. **If Solution 1 Fails - Try Solution 5** (Tool Pre-caching via SSE)
   - Send tool definitions as individual SSE events
   - Use different event types for each tool

3. **If Still Failing - Try WebSocket Transport**
   - Replace SSE with WebSocket for bidirectional communication
   - More control over connection lifecycle

## Known Issues & Workarounds

### Issue 1: Claude Never Calls tools/list
**Status**: Confirmed bug in Claude Enterprise
**Workaround**: Include tools in initialize response or send as SSE events

### Issue 2: SSE Connection Drops
**Status**: Under investigation
**Potential Causes**:
- Azure App Service timeout
- Missing keepalive events
- Claude.ai connection limits

### Issue 3: Random Port Redirects
**Status**: Expected behavior
**Solution**: Already handled with dynamic redirect URIs

## Resources
- [MCP Specification](https://modelcontextprotocol.io/docs)
- [Claude Enterprise MCP Docs](https://docs.anthropic.com/en/docs/integrations/mcp)
- [Azure App Service Logs](https://portal.azure.com/#view/WebsitesExtension/FunctionsIFrameBlade/id/%2Fsubscriptions%2F...)

---
*Last Updated: 2025-08-03*
*Next Test Scheduled: After implementing Solution 1*