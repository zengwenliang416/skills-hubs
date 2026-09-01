use std::{
    collections::HashMap,
    fs,
    path::Path,
    sync::{Arc, Mutex, MutexGuard},
    time::Duration,
};

use anyhow::{Context, Result, anyhow};
use chrono::{Duration as ChronoDuration, NaiveDate};
use rusqlite::{Connection, params};
#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

use crate::model::{DailyVisitors, SkillEngagement, SkillEventType};

const SCHEMA_VERSION: i64 = 3;

#[derive(Clone)]
pub struct Store {
    connection: Arc<Mutex<Connection>>,
}

#[derive(Debug)]
pub struct StoreMetrics {
    pub total_visitors: u64,
    pub today_visitors: u64,
    pub total_page_views: u64,
    pub daily_visitors: Vec<DailyVisitors>,
    pub skill_engagement: Vec<SkillEngagement>,
}

impl Store {
    pub fn open(path: &Path) -> Result<Self> {
        if let Some(parent) = path
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        {
            fs::create_dir_all(parent).with_context(|| {
                format!("failed to create database directory {}", parent.display())
            })?;
        }

        let connection = Connection::open(path)
            .with_context(|| format!("failed to open database {}", path.display()))?;
        #[cfg(unix)]
        fs::set_permissions(path, fs::Permissions::from_mode(0o600))
            .with_context(|| format!("failed to secure database {}", path.display()))?;
        Self::from_connection(connection)
    }

    #[cfg(test)]
    fn open_in_memory() -> Result<Self> {
        Self::from_connection(Connection::open_in_memory()?)
    }

    fn from_connection(connection: Connection) -> Result<Self> {
        connection.busy_timeout(Duration::from_secs(5))?;
        connection.pragma_update(None, "journal_mode", "WAL")?;
        connection.pragma_update(None, "secure_delete", "ON")?;

        let schema_version =
            connection.pragma_query_value(None, "user_version", |row| row.get::<_, i64>(0))?;
        if schema_version > SCHEMA_VERSION {
            return Err(anyhow!(
                "database schema version {schema_version} is newer than supported version {SCHEMA_VERSION}"
            ));
        }
        if schema_version < 2 {
            connection.execute_batch(
                "
                DROP TABLE IF EXISTS daily_visits;
                CREATE TABLE daily_visits (
                    visit_date TEXT NOT NULL,
                    visitor_ip TEXT NOT NULL,
                    page_views INTEGER NOT NULL DEFAULT 1 CHECK (page_views > 0),
                    PRIMARY KEY (visit_date, visitor_ip)
                );
                CREATE INDEX idx_daily_visits_ip
                    ON daily_visits (visitor_ip);
                ",
            )?;
        }
        connection.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS daily_visits (
                visit_date TEXT NOT NULL,
                visitor_ip TEXT NOT NULL,
                page_views INTEGER NOT NULL DEFAULT 1 CHECK (page_views > 0),
                PRIMARY KEY (visit_date, visitor_ip)
            );
            CREATE INDEX IF NOT EXISTS idx_daily_visits_ip
                ON daily_visits (visitor_ip);
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
            ",
        )?;

