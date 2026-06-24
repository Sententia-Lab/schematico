---
name: Bug report
about: Something isn't working the way you expected
title: "[Bug] "
labels: bug
---

**What happened?**
A clear description of the bug.

**What did you expect to happen?**

**Steps to reproduce**
1. ...
2. ...

If it helps, include the schema you used and the exact command:

```json
{ "table": "...", "fields": [ ... ] }
```

```bash
schematico discover ...
```

**Environment**
- schematico version: <!-- pip show schematico -->
- Python version:
- OS:
- Mode: generate / discover
- Model: <!-- e.g. gateway/anthropic:claude-sonnet-4-6 -->

**Logs**
Re-run with `LOG_LEVEL=DEBUG` and paste any relevant output (redact API keys!).
