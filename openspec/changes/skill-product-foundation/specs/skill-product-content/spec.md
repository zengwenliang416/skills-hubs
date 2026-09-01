## ADDED Requirements

### Requirement: Catalog provides decision-ready Skill content
The catalog MUST provide a factual Chinese description, tags, highlights, use
cases, install methods, documentation URL, and repository URL for every Skill.

#### Scenario: Complete catalog entry
- **WHEN** the frontend loads a current Skill entry
- **THEN** all decision and navigation fields are available without another content request

#### Scenario: Unsupported installation method
- **WHEN** current Skill documentation does not provide an executable install command
- **THEN** the catalog describes the supported manual method without inventing a command

### Requirement: One complete detail experience serves every entry path
The frontend SHALL use one Skill detail component for catalog, featured, and
command-palette entry paths.

#### Scenario: Open from catalog
- **WHEN** a visitor opens a Skill from the catalog grid
- **THEN** the complete description, tags, highlights, use cases, metadata, install methods, documentation, and source actions are shown

#### Scenario: Open from command palette
- **WHEN** a visitor selects the same Skill from the command palette
- **THEN** the same complete detail component and content are shown

### Requirement: Supported install commands can be copied
The detail experience SHALL allow copying each install method that contains a
command and MUST provide accessible success or failure feedback.

#### Scenario: Successful install copy
- **WHEN** the clipboard operation succeeds
- **THEN** the selected command is copied and visible plus assistive status feedback says it succeeded

#### Scenario: Manual-only install method
- **WHEN** an install method contains guidance but no command
- **THEN** the guidance is displayed without a nonfunctional copy control

### Requirement: Documentation and source actions remain reliable
The detail experience SHALL provide named external links for official
documentation and the Skill source directory.

#### Scenario: Analytics unavailable during outbound navigation
- **WHEN** behavior reporting fails while a visitor activates an outbound link
- **THEN** the requested destination still opens

### Requirement: Detail UI preserves existing experience contracts
The expanded detail MUST remain responsive, theme-compatible, keyboard and
touch accessible, and reduced-motion safe.

#### Scenario: Narrow viewport
- **WHEN** the detail is opened at a 320px viewport
- **THEN** its content remains readable and operable without page-level horizontal overflow

#### Scenario: Reduced motion
- **WHEN** the visitor requests reduced motion
- **THEN** all content and controls remain available without non-essential animation
