PRAGMA secure_delete = ON;

BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS daily_skill_events (
    event_date TEXT NOT NULL,
    visitor_ip TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'skill_view',
            'install_copy',
            'documentation_click',
            'repository_click'
        )
    ),
    event_count INTEGER NOT NULL DEFAULT 1 CHECK (event_count > 0),
    PRIMARY KEY (event_date, visitor_ip, skill_name, event_type)
);

CREATE INDEX IF NOT EXISTS idx_daily_skill_events_skill_type
    ON daily_skill_events (skill_name, event_type);

PRAGMA user_version = 3;

COMMIT;
