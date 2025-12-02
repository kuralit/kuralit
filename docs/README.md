# KuralIt Documentation

This directory contains the source files for the KuralIt documentation site, built with [Mintlify](https://mintlify.com).

## Documentation Structure

The documentation is organized into the following main sections:

### Getting Started
- Introduction to KuralIt
- Quickstart guides for Python and Flutter SDKs
- Architecture overview
- Configuration guides
- Feature overview

### Basics
- **Agents**: Creating agents, instructions, and context management
- **Tools**: Function calling, custom functions, REST API tools, and toolkits
- **Voice**: Speech-to-text, voice activity detection, turn detection, and audio streaming
- **Sessions**: Session management, conversation history, and multi-turn conversations

### Additional Features
- Protocol details
- Streaming capabilities
- Error handling
- Connection management
- State management

### Integrations
- **Model Providers**: LLM integrations (Gemini, etc.)
- **STT Providers**: Speech-to-text providers (Deepgram, Google Cloud Speech)
- **VAD Providers**: Voice activity detection (Silero)
- **Turn Detection Providers**: Turn detection models (Multilingual)

### SDK Documentation
- **Python SDK**: API reference, guides, examples, and plugins
- **Flutter SDK**: API reference, guides, examples, and templates

### Help
- Installation and setup
- Configuration help
- Troubleshooting
- FAQ

## Development

### Prerequisites

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview your documentation changes locally:

```bash
npm i -g mint
```

### Running Locally

Run the following command at the root of the documentation directory (where `docs.json` is located):

```bash
mint dev
```

View your local preview at `http://localhost:3000`.

### Updating Documentation

1. **Edit MDX files**: Documentation pages are written in MDX format (Markdown with JSX)
2. **Update navigation**: Edit `docs.json` to add, remove, or reorganize pages
3. **Preview changes**: Run `mint dev` to see changes in real-time
4. **Commit changes**: Commit and push to trigger automatic deployment

## Configuration

The documentation is configured via `docs.json`, which includes:

- **Theme settings**: Colors, logo, favicon
- **Navigation structure**: All pages and their organization
- **Contextual options**: AI assistant integrations (ChatGPT, Claude, etc.)
- **Footer links**: Social media and external links

## Publishing

### Automatic Deployment

Changes are automatically deployed to production after pushing to the default branch. This is handled by the Mintlify GitHub App, which should be installed from your [Mintlify dashboard](https://dashboard.mintlify.com/settings/organization/github-app).

### Manual Deployment

If needed, you can manually trigger deployment from the Mintlify dashboard.

## Contributing to Documentation

We welcome contributions to improve the documentation! Here's how you can help:

### Reporting Issues

If you find errors, unclear explanations, or missing information:

1. Open an issue on GitHub describing the problem
2. Include the page URL and section
3. Suggest improvements if you have ideas

### Submitting Changes

1. **Fork the repository**
2. **Create a branch** for your changes:
   ```bash
   git checkout -b docs/your-change-name
   ```
3. **Make your edits** to the relevant MDX files
4. **Test locally** using `mint dev`
5. **Commit and push** your changes
6. **Open a pull request** with a clear description

### Documentation Guidelines

- **Be clear and concise**: Write for developers who may be new to the framework
- **Include examples**: Code examples help users understand concepts quickly
- **Keep it up to date**: Update docs when features change
- **Use proper formatting**: Follow Markdown best practices
- **Add screenshots**: Visual aids help explain UI components and workflows

### Common Tasks

#### Adding a New Page

1. Create a new `.mdx` file in the appropriate directory
2. Add the page to `docs.json` in the navigation structure
3. Follow the existing page structure and formatting

#### Updating Navigation

Edit the `navigation` section in `docs.json` to:
- Add new pages
- Reorganize sections
- Update page titles or descriptions

#### Adding Code Examples

Use code blocks with language specification:

````markdown
```python
from kuralit.server import create_app
# Your code here
```
````

## File Structure

```
docs/
├── docs.json              # Main configuration file
├── README.md              # This file
├── getting-started/       # Introduction and quickstart guides
├── basics/                # Core concepts (agents, tools, voice, sessions)
├── additional-features/   # Advanced features
├── integrations/         # Provider integrations
├── python-sdk/           # Python SDK documentation
├── flutter-sdk/          # Flutter SDK documentation
├── help/                 # Help and troubleshooting
├── images/               # Images and diagrams
└── logo/                 # Logo files
```

## Troubleshooting

### Dev Environment Issues

If your dev environment isn't running:

```bash
mint update
```

This ensures you have the most recent version of the CLI.

### 404 Errors

If a page loads as a 404:
- Make sure you are running `mint dev` in the folder with `docs.json`
- Verify the page path in `docs.json` matches the file location
- Check that the file extension is `.mdx` (not `.md`)

### Build Errors

- Check that all referenced pages exist
- Verify `docs.json` syntax is valid JSON
- Ensure image paths are correct

## Resources

- [Mintlify Documentation](https://mintlify.com/docs)
- [Mintlify Components](https://mintlify.com/docs/components)
- [MDX Guide](https://mdxjs.com/docs/)

## Support

For documentation-related questions or issues:

- **GitHub Issues**: [Open an issue](https://github.com/kuralit/kuralit/issues)
- **Email**: hello@kuralit.com
- **Discord**: [Join our Discord](https://discord.gg/xjv54fex)

---

**Note**: This documentation is continuously updated. If you notice something outdated or incorrect, please help us improve it by submitting a pull request or opening an issue.
