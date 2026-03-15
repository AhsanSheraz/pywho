# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email [ahsansheraz@gmail.com](mailto:ahsansheraz@gmail.com) with details.
3. Include steps to reproduce, if possible.

You can expect an initial response within 48 hours. Once confirmed, a fix will be released as a patch version as soon as possible.

## Scope

pywho is a read-only diagnostic tool that:
- Does **not** execute arbitrary code
- Does **not** modify the filesystem
- Does **not** make network requests
- Uses only Python stdlib modules (zero dependencies)

The primary risk surface is limited to information disclosure (environment details displayed in terminal output).
