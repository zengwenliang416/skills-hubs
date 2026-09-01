use std::{
    collections::HashMap,
    net::{IpAddr, Ipv6Addr, SocketAddr},
    str::FromStr,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};

use anyhow::{Result, anyhow};
use axum::http::HeaderMap;
use ipnet::IpNet;

const DEFAULT_MAX_LIMITER_ENTRIES: usize = 4096;
const DEFAULT_LIMITER_CLEANUP_INTERVAL: Duration = Duration::from_secs(30);

#[derive(Clone, Debug)]
pub struct TrustedProxies {
    networks: Arc<[IpNet]>,
}

impl TrustedProxies {
    pub fn parse(value: &str) -> Result<Self> {
        let networks = value
            .split(',')
            .map(str::trim)
            .filter(|entry| !entry.is_empty())
            .map(|entry| {
                entry.parse::<IpNet>().map_err(|_| {
                    anyhow!("SKILLS_HUB_TRUSTED_PROXIES contains invalid CIDR {entry}")
                })
            })
            .collect::<Result<Vec<_>>>()?;
        Ok(Self {
            networks: networks.into(),
        })
    }

    fn contains(&self, ip: IpAddr) -> bool {
        self.networks
            .iter()
            .any(|network| network.contains(&normalize_ip(ip)))
    }
}

pub fn client_ip(peer_ip: IpAddr, headers: &HeaderMap, trusted: &TrustedProxies) -> IpAddr {
    let peer_ip = normalize_ip(peer_ip);
    if !trusted.contains(peer_ip) {
        return peer_ip;
    }

    let mut chain = forwarded_chain(headers);
    if chain.is_empty() {
        chain = header_chain(headers, "x-forwarded-for");
    }
    chain.push(peer_ip);

    chain
        .into_iter()
        .rev()
        .map(normalize_ip)
        .find(|ip| !trusted.contains(*ip))
        .or_else(|| header_ip(headers, "x-real-ip").map(normalize_ip))
        .unwrap_or(peer_ip)
}

fn forwarded_chain(headers: &HeaderMap) -> Vec<IpAddr> {
    headers
        .get("forwarded")
        .and_then(|value| value.to_str().ok())
        .into_iter()
        .flat_map(|value| value.split(','))
        .filter_map(|hop| {
            hop.split(';').find_map(|parameter| {
                let (name, value) = parameter.split_once('=')?;
                name.trim()
                    .eq_ignore_ascii_case("for")
                    .then(|| parse_ip_token(value))
                    .flatten()
            })
        })
        .collect()
}

fn header_chain(headers: &HeaderMap, name: &'static str) -> Vec<IpAddr> {
    headers
        .get(name)
        .and_then(|value| value.to_str().ok())
        .into_iter()
        .flat_map(|value| value.split(','))
        .filter_map(parse_ip_token)
        .collect()
}

fn header_ip(headers: &HeaderMap, name: &'static str) -> Option<IpAddr> {
    let value = headers.get(name)?.to_str().ok()?;
    parse_ip_token(value)
}

fn parse_ip_token(value: &str) -> Option<IpAddr> {
    let value = value.trim().trim_matches('"');
    if let Some(bracketed) = value.strip_prefix('[') {
        return bracketed
            .split_once(']')
            .and_then(|(ip, _)| IpAddr::from_str(ip).ok());
    }
    IpAddr::from_str(value)
        .ok()
        .or_else(|| SocketAddr::from_str(value).ok().map(|address| address.ip()))
}

fn normalize_ip(ip: IpAddr) -> IpAddr {
    match ip {
        IpAddr::V6(ipv6) => ipv6
            .to_ipv4_mapped()
            .map(IpAddr::V4)
            .unwrap_or(IpAddr::V6(ipv6)),
        ipv4 => ipv4,
    }
}

#[derive(Clone)]
pub struct WriteLimiter {
    limit: u32,
    window: Duration,
    max_entries: usize,
    cleanup_interval: Duration,
    state: Arc<Mutex<LimiterState>>,
}

struct LimiterState {
    entries: HashMap<IpAddr, RateWindow>,
    last_cleanup: Instant,
}

struct RateWindow {
    started_at: Instant,
    count: u32,
}

impl WriteLimiter {
    pub fn per_minute(limit: u32) -> Self {
        Self::new(
            limit,
            Duration::from_secs(60),
            DEFAULT_MAX_LIMITER_ENTRIES,
            DEFAULT_LIMITER_CLEANUP_INTERVAL,
        )
    }

