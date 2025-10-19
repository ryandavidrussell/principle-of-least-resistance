# Ghost helper — safer reorganizations (2025-10-19)

This update improves the "Ghost" helper script used to reorganize repository files and optionally open a GitHub pull request.

Summary
- One-command repo reorg + optional PR creation
- Safer semantics, clearer diagnostics, and better automation behaviour

What's new
- --commit-message to customize commit text
- --preserve-paths to keep nested structure when a plan lists subpaths
- Better use of --repo when opening PRs with gh (ensures correct target)
- Improved dry-run output (concise plan + moved/skipped/error counts)
- Clearer error messages and surfaced command failures

Why
- Phone-friendly and one-command cleanup for reorg tasks
- Safer semantics and better diagnostics during automation

Notes
- Backwards compatible: default behavior and default plan unchanged
- Idempotent: already-correct files are skipped
- Requires git; gh (GitHub CLI) only needed if you want to open a PR automatically

