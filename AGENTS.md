# Repository Guidelines

## Structure

- Put each self-contained Skill under `skills/<skill-name>/`.
- Keep runtime code, `SKILL.md`, references, tests, security policy, metadata,
  and the Skill-specific `LICENSE` together.
- Update the root `README.md` and `catalog.json` when adding or removing a Skill.

## Public Release Safety

- Never commit credentials, cookies, private communications, `.env` files, or
  machine-specific authentication material.
- Exclude generated images, caches, review reports, local build archives, and
  absolute paths that identify a private workstation.
- Preserve each Skill's existing license. Do not apply a repository-wide
  license or change a Skill's license without explicit owner approval.

## Validation

- Run the closest Skill-specific tests before committing.
- Run a credential-pattern scan over staged files.
- For npm-distributed Skills, run `npm pack --dry-run --json` and verify the
  file allowlist before publishing.
