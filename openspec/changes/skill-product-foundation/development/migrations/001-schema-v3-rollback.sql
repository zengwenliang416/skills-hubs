BEGIN IMMEDIATE;

DROP INDEX IF EXISTS idx_daily_skill_events_skill_type;
DROP TABLE IF EXISTS daily_skill_events;

PRAGMA user_version = 2;

COMMIT;
