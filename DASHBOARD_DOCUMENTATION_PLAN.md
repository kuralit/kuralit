# Dashboard Documentation Update Plan

## Overview

This plan outlines the documentation updates needed before moving the Kuralit Dashboard (Kuralit-UI) to a separate repository. The goal is to ensure users are aware of the dashboard as an optional monitoring and debugging tool, with clear references to its separate repository location.

**Pre-Move Actions**: Copy relevant documentation files (LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md) to Kuralit-UI folder before moving to separate repository.

---

## Phase 1: Main Repository README Updates

### File: `README.md`

#### 1.1 Add Dashboard Section

**Location**: After "Flutter SDK" section (after line 208), before "Examples" section

**Content to Add**:

```markdown
### Kuralit Dashboard

The **Kuralit Dashboard** is a real-time monitoring and debugging tool for your AI Voice Agent servers. It provides:

- **Real-time Monitoring**: Watch conversations as they happen
- **Metrics Tracking**: Monitor messages, tool calls, errors, and latency
- **Debugging Tools**: Inspect conversation history and agent responses
- **Session Management**: View and manage active sessions

**Repository**: [kuralit-ui](https://github.com/kuralit/kuralit-ui) (separate repository)

**Documentation**: [Dashboard Guide →](docs/basics/sessions/dashboard)

> **Note**: The dashboard is an optional tool. The core SDKs work independently without it.
```

**Action Items**:
- [ ] Add dashboard section after Flutter SDK section
- [ ] Update repository URL once new repo is created
- [ ] Verify documentation link works after dashboard.mdx is created

---

## Phase 2: Documentation Site Updates

### 2.1 Update Navigation Structure

**File**: `docs/docs.json`

**Location**: Add Dashboard as a separate page under "Sessions" group in "Basics"

**Structure**:

```json
{
  "group": "Sessions",
  "pages": [
    "basics/sessions/index",
    "basics/sessions/session-management",
    "basics/sessions/conversation-history",
    "basics/sessions/multi-turn",
    "basics/sessions/dashboard"
  ]
}
```

**Action Items**:
- [ ] Update docs.json to add "basics/sessions/dashboard" to Sessions group
- [ ] Verify navigation appears correctly in Mintlify

### 2.2 Create Dashboard Documentation Page

**New File**: `docs/basics/sessions/dashboard.mdx`

**Content Structure**:

1. **Frontmatter**:
   ```yaml
   ---
   title: "Dashboard"
   description: "Real-time monitoring and debugging tool for Kuralit servers"
   ---
   ```

2. **Overview Section**:
   - What the dashboard is
   - Purpose: monitoring, debugging, metrics visualization
   - Separate repository (link to GitHub)
   - Optional tool (not required for SDK functionality)

3. **Features Section** (with CardGroup):
   - Real-time conversation monitoring
   - Metrics tracking (messages, tool calls, errors, latency)
   - Timeline viewer for conversation history
   - Session management view
   - Connection status monitoring

4. **Installation & Setup**:
   - Link to dashboard repository
   - Prerequisites (Node.js)
   - Installation commands
   - Environment configuration
   - Quick start commands

5. **Usage Guide**:
   - How to connect to a running server
   - Understanding the metrics display
   - Reading the timeline view
   - Interpreting connection status
   - Session selection and navigation

6. **Architecture**:
   - How it connects (WebSocket endpoint)
   - Event-driven updates
   - Data flow from server to dashboard
   - Optional: Simple diagram

7. **Screenshots/Examples**:
   - Dashboard interface overview (use `/logo/kuralit-dashboard.png`)
   - Metrics display
   - Timeline view
   - Connection status indicators
   
   **Screenshot Location**: `docs/logo/kuralit-dashboard.png` ✅ (verified)

8. **Troubleshooting**:
   - Connection issues
   - Missing data in dashboard
   - Real-time update problems
   - WebSocket connection failures