        Ok(Self {
            connection: Arc::new(Mutex::new(connection)),
        })
    }

    pub fn record_visit(&self, date: NaiveDate, visitor_ip: &str) -> Result<()> {
        let connection = self.connection()?;
        connection.execute(
            "
            INSERT INTO daily_visits (visit_date, visitor_ip, page_views)
            VALUES (?1, ?2, 1)
            ON CONFLICT (visit_date, visitor_ip)
            DO UPDATE SET page_views = page_views + 1
            ",
            params![date.to_string(), visitor_ip],
        )?;
        Ok(())
    }

    pub fn record_skill_event(
        &self,
        date: NaiveDate,
        visitor_ip: &str,
        skill_name: &str,
        event_type: SkillEventType,
    ) -> Result<()> {
        let connection = self.connection()?;
        connection.execute(
            "
            INSERT INTO daily_skill_events (
                event_date,
                visitor_ip,
                skill_name,
                event_type,
                event_count
            )
            VALUES (?1, ?2, ?3, ?4, 1)
            ON CONFLICT (event_date, visitor_ip, skill_name, event_type)
            DO UPDATE SET event_count = event_count + 1
            ",
            params![
                date.to_string(),
                visitor_ip,
                skill_name,
                event_type.as_str()
            ],
        )?;
        Ok(())
    }

    pub fn prune_before(&self, cutoff: NaiveDate) -> Result<()> {
        let mut connection = self.connection()?;
        let transaction = connection.transaction()?;
        transaction.execute(
            "DELETE FROM daily_visits WHERE visit_date < ?1",
            params![cutoff.to_string()],
        )?;
        transaction.execute(
            "DELETE FROM daily_skill_events WHERE event_date < ?1",
            params![cutoff.to_string()],
        )?;
        transaction.commit()?;
        let (busy, log_frames, checkpointed_frames) =
            connection.query_row("PRAGMA wal_checkpoint(TRUNCATE)", [], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, i64>(2)?,
                ))
            })?;
        if busy != 0 {
            return Err(anyhow!(
                "WAL truncate checkpoint remained busy: {checkpointed_frames}/{log_frames} frames checkpointed"
            ));
        }
        Ok(())
    }

    pub fn metrics(&self, today: NaiveDate, skill_names: &[String]) -> Result<StoreMetrics> {
        let start = today - ChronoDuration::days(6);
        let connection = self.connection()?;

        let total_visitors = query_count(
            &connection,
            "SELECT COUNT(DISTINCT visitor_ip) FROM daily_visits",
            [],
        )?;
        let today_visitors = query_count(
            &connection,
            "SELECT COUNT(*) FROM daily_visits WHERE visit_date = ?1",
            params![today.to_string()],
        )?;
        let total_page_views = query_count(
            &connection,
            "SELECT COALESCE(SUM(page_views), 0) FROM daily_visits",
            [],
        )?;

        let mut statement = connection.prepare(
            "
            SELECT visit_date, COUNT(*)
            FROM daily_visits
            WHERE visit_date BETWEEN ?1 AND ?2
            GROUP BY visit_date
            ",
        )?;
        let rows = statement.query_map(params![start.to_string(), today.to_string()], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?))
        })?;

        let mut counts = HashMap::new();
        for row in rows {
            let (date, visitors) = row?;
            counts.insert(date, to_u64(visitors)?);
        }

        let daily_visitors = (0..7)
            .map(|offset| start + ChronoDuration::days(offset))
            .map(|date| {
                let date = date.to_string();
                let visitors = counts.get(&date).copied().unwrap_or_default();
                DailyVisitors { date, visitors }
            })
            .collect();

        let mut statement = connection.prepare(
            "
            SELECT
                skill_name,
                COUNT(DISTINCT visitor_ip),
                COALESCE(SUM(CASE WHEN event_type = 'skill_view' THEN event_count ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN event_type = 'install_copy' THEN event_count ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN event_type = 'documentation_click' THEN event_count ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN event_type = 'repository_click' THEN event_count ELSE 0 END), 0)
            FROM daily_skill_events
            GROUP BY skill_name
            ",
        )?;
        let rows = statement.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, i64>(2)?,
                row.get::<_, i64>(3)?,
                row.get::<_, i64>(4)?,
                row.get::<_, i64>(5)?,
            ))
        })?;
        let mut engagement_by_skill = HashMap::new();
        for row in rows {
            let (
                skill_name,
                unique_visitors,
                views,
                install_copies,
                documentation_clicks,
                repository_clicks,
            ) = row?;
            engagement_by_skill.insert(
                skill_name.clone(),
                SkillEngagement {
                    skill_name,
                    unique_visitors: to_u64(unique_visitors)?,
                    views: to_u64(views)?,
                    install_copies: to_u64(install_copies)?,
                    documentation_clicks: to_u64(documentation_clicks)?,
                    repository_clicks: to_u64(repository_clicks)?,
                },
            );
        }
        let skill_engagement = skill_names
            .iter()
            .map(|skill_name| {
                engagement_by_skill
                    .remove(skill_name)
                    .unwrap_or_else(|| SkillEngagement {
                        skill_name: skill_name.clone(),
                        unique_visitors: 0,
                        views: 0,
                        install_copies: 0,
                        documentation_clicks: 0,
                        repository_clicks: 0,
                    })
            })
            .collect();

        Ok(StoreMetrics {
            total_visitors,
            today_visitors,
            total_page_views,
            daily_visitors,
            skill_engagement,
        })
    }

    fn connection(&self) -> Result<MutexGuard<'_, Connection>> {
        self.connection
            .lock()
            .map_err(|_| anyhow!("database connection lock is poisoned"))
    }
}

