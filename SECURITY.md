# Security policy

The MVP does not execute generated Python and rejects remote data URLs. Future code-execution features must use an isolated subprocess or container with no network by default, read-only inputs, dependency allowlists, time limits, memory limits, and captured artifacts. Never add a bare `exec()` or `eval()` path.

Report suspected credential exposure or unsafe execution privately to the repository owner before opening a public issue.
