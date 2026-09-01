## ADDED Requirements

### Requirement: Backend accepts only fixed Skill events
The backend MUST accept only `skill_view`, `install_copy`,
`documentation_click`, and `repository_click` for Skill names present in the
current catalog.

#### Scenario: Valid event
- **WHEN** a request contains a fixed event and current catalog Skill name
- **THEN** the backend records the action and returns HTTP 204

#### Scenario: Unknown event or Skill
- **WHEN** a request contains an unknown event type or Skill name
- **THEN** the backend returns HTTP 400 and does not write an event row

#### Scenario: Unexpected request field
- **WHEN** an event request contains a field outside the fixed schema
- **THEN** the backend returns HTTP 400

### Requirement: Behavior data uses daily IP aggregation
The backend MUST resolve the visitor IP using the existing proxy policy and
aggregate behavior by UTC date, IP, Skill, and event type.

#### Scenario: Repeated daily action
- **WHEN** the same IP performs the same Skill action twice on one UTC date
- **THEN** one database row remains and its `event_count` is two

#### Scenario: Different visitor
- **WHEN** two IPs perform the same Skill action
- **THEN** aggregate totals include both actions and unique visitors equals two

#### Scenario: Forged forwarding header in direct mode
- **WHEN** proxy trust is disabled and a client sends forwarding headers
- **THEN** the TCP peer IP is used

### Requirement: Migration preserves valid visitor statistics
The database migration from schema v2 to v3 MUST retain `daily_visits` and add
the Skill event entity.

#### Scenario: Open a schema v2 database
- **WHEN** the v3 server opens a database containing valid v2 IP visit rows
- **THEN** those visit rows remain queryable and the event table is available

### Requirement: Metrics expose aggregates without raw IP
The metrics API SHALL return one aggregate engagement item per catalog Skill and
MUST NOT return visitor IP values.

#### Scenario: Skill has no events
- **WHEN** a catalog Skill has no stored event row
- **THEN** its views, copies, outbound clicks, and unique visitor counts are zero

#### Scenario: Skill has events
- **WHEN** stored events exist for a catalog Skill
- **THEN** the response contains total counts by fixed event type and distinct interested visitors

### Requirement: Frontend reports behavior without blocking actions
The frontend SHALL report the four events as best-effort side effects and MUST
not wait before opening details, showing copy feedback, or navigating.

#### Scenario: Event endpoint unavailable
- **WHEN** the endpoint fails during a primary interaction
- **THEN** the primary interaction completes and no blocking analytics error is shown

### Requirement: npm availability is represented accurately
The metrics UI MUST distinguish complete npm data from partial or unavailable
package data.

#### Scenario: One npm package is unavailable
- **WHEN** at least one package has `downloads: null`
- **THEN** the total is labeled as partial and the missing package is not presented as a confirmed zero
