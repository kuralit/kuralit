# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Disclose Publicly

**Please do not** report security vulnerabilities through public GitHub issues, discussions, or any other public channels.

### 2. Report Privately

Send an email to **hello@kuralit.com** with the following information:

- **Subject**: `[SECURITY] Brief description of the vulnerability`
- **Description**: Detailed description of the vulnerability
- **Impact**: Potential impact and severity
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Proof of Concept**: If available, include a proof of concept
- **Suggested Fix**: If you have ideas for a fix, please include them

### 3. What to Include

Your report should include:

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Affected component (Python SDK, Flutter SDK, server, client, etc.)
- Version information
- Steps to reproduce
- Potential impact
- Any additional context

### 4. Response Timeline

We will acknowledge receipt of your report within **48 hours** and provide an initial assessment within **7 days**. We will keep you informed of our progress and work with you to understand and resolve the issue.

### 5. Disclosure Policy

- We will work with you to fix the vulnerability
- We will credit you for the discovery (unless you prefer to remain anonymous)
- We will coordinate public disclosure after a fix is available
- We will not disclose your identity without your permission

## Security Best Practices

### For Users

1. **Keep Dependencies Updated**
   - Regularly update the Kuralit SDKs
   - Keep Python, Flutter, and other dependencies up to date
   - Monitor for security advisories

2. **API Keys and Credentials**
   - Never commit API keys or credentials to version control
   - Use environment variables or secure configuration management
   - Rotate keys regularly
   - Use different keys for development and production

3. **Network Security**
   - Use HTTPS/WSS for all connections in production
   - Validate SSL certificates
   - Implement proper authentication and authorization
   - Use API key validation on the server side

4. **Input Validation**
   - Validate and sanitize all user inputs
   - Use parameterized queries if using databases
   - Implement rate limiting where appropriate

5. **Error Handling**
   - Don't expose sensitive information in error messages
   - Log errors securely without exposing user data
   - Implement proper error handling and recovery

### For Developers

1. **Code Security**
   - Follow secure coding practices
   - Use type hints and validation (Pydantic for Python)
   - Avoid hardcoded secrets or credentials
   - Implement proper authentication and authorization

2. **Dependencies**
   - Regularly audit dependencies for vulnerabilities
   - Use tools like `pip-audit` or `safety` for Python
   - Keep dependencies up to date
   - Remove unused dependencies

3. **Testing**
   - Write security-focused tests
   - Test for common vulnerabilities (OWASP Top 10)
   - Perform security code reviews
   - Use static analysis tools

4. **Documentation**
   - Document security considerations
   - Provide security examples
   - Warn about common pitfalls

## Known Security Considerations

### WebSocket Security

- Always use WSS (WebSocket Secure) in production
- Implement proper authentication before allowing connections
- Validate API keys on the server
- Implement rate limiting to prevent abuse

### API Key Management

- API keys should be validated on every request
- Use strong, randomly generated API keys
- Implement key rotation policies
- Never expose API keys in client-side code

### Audio Data

- Audio data may contain sensitive information
- Ensure secure transmission (WSS)
- Consider encryption for sensitive audio data
- Implement proper data retention policies

### Tool Execution

- Tools can execute external code or make API calls
- Validate and sanitize tool inputs
- Implement timeouts for tool execution
- Monitor and log tool executions
- Restrict tool access based on user permissions

## Security Updates

Security updates will be released as:

- **Patch versions** (e.g., 0.1.0 → 0.1.1) for critical security fixes
- **Minor versions** (e.g., 0.1.0 → 0.2.0) for security improvements
- **Security advisories** will be published for significant vulnerabilities

## Security Acknowledgments

We would like to thank the following individuals and organizations for responsibly disclosing security vulnerabilities:

(To be updated as vulnerabilities are reported and fixed)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security.html)
- [Flutter Security](https://docs.flutter.dev/security)
- [WebSocket Security](https://datatracker.ietf.org/doc/html/rfc6455#section-10)

## Contact

For security-related inquiries:

- **Email**: hello@kuralit.com
- **Subject Prefix**: `[SECURITY]` for security issues

For general support and questions, please use GitHub Issues or Discussions.

---

**Thank you for helping keep Kuralit secure!**

