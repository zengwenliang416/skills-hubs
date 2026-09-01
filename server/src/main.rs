mod catalog;
mod model;
mod npm;
mod store;
mod traffic;

use std::{env, net::SocketAddr, path::PathBuf, sync::Arc, time::Duration};

use anyhow::{Context, Result};
use axum::{
    Json, Router,
    extract::{ConnectInfo, DefaultBodyLimit, State, rejection::JsonRejection},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use catalog::catalog_index_from_path;
use chrono::{NaiveDate, Utc};
use model::{
    ErrorResponse, HealthResponse, MetricsResponse, RetentionHealthResponse, SkillEventRequest,
};
use npm::NpmDownloads;
use store::Store;
use tokio::sync::{RwLock, Semaphore};
use tower_http::services::{ServeDir, ServeFile};
use traffic::{TrustedProxies, WriteLimiter, client_ip};

const DEFAULT_BIND: &str = "127.0.0.1:8080";
const DEFAULT_CATALOG_PATH: &str = "catalog.json";
const DEFAULT_DB_PATH: &str = "data/skills-hub.sqlite3";
const DEFAULT_STATIC_DIR: &str = "web/dist";
const DEFAULT_TRUSTED_PROXIES: &str = "";
const DEFAULT_WRITE_LIMIT_PER_MINUTE: &str = "120";
const DEFAULT_DB_CONCURRENCY: &str = "16";
const DEFAULT_IP_RETENTION_DAYS: &str = "90";

#[derive(Clone)]
struct AppState {
    store: Store,
    npm_downloads: NpmDownloads,
    skill_names: Arc<[String]>,
    trusted_proxies: TrustedProxies,
    write_limiter: WriteLimiter,
    db_permits: Arc<Semaphore>,
    retention_health: RetentionHealth,
}

#[derive(Clone)]
struct RetentionHealth {
    state: Arc<RwLock<RetentionHealthResponse>>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let bind = env_value("SKILLS_HUB_BIND", DEFAULT_BIND);
    let catalog_path = PathBuf::from(env_value("SKILLS_HUB_CATALOG_PATH", DEFAULT_CATALOG_PATH));
    let db_path = PathBuf::from(env_value("SKILLS_HUB_DB_PATH", DEFAULT_DB_PATH));
    let static_dir = PathBuf::from(env_value("SKILLS_HUB_STATIC_DIR", DEFAULT_STATIC_DIR));
    let trusted_proxies = TrustedProxies::parse(&env_value(
        "SKILLS_HUB_TRUSTED_PROXIES",
        DEFAULT_TRUSTED_PROXIES,
    ))?;
    let write_limit = env_positive_u32(
        "SKILLS_HUB_WRITE_LIMIT_PER_MINUTE",
        DEFAULT_WRITE_LIMIT_PER_MINUTE,
    )?;
    let db_concurrency = env_positive_u32("SKILLS_HUB_DB_CONCURRENCY", DEFAULT_DB_CONCURRENCY)?;
    let retention_days =
        env_positive_u32("SKILLS_HUB_IP_RETENTION_DAYS", DEFAULT_IP_RETENTION_DAYS)?;
    let catalog_index = catalog_index_from_path(&catalog_path)?;
    let store = Store::open(&db_path)?;
    prune_expired_ip_data(&store, retention_days)?;
    let db_permits = Arc::new(Semaphore::new(db_concurrency as usize));
    let retention_health = RetentionHealth::healthy();
    spawn_retention_task(
        store.clone(),
        retention_days,
        db_permits.clone(),
        retention_health.clone(),
    );

    let state = AppState {
        store,
        npm_downloads: NpmDownloads::new(catalog_index.package_names)?,
        skill_names: catalog_index.skill_names.into(),
        trusted_proxies,
        write_limiter: WriteLimiter::per_minute(write_limit),
        db_permits,
        retention_health,
    };
    let static_files =
        ServeDir::new(&static_dir).not_found_service(ServeFile::new(static_dir.join("index.html")));
    let app = Router::new()
        .route("/api/visits", post(record_visit))
        .route(
            "/api/events",
            post(record_skill_event).layer(DefaultBodyLimit::max(1024)),
        )
        .route("/api/metrics", get(get_metrics))
        .route("/api/healthz", get(get_health))
        .fallback_service(static_files)
        .with_state(state);

    let listener = tokio::net::TcpListener::bind(&bind)
        .await
        .with_context(|| format!("failed to bind server to {bind}"))?;
    println!("skills-hub-server listening on {bind}");
    axum::serve(
        listener,
        app.into_make_service_with_connect_info::<SocketAddr>(),
    )
    .await
    .context("HTTP server stopped unexpectedly")
}

async fn record_visit(
    State(state): State<AppState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    headers: HeaderMap,
) -> Result<Json<MetricsResponse>, ApiError> {
    let today = Utc::now().date_naive();
    let visitor_ip = client_ip(peer.ip(), &headers, &state.trusted_proxies);
    enforce_write_capacity(&state, visitor_ip)?;
    let permit = state
        .db_permits
        .clone()
        .try_acquire_owned()
        .map_err(|_| ApiError::too_many_requests())?;
    let store = state.store.clone();
    let visitor_ip = visitor_ip.to_string();

    tokio::task::spawn_blocking(move || {
        let _permit = permit;
        store.record_visit(today, &visitor_ip)
    })
    .await
    .map_err(|_| ApiError::internal())?
    .map_err(|_| ApiError::internal())?;

    metrics_response(state, today).await
}

async fn record_skill_event(
    State(state): State<AppState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    headers: HeaderMap,
    payload: Result<Json<SkillEventRequest>, JsonRejection>,
) -> Result<StatusCode, ApiError> {
    let Json(event) = payload.map_err(|rejection| ApiError::request(rejection.status()))?;
    if !state
        .skill_names
        .iter()
        .any(|skill_name| skill_name == &event.skill_name)
    {
        return Err(ApiError::request(StatusCode::UNPROCESSABLE_ENTITY));
    }

    let today = Utc::now().date_naive();
    let visitor_ip = client_ip(peer.ip(), &headers, &state.trusted_proxies);
    enforce_write_capacity(&state, visitor_ip)?;
    let permit = state
        .db_permits
        .clone()
        .try_acquire_owned()
        .map_err(|_| ApiError::too_many_requests())?;
    let store = state.store.clone();
    let visitor_ip = visitor_ip.to_string();
    tokio::task::spawn_blocking(move || {
        let _permit = permit;
        store.record_skill_event(today, &visitor_ip, &event.skill_name, event.event_type)
    })
    .await
    .map_err(|_| ApiError::internal())?
    .map_err(|_| ApiError::internal())?;

    Ok(StatusCode::NO_CONTENT)
}

async fn get_metrics(State(state): State<AppState>) -> Result<Json<MetricsResponse>, ApiError> {
    metrics_response(state, Utc::now().date_naive()).await
}

async fn get_health(State(state): State<AppState>) -> (StatusCode, Json<HealthResponse>) {
    let retention = state.retention_health.snapshot().await;
    let (status_code, status) = if retention.healthy {
        (StatusCode::OK, "ok")
    } else {
        (StatusCode::SERVICE_UNAVAILABLE, "degraded")
    };

    (status_code, Json(HealthResponse { status, retention }))
}

async fn metrics_response(
    state: AppState,
    today: NaiveDate,
) -> Result<Json<MetricsResponse>, ApiError> {
    let permit = state
        .db_permits
        .clone()
        .try_acquire_owned()
        .map_err(|_| ApiError::too_many_requests())?;
    let store = state.store.clone();
    let skill_names = state.skill_names.clone();
    let store_metrics = tokio::task::spawn_blocking(move || {
        let _permit = permit;
        store.metrics(today, &skill_names)
    });
    let npm_downloads = state.npm_downloads.metrics();
    let (store_metrics, npm_downloads) = tokio::join!(store_metrics, npm_downloads);
    let store_metrics = store_metrics
        .map_err(|_| ApiError::internal())?
        .map_err(|_| ApiError::internal())?;

    Ok(Json(MetricsResponse {
        total_visitors: store_metrics.total_visitors,
        today_visitors: store_metrics.today_visitors,
        total_page_views: store_metrics.total_page_views,
        daily_visitors: store_metrics.daily_visitors,
        npm_downloads,
        skill_engagement: store_metrics.skill_engagement,
    }))
}

fn enforce_write_capacity(state: &AppState, visitor_ip: std::net::IpAddr) -> Result<(), ApiError> {
    state
        .write_limiter
        .allow(visitor_ip)
        .then_some(())
        .ok_or_else(ApiError::too_many_requests)
}

fn env_value(name: &str, default: &str) -> String {
    env::var(name).unwrap_or_else(|_| default.to_owned())
}

fn env_positive_u32(name: &str, default: &str) -> Result<u32> {
    let value = env_value(name, default);
    match value.parse::<u32>() {
        Ok(value) if value > 0 => Ok(value),
        _ => anyhow::bail!("{name} must be a positive integer"),
    }
}

fn retention_cutoff(retention_days: u32) -> NaiveDate {
    Utc::now().date_naive() - chrono::Duration::days(i64::from(retention_days.saturating_sub(1)))
}

fn prune_expired_ip_data(store: &Store, retention_days: u32) -> Result<()> {
    store.prune_before(retention_cutoff(retention_days))
}

fn spawn_retention_task(
    store: Store,
    retention_days: u32,
    db_permits: Arc<Semaphore>,
    retention_health: RetentionHealth,
) {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(24 * 60 * 60));
        interval.tick().await;
        loop {
            interval.tick().await;
            let store = store.clone();
            let cutoff = retention_cutoff(retention_days);
            let permit = match db_permits.clone().acquire_owned().await {
                Ok(permit) => permit,
                Err(error) => {
                    eprintln!("retention cleanup semaphore closed: {error}");
                    retention_health.mark_failure().await;
                    return;
                }
            };
            let result = tokio::task::spawn_blocking(move || {
                let _permit = permit;
                store.prune_before(cutoff)
            })
            .await;
            match result {
                Ok(Ok(())) => retention_health.mark_success().await,
                Ok(Err(error)) => {
                    eprintln!("retention cleanup failed: {error:#}");
                    retention_health.mark_failure().await;
                }
                Err(error) => {
                    eprintln!("retention cleanup task failed: {error}");
                    retention_health.mark_failure().await;
                }
            }
        }
    });
}