9. **Related Links**:
   - Dashboard repository: [kuralit-ui](https://github.com/kuralit/kuralit-ui)
   - GitHub issues
   - Related documentation (Python SDK, WebSocket server, Sessions)

10. **License**:
    - Dashboard uses the same licensing terms as the main Kuralit repository
    - Non-commercial license applies

**Action Items**:
- [ ] Create dashboard.mdx file at `docs/basics/sessions/dashboard.mdx`
- [ ] Write all sections with proper MDX formatting
- [ ] Add code examples for installation
- [ ] Add screenshot from `docs/logo/kuralit-dashboard.png` (path verified ✅)
- [ ] Include troubleshooting section
- [ ] Add link to dashboard repository: https://github.com/kuralit/kuralit-ui
- [ ] Mention licensing (same as main repo)

---

## Phase 3: Update Architecture Documentation

### File: `docs/getting-started/architecture.mdx`

#### 3.1 Add Dashboard Component

**Location**: After "AI Voice Agent Server" section (around line 40)

**Content to Add**:

```markdown
### Kuralit Dashboard (Optional)

The Kuralit Dashboard is an optional monitoring tool that provides real-time visibility into your AI Voice Agent server:

- **Real-time Monitoring**: Watch conversations and agent interactions as they happen
- **Metrics Dashboard**: Track server-wide and session-specific metrics
- **Debugging Interface**: Inspect conversation history and troubleshoot issues

The dashboard connects to your server via WebSocket and displays real-time updates without requiring server restarts.

**Learn more**: [Dashboard Documentation →](/basics/sessions/dashboard)
```

**Action Items**:
- [ ] Add dashboard section to architecture.mdx
- [ ] Ensure it's clear it's optional
- [ ] Add link to dashboard documentation
- [ ] Verify formatting matches existing style

---

## Phase 4: Update Development Documentation (Optional)

### File: `docs/development.mdx`

#### 4.1 Add Dashboard Development Section

**Location**: After existing content (after line 76)

**Content to Add**:

```markdown
## Using the Dashboard for Development

The Kuralit Dashboard is a valuable tool during development for monitoring and debugging your AI Voice Agent servers.

### Quick Setup

1. **Install the dashboard** from the [dashboard repository](https://github.com/kuralit/kuralit-dashboard)
2. **Start your server** with the Python SDK
3. **Connect the dashboard** to your server's WebSocket endpoint
4. **Monitor in real-time** as you test your agents

### Benefits for Development

- **Real-time Debugging**: See messages and responses as they happen
- **Metrics Monitoring**: Track performance and identify bottlenecks
- **Session Inspection**: Review conversation history and agent behavior
- **Error Tracking**: Quickly identify and debug issues

**Full Documentation**: [Dashboard Guide →](/basics/sessions/dashboard)
```

**Action Items**:
- [ ] Decide if this section is needed
- [ ] Add development section if approved
- [ ] Link to dashboard documentation

---

## Phase 5: Update Python SDK Documentation (Optional)

### File: `docs/python-sdk/index.mdx`

#### 5.1 Add Dashboard Reference

**Location**: In features or usage section

**Content to Add**:

```markdown
<Info>
  **Monitoring**: Use the [Kuralit Dashboard](/basics/sessions/dashboard) to monitor your server in real-time, track metrics, and debug conversations.
</Info>
```

**Action Items**:
- [ ] Decide if dashboard mention is needed in Python SDK docs
- [ ] Add info callout if approved
- [ ] Link to dashboard documentation

---

## Phase 6: Create Dashboard Quick Reference (Optional)

**Note**: This phase is optional. The main dashboard.mdx page can include a quick start section instead of a separate page.

**Decision**: Skip separate quickstart page - include quick start section in main dashboard.mdx

---

## Implementation Checklist

### Pre-Implementation
- [x] Confirm dashboard repository name and URL ✅
- [x] Decide on navigation placement (Sessions in Basics) ✅
- [x] Gather screenshots (docs/logo/kuralit-dashboard.png) ✅
- [x] Copy documentation files to Kuralit-UI ✅
  - [x] LICENSE
  - [x] SECURITY.md
  - [x] CONTRIBUTING.md
  - [x] CODE_OF_CONDUCT.md

### Phase 1: Main README
- [ ] Add dashboard section to README.md
- [ ] Update repository URL placeholder
- [ ] Verify markdown formatting
- [ ] Test documentation link (after Phase 2)

### Phase 2: Documentation Site
- [ ] Update docs.json navigation (add to Sessions group in Basics)
- [ ] Create dashboard.mdx file at `docs/basics/sessions/dashboard.mdx`
- [ ] Write all sections
- [ ] Add code examples
- [ ] Add screenshot from `docs/logo/kuralit-dashboard.png`
- [ ] Test locally with `mint dev`
- [ ] Verify all links work

### Phase 3: Architecture Docs
- [ ] Add dashboard section to architecture.mdx
- [ ] Verify formatting consistency
- [ ] Test link to dashboard docs

### Phase 4: Development Docs (Optional)
- [ ] Add development section if approved
- [ ] Link to dashboard docs

### Phase 5: Python SDK Docs (Optional)
- [ ] Add dashboard reference if approved
- [ ] Link to dashboard docs

### Phase 6: Quick Reference (Optional)
- [ ] Skip - include quick start in main dashboard.mdx instead

### Final Review
- [ ] Review all documentation for consistency
- [ ] Verify all links work
- [ ] Check spelling and grammar
- [ ] Test navigation structure
- [ ] Preview in Mintlify locally
- [ ] Get approval before merging

---

## Key Points to Emphasize

1. **Separate Repository**: Dashboard is in its own repository (not in main SDK repo)
2. **Optional Tool**: Not required for SDK functionality - core SDKs work independently
3. **Development Tool**: Primarily for monitoring and debugging during development
4. **Real-time**: Emphasize real-time monitoring capabilities
5. **License**: Same licensing terms as main repository

---

## Content Guidelines

### Terminology
- Use "Kuralit Dashboard" or "Dashboard" consistently
- Refer to it as an "optional tool" or "monitoring tool"
- Avoid calling it a "requirement" or "dependency"

### Tone
- Clear and concise
- Developer-focused
- Emphasize benefits without overselling
- Be honest about it being optional

### Links
- Always use relative links for documentation pages: `/additional-features/dashboard`
- Use absolute URLs for external links (GitHub repository)
- Test all links before finalizing

### Formatting
- Use MDX components (CardGroup, Card, Info, etc.) where appropriate
- Follow existing documentation style
- Include code examples with proper syntax highlighting
- Use proper heading hierarchy

---

## Questions - RESOLVED ✅

1. **Repository Name**: `kuralit-ui` ✅
   - Repository folder: `Kuralit-UI`

2. **Repository URL**: `https://github.com/kuralit/kuralit-ui` ✅

3. **License**: Same licensing terms as main repository ✅
   - Non-commercial license applies
   - LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md copied to Kuralit-UI

4. **Screenshots**: Available at `docs/logo/kuralit-dashboard.png` ✅
   - Dashboard interface screenshot included

5. **Placement**: Under "Sessions" group in "Basics" section ✅
   - File location: `docs/basics/sessions/dashboard.mdx`
   - Navigation: Add to Sessions group pages array

6. **Quickstart Page**: Not needed - include quick start section in main dashboard.mdx ✅

---

## Timeline Estimate

- **Phase 1** (README): 15-30 minutes
- **Phase 2** (Documentation): 1-2 hours
- **Phase 3** (Architecture): 15-30 minutes
- **Phase 4** (Development - Optional): 15-30 minutes
- **Phase 5** (Python SDK - Optional): 15 minutes
- **Phase 6** (Quickstart - Optional): 30 minutes

**Total Estimated Time**: 2-4 hours (depending on optional sections)

---

## Next Steps

1. ✅ **Questions resolved** - All questions answered
2. ✅ **Documentation files copied** - LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md added to Kuralit-UI
3. **Get approval** to proceed with implementation
4. **Implement phases** in order:
   - Phase 1: Update README.md
   - Phase 2: Create dashboard.mdx and update docs.json
   - Phase 3: Update architecture.mdx
   - Phase 4-6: Optional enhancements
4. **Review and test** all changes
5. **Merge documentation** updates
6. **Move dashboard** to separate repository (kuralit-ui) - documentation files already included
7. **Verify all links** work after repository move

---

## Notes

- All documentation should be updated **before** moving the dashboard to a separate repository
- This ensures users have references to the dashboard even after the move
- Links can be updated after the repository is created if the URL is different
- Keep documentation concise - detailed setup instructions should be in the dashboard repository's README

---

**Last Updated**: [Date]
**Status**: Planning Phase
**Next Review**: After questions are resolved