fn query_count<P>(connection: &Connection, sql: &str, params: P) -> Result<u64>
where
    P: rusqlite::Params,
{
    let value = connection.query_row(sql, params, |row| row.get::<_, i64>(0))?;
    to_u64(value)
}

fn to_u64(value: i64) -> Result<u64> {
    u64::try_from(value).map_err(|_| anyhow!("database returned a negative aggregate"))
}

#[cfg(test)]
mod tests {
    use std::{
        fs, process,
        time::{SystemTime, UNIX_EPOCH},
    };

    use chrono::NaiveDate;
    use rusqlite::Connection;

    use crate::model::SkillEventType;

    use super::Store;

    fn skill_names() -> Vec<String> {
        vec!["image-api-workbench".to_owned(), "manual-skill".to_owned()]
    }

    fn temporary_database_path() -> std::path::PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system time after epoch")
            .as_nanos();
        std::env::temp_dir().join(format!(
            "skills-hub-checkpoint-{}-{unique}.sqlite3",
            process::id()
        ))
    }

    fn remove_database_files(path: &std::path::Path) {
        for suffix in ["", "-wal", "-shm"] {
            let file_name = format!(
                "{}{suffix}",
                path.file_name()
                    .expect("database file name")
                    .to_string_lossy()
            );
            let _ = fs::remove_file(path.with_file_name(file_name));
        }
    }

    #[test]
    fn repeat_visit_counts_once_as_visitor_and_each_time_as_page_view() {
        let store = Store::open_in_memory().expect("open in-memory database");
        let today = NaiveDate::from_ymd_opt(2026, 8, 31).expect("valid date");

        store
            .record_visit(today, "11111111-1111-4111-8111-111111111111")
            .expect("record first visit");
        store
            .record_visit(today, "11111111-1111-4111-8111-111111111111")
            .expect("record repeat visit");
        store
            .record_visit(today, "22222222-2222-4222-8222-222222222222")
            .expect("record second visitor");

        let metrics = store.metrics(today, &skill_names()).expect("load metrics");
        assert_eq!(metrics.total_visitors, 2);
        assert_eq!(metrics.today_visitors, 2);
        assert_eq!(metrics.total_page_views, 3);
        assert_eq!(metrics.daily_visitors.last().unwrap().visitors, 2);
    }

    #[test]
    fn legacy_uuid_schema_is_rebuilt_for_ip_storage() {
        let connection = Connection::open_in_memory().expect("open in-memory database");
        connection
            .execute_batch(
                "
                CREATE TABLE daily_visits (
                    visit_date TEXT NOT NULL,
                    visitor_id TEXT NOT NULL,
                    page_views INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (visit_date, visitor_id)
                );
                INSERT INTO daily_visits (visit_date, visitor_id, page_views)
                VALUES ('2026-08-31', 'legacy-id', 3);
                ",
            )
            .expect("create legacy schema");

        let store = Store::from_connection(connection).expect("migrate legacy schema");
        let today = NaiveDate::from_ymd_opt(2026, 9, 1).expect("valid date");
        let metrics = store
            .metrics(today, &skill_names())
            .expect("load migrated metrics");
        assert_eq!(metrics.total_visitors, 0);
        assert_eq!(metrics.total_page_views, 0);

        store
            .record_visit(today, "203.0.113.10")
            .expect("record IP after migration");
        let metrics = store
            .metrics(today, &skill_names())
            .expect("load IP metrics");
        assert_eq!(metrics.total_visitors, 1);
    }

    #[test]
    fn recent_daily_visitors_contains_seven_days_and_fills_missing_days() {
        let store = Store::open_in_memory().expect("open in-memory database");
        let today = NaiveDate::from_ymd_opt(2026, 8, 31).expect("valid date");

        store
            .record_visit(
                today - chrono::Duration::days(2),
                "11111111-1111-4111-8111-111111111111",
            )
            .expect("record earlier visit");
        store
            .record_visit(today, "22222222-2222-4222-8222-222222222222")
            .expect("record today's visit");

        let metrics = store.metrics(today, &skill_names()).expect("load metrics");
        let days: Vec<_> = metrics
            .daily_visitors
            .iter()
            .map(|item| (item.date.as_str(), item.visitors))
            .collect();

        assert_eq!(
            days,
            vec![
                ("2026-08-25", 0),
                ("2026-08-26", 0),
                ("2026-08-27", 0),
                ("2026-08-28", 0),
                ("2026-08-29", 1),
                ("2026-08-30", 0),
                ("2026-08-31", 1),
            ]
        );
    }

    #[test]
    fn schema_v2_visit_data_is_preserved_when_events_are_added() {
        let connection = Connection::open_in_memory().expect("open in-memory database");
        connection
            .execute_batch(
                "
                CREATE TABLE daily_visits (
                    visit_date TEXT NOT NULL,
                    visitor_ip TEXT NOT NULL,
                    page_views INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (visit_date, visitor_ip)
                );
                INSERT INTO daily_visits (visit_date, visitor_ip, page_views)
                VALUES ('2026-09-01', '203.0.113.10', 4);
                PRAGMA user_version = 2;
                ",
            )
            .expect("create v2 schema");

        let store = Store::from_connection(connection).expect("migrate v2 schema");
        let today = NaiveDate::from_ymd_opt(2026, 9, 1).expect("valid date");
        let metrics = store.metrics(today, &skill_names()).expect("load metrics");

        assert_eq!(metrics.total_visitors, 1);
        assert_eq!(metrics.total_page_views, 4);
        assert_eq!(metrics.skill_engagement.len(), 2);
    }

    #[test]
    fn skill_events_aggregate_counts_and_unique_visitors() {
        let store = Store::open_in_memory().expect("open in-memory database");
        let today = NaiveDate::from_ymd_opt(2026, 9, 1).expect("valid date");

        store
            .record_skill_event(
                today,
                "203.0.113.10",
                "image-api-workbench",
                SkillEventType::SkillView,
            )
            .expect("record first view");
        store
            .record_skill_event(
                today,
                "203.0.113.10",
                "image-api-workbench",
                SkillEventType::SkillView,
            )
            .expect("record repeated view");
        store
            .record_skill_event(
                today,
                "198.51.100.7",
                "image-api-workbench",
                SkillEventType::InstallCopy,
            )
            .expect("record install copy");

        let metrics = store.metrics(today, &skill_names()).expect("load metrics");
        let image = &metrics.skill_engagement[0];
        let manual = &metrics.skill_engagement[1];

        assert_eq!(image.unique_visitors, 2);
        assert_eq!(image.views, 2);
        assert_eq!(image.install_copies, 1);
        assert_eq!(manual.unique_visitors, 0);
    }

    #[test]
    fn retention_prunes_old_visits_and_events() {
        let store = Store::open_in_memory().expect("open in-memory database");
        let old = NaiveDate::from_ymd_opt(2026, 5, 1).expect("valid old date");
        let current = NaiveDate::from_ymd_opt(2026, 9, 1).expect("valid current date");

        store
            .record_visit(old, "203.0.113.10")
            .expect("record old visit");
        store
            .record_skill_event(
                old,
                "203.0.113.10",
                "image-api-workbench",
                SkillEventType::SkillView,
            )
            .expect("record old event");
        store
            .record_visit(current, "198.51.100.7")
            .expect("record current visit");
        store.prune_before(current).expect("prune expired IP data");

        let metrics = store
            .metrics(current, &skill_names())
            .expect("load retained metrics");
        assert_eq!(metrics.total_visitors, 1);
        assert_eq!(metrics.skill_engagement[0].views, 0);
    }

    #[test]
    fn retention_reports_busy_wal_checkpoint() {
        let path = temporary_database_path();
        let store = Store::open(&path).expect("open file database");
        let old = NaiveDate::from_ymd_opt(2026, 5, 1).expect("valid old date");
        let current = NaiveDate::from_ymd_opt(2026, 9, 1).expect("valid current date");
        store
            .record_visit(old, "203.0.113.10")
            .expect("record old visit");

        let reader = Connection::open(&path).expect("open external reader");
        reader
            .execute_batch("BEGIN")
            .expect("begin read transaction");
        let _: i64 = reader
            .query_row("SELECT COUNT(*) FROM daily_visits", [], |row| row.get(0))
            .expect("establish read snapshot");
        store
            .record_visit(current, "198.51.100.7")
            .expect("record current visit after snapshot");

        let error = store
            .prune_before(current)
            .expect_err("busy checkpoint must degrade retention");
        assert!(error.to_string().contains("checkpoint remained busy"));

        reader
            .execute_batch("ROLLBACK")
            .expect("release read transaction");
        store
            .prune_before(current)
            .expect("checkpoint succeeds after reader releases snapshot");

        drop(reader);
        drop(store);
        remove_database_files(&path);
    }
}