impl RetentionHealth {
    fn healthy() -> Self {
        Self {
            state: Arc::new(RwLock::new(RetentionHealthResponse {
                healthy: true,
                last_success_at: Some(Utc::now().to_rfc3339()),
                last_failure_at: None,
            })),
        }
    }

    async fn snapshot(&self) -> RetentionHealthResponse {
        self.state.read().await.clone()
    }

    async fn mark_success(&self) {
        let mut state = self.state.write().await;
        state.healthy = true;
        state.last_success_at = Some(Utc::now().to_rfc3339());
    }

    async fn mark_failure(&self) {
        let mut state = self.state.write().await;
        state.healthy = false;
        state.last_failure_at = Some(Utc::now().to_rfc3339());
    }
}

#[derive(Debug)]
struct ApiError {
    status: StatusCode,
    message: &'static str,
}

impl ApiError {
    fn request(status: StatusCode) -> Self {
        Self {
            status,
            message: "invalid request",
        }
    }

    fn too_many_requests() -> Self {
        Self {
            status: StatusCode::TOO_MANY_REQUESTS,
            message: "too many requests",
        }
    }

    fn internal() -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            message: "internal server error",
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(ErrorResponse {
                error: self.message.to_owned(),
            }),
        )
            .into_response()
    }
}

#[cfg(test)]
mod tests {
    use super::RetentionHealth;

    #[tokio::test]
    async fn retention_health_tracks_failure_and_recovery() {
        let health = RetentionHealth::healthy();
        assert!(health.snapshot().await.healthy);

        health.mark_failure().await;
        let failed = health.snapshot().await;
        assert!(!failed.healthy);
        assert!(failed.last_failure_at.is_some());

        health.mark_success().await;
        let recovered = health.snapshot().await;
        assert!(recovered.healthy);
        assert!(recovered.last_success_at.is_some());
    }
}
