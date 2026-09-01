use std::{
    collections::HashMap,
    sync::Arc,
    time::{Duration, Instant},
};

use anyhow::{Context, Result, anyhow};
use futures_util::future::join_all;
use reqwest::{Client, StatusCode};
use serde::Deserialize;
use tokio::sync::{Mutex, RwLock};

use crate::model::NpmDownload;

const CACHE_TTL: Duration = Duration::from_secs(15 * 60);
const FAILURE_CACHE_TTL: Duration = Duration::from_secs(2 * 60);

#[derive(Clone)]
pub struct NpmDownloads {
    client: Client,
    package_names: Arc<[String]>,
    cache: Arc<RwLock<HashMap<String, CachedDownload>>>,
    failures: Arc<RwLock<HashMap<String, CachedFailure>>>,
    refresh_locks: Arc<HashMap<String, Arc<Mutex<()>>>>,
}

#[derive(Clone)]
struct CachedDownload {
    fetched_at: Instant,
    downloads: u64,
    period_start: String,
    period_end: String,
}

#[derive(Clone)]
struct CachedFailure {
    fetched_at: Instant,
    message: String,
}

#[derive(Debug, Deserialize)]
struct NpmPointResponse {
    downloads: u64,
    start: String,
    end: String,
}

impl NpmDownloads {
    pub fn new(package_names: Vec<String>) -> Result<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(10))
            .user_agent("skills-hub-server/0.1")
            .build()
            .context("failed to create npm HTTP client")?;
        let refresh_locks = package_names
            .iter()
            .map(|package_name| (package_name.clone(), Arc::new(Mutex::new(()))))
            .collect();

        Ok(Self {
            client,
            package_names: package_names.into(),
            cache: Arc::new(RwLock::new(HashMap::new())),
            failures: Arc::new(RwLock::new(HashMap::new())),
            refresh_locks: Arc::new(refresh_locks),
        })
    }

    pub async fn metrics(&self) -> Vec<NpmDownload> {
        join_all(
            self.package_names
                .iter()
                .map(|package_name| self.package_metrics(package_name)),
        )
        .await
    }

    async fn package_metrics(&self, package_name: &str) -> NpmDownload {
        if let Some(response) = self.fresh_response(package_name).await {
            return response;
        }

        let Some(refresh_lock) = self.refresh_locks.get(package_name).cloned() else {
            return failed_response(package_name, None, "package is not configured".to_owned());
        };
        let _refresh = refresh_lock.lock().await;
        if let Some(response) = self.fresh_response(package_name).await {
            return response;
        }
        match self.fetch(package_name).await {
            Ok(download) => {
                self.cache
                    .write()
                    .await
                    .insert(package_name.to_owned(), download.clone());
                self.failures.write().await.remove(package_name);
                cached_response(package_name, &download, false, None)
            }
            Err(error) => {
                let message = error.to_string();
                self.failures.write().await.insert(
                    package_name.to_owned(),
                    CachedFailure {
                        fetched_at: Instant::now(),
                        message: message.clone(),
                    },
                );
                let cached = self.cache.read().await.get(package_name).cloned();
                failed_response(package_name, cached.as_ref(), message)
            }
        }
    }

    async fn fresh_response(&self, package_name: &str) -> Option<NpmDownload> {
        let cached = self.cache.read().await.get(package_name).cloned();
        if let Some(cached) = cached
            .as_ref()
            .filter(|cached| cached.fetched_at.elapsed() < CACHE_TTL)
        {
            return Some(cached_response(package_name, cached, false, None));
        }

        let failure = self
            .failures
            .read()
            .await
            .get(package_name)
            .filter(|failure| failure.fetched_at.elapsed() < FAILURE_CACHE_TTL)
            .cloned();
        failure.map(|failure| failed_response(package_name, cached.as_ref(), failure.message))
    }

    async fn fetch(&self, package_name: &str) -> Result<CachedDownload> {
        let mut url = reqwest::Url::parse("https://api.npmjs.org/downloads/point/last-week/")
            .context("invalid npm API base URL")?;
        url.path_segments_mut()
            .map_err(|_| anyhow!("invalid npm API base URL"))?
            .pop_if_empty()
            .push(package_name);
        let response = self
            .client
            .get(url)
            .send()
            .await
            .map_err(|_| anyhow!("npm API request failed"))?;

        if response.status() != StatusCode::OK {
            return Err(anyhow!(
                "npm API returned HTTP {}",
                response.status().as_u16()
            ));
        }

        let body = response
            .text()
            .await
            .map_err(|_| anyhow!("npm API response body could not be read"))?;
        let point = parse_point_response(&body)?;

        Ok(CachedDownload {
            fetched_at: Instant::now(),
            downloads: point.downloads,
            period_start: point.start,
            period_end: point.end,
        })
    }
}

fn cached_response(
    package_name: &str,
    cached: &CachedDownload,
    stale: bool,
    error: Option<String>,
) -> NpmDownload {
    NpmDownload {
        package_name: package_name.to_owned(),
        downloads: Some(cached.downloads),
        period_start: Some(cached.period_start.clone()),
        period_end: Some(cached.period_end.clone()),
        stale,
        error,
    }
}

fn failed_response(
    package_name: &str,
    cached: Option<&CachedDownload>,
    message: String,
) -> NpmDownload {
    match cached {
        Some(cached) => cached_response(package_name, cached, true, Some(message)),
        None => NpmDownload {
            package_name: package_name.to_owned(),
            downloads: None,
            period_start: None,
            period_end: None,
            stale: true,
            error: Some(message),
        },
    }
}

fn parse_point_response(body: &str) -> Result<NpmPointResponse> {
    serde_json::from_str(body).map_err(|_| anyhow!("npm API returned invalid JSON"))
}

#[cfg(test)]
mod tests {
    use std::{sync::Arc, time::Instant};

    use super::{CachedDownload, NpmDownloads, failed_response, parse_point_response};

    #[test]
    fn parses_npm_point_response() {
        let response = parse_point_response(
            r#"{
                "downloads": 1234,
                "start": "2026-08-24",
                "end": "2026-08-30",
                "package": "image-api-workbench"
            }"#,
        )
        .expect("parse npm response");

        assert_eq!(response.downloads, 1234);
        assert_eq!(response.start, "2026-08-24");
        assert_eq!(response.end, "2026-08-30");
    }

    #[test]
    fn rejects_invalid_npm_point_response() {
        let error = parse_point_response(r#"{"downloads":"many"}"#)
            .expect_err("invalid response should fail");

        assert_eq!(error.to_string(), "npm API returned invalid JSON");
    }

    #[test]
    fn negative_cache_response_preserves_stale_success() {
        let cached = CachedDownload {
            fetched_at: Instant::now(),
            downloads: 42,
            period_start: "2026-08-24".to_owned(),
            period_end: "2026-08-30".to_owned(),
        };

        let response = failed_response("example", Some(&cached), "HTTP 404".to_owned());

        assert_eq!(response.downloads, Some(42));
        assert!(response.stale);
        assert_eq!(response.error.as_deref(), Some("HTTP 404"));
    }

    #[test]
    fn refresh_locks_are_independent_per_package() {
        let downloads = NpmDownloads::new(vec!["package-one".to_owned(), "package-two".to_owned()])
            .expect("create npm downloads");
        let first = downloads
            .refresh_locks
            .get("package-one")
            .expect("first package lock");
        let second = downloads
            .refresh_locks
            .get("package-two")
            .expect("second package lock");

        assert!(!Arc::ptr_eq(first, second));
    }
}