    fn new(limit: u32, window: Duration, max_entries: usize, cleanup_interval: Duration) -> Self {
        Self {
            limit,
            window,
            max_entries,
            cleanup_interval,
            state: Arc::new(Mutex::new(LimiterState {
                entries: HashMap::new(),
                last_cleanup: Instant::now(),
            })),
        }
    }

    pub fn allow(&self, ip: IpAddr) -> bool {
        let now = Instant::now();
        let key = rate_limit_key(ip);
        let Ok(mut state) = self.state.lock() else {
            return false;
        };
        if now.duration_since(state.last_cleanup) >= self.cleanup_interval {
            state
                .entries
                .retain(|_, entry| now.duration_since(entry.started_at) < self.window);
            state.last_cleanup = now;
        }
        if !state.entries.contains_key(&key) && state.entries.len() >= self.max_entries {
            return false;
        }
        let entry = state.entries.entry(key).or_insert(RateWindow {
            started_at: now,
            count: 0,
        });
        if now.duration_since(entry.started_at) >= self.window {
            entry.started_at = now;
            entry.count = 0;
        }
        if entry.count >= self.limit {
            return false;
        }
        entry.count += 1;
        true
    }
}

fn rate_limit_key(ip: IpAddr) -> IpAddr {
    match normalize_ip(ip) {
        IpAddr::V6(ipv6) => {
            let segments = ipv6.segments();
            IpAddr::V6(Ipv6Addr::new(
                segments[0],
                segments[1],
                segments[2],
                segments[3],
                0,
                0,
                0,
                0,
            ))
        }
        ipv4 => ipv4,
    }
}

#[cfg(test)]
mod tests {
    use std::{
        net::{IpAddr, Ipv4Addr},
        time::Duration,
    };

    use axum::http::{HeaderMap, HeaderValue};

    use super::{TrustedProxies, WriteLimiter, client_ip, normalize_ip};

    #[test]
    fn untrusted_peer_cannot_spoof_forwarding_headers() {
        let mut headers = HeaderMap::new();
        headers.insert("x-forwarded-for", HeaderValue::from_static("203.0.113.10"));
        let peer = IpAddr::V4(Ipv4Addr::LOCALHOST);
        let trusted = TrustedProxies::parse("").expect("empty proxy list");

        assert_eq!(client_ip(peer, &headers, &trusted), peer);
    }

    #[test]
    fn trusted_proxy_removes_trusted_hops_from_the_right() {
        let mut headers = HeaderMap::new();
        headers.insert(
            "x-forwarded-for",
            HeaderValue::from_static("198.51.100.9, 203.0.113.10, 10.0.0.2"),
        );
        let trusted = TrustedProxies::parse("127.0.0.1/32,10.0.0.0/8").expect("trusted networks");

        assert_eq!(
            client_ip(IpAddr::V4(Ipv4Addr::LOCALHOST), &headers, &trusted),
            "203.0.113.10".parse::<IpAddr>().expect("valid IP")
        );
    }

    #[test]
    fn normalizes_ipv4_mapped_ipv6() {
        let mapped = "::ffff:192.0.2.1".parse().expect("valid mapped IP");
        assert_eq!(
            normalize_ip(mapped),
            "192.0.2.1".parse::<IpAddr>().expect("valid IPv4")
        );
    }

    #[test]
    fn limiter_rejects_requests_after_the_window_limit() {
        let limiter = WriteLimiter::per_minute(2);
        let ip = IpAddr::V4(Ipv4Addr::LOCALHOST);

        assert!(limiter.allow(ip));
        assert!(limiter.allow(ip));
        assert!(!limiter.allow(ip));
    }

    #[test]
    fn limiter_rejects_new_keys_at_hard_capacity() {
        let limiter = WriteLimiter::new(2, Duration::from_secs(60), 2, Duration::from_secs(30));

        assert!(limiter.allow("192.0.2.1".parse().expect("valid IP")));
        assert!(limiter.allow("192.0.2.2".parse().expect("valid IP")));
        assert!(!limiter.allow("192.0.2.3".parse().expect("valid IP")));
    }

    #[test]
    fn limiter_groups_native_ipv6_by_64_prefix() {
        let limiter = WriteLimiter::new(1, Duration::from_secs(60), 2, Duration::from_secs(30));

        assert!(limiter.allow("2001:db8:1234:5678::1".parse().expect("valid first IPv6")));
        assert!(!limiter.allow("2001:db8:1234:5678::2".parse().expect("valid second IPv6")));
        assert!(
            limiter.allow(
                "2001:db8:1234:5679::1"
                    .parse()
                    .expect("valid different prefix")
            )
        );
    }
}
