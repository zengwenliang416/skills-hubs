use std::{collections::HashSet, fs, path::Path};

use anyhow::{Context, Result, anyhow};
use serde::Deserialize;

#[derive(Debug)]
pub struct CatalogIndex {
    pub skill_names: Vec<String>,
    pub package_names: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct Catalog {
    skills: Vec<CatalogSkill>,
}

#[derive(Debug, Deserialize)]
struct CatalogSkill {
    name: String,
    npm: Option<String>,
}

pub fn catalog_index_from_path(path: &Path) -> Result<CatalogIndex> {
    let body = fs::read_to_string(path)
        .with_context(|| format!("failed to read catalog {}", path.display()))?;
    parse_catalog_index(&body)
        .with_context(|| format!("failed to parse catalog {}", path.display()))
}

fn parse_catalog_index(body: &str) -> Result<CatalogIndex> {
    let catalog: Catalog = serde_json::from_str(body)?;
    let mut skill_names = Vec::with_capacity(catalog.skills.len());
    let mut package_names = Vec::new();
    let mut seen_skills = HashSet::new();
    let mut seen_packages = HashSet::new();

    for skill in catalog.skills {
        let name = skill.name.trim();
        if name.is_empty() {
            return Err(anyhow!("catalog contains an empty Skill name"));
        }
        if !seen_skills.insert(name.to_owned()) {
            return Err(anyhow!("catalog contains duplicate Skill name {name}"));
        }
        skill_names.push(name.to_owned());

        if let Some(package_name) = skill.npm {
            let package_name = package_name.trim();
            if !package_name.is_empty() && seen_packages.insert(package_name.to_owned()) {
                package_names.push(package_name.to_owned());
            }
        }
    }

    if skill_names.is_empty() {
        return Err(anyhow!("catalog contains no Skills"));
    }

    Ok(CatalogIndex {
        skill_names,
        package_names,
    })
}

#[cfg(test)]
mod tests {
    use super::parse_catalog_index;

    #[test]
    fn extracts_ordered_skills_and_unique_packages() {
        let index = parse_catalog_index(
            r#"{
                "skills": [
                    {"name":"one","npm":"package-one"},
                    {"name":"two","npm":" package-two "},
                    {"name":"three","npm":"package-one"},
                    {"name":"manual"}
                ]
            }"#,
        )
        .expect("parse catalog");

        assert_eq!(index.skill_names, vec!["one", "two", "three", "manual"]);
        assert_eq!(index.package_names, vec!["package-one", "package-two"]);
    }

    #[test]
    fn rejects_duplicate_skill_names() {
        let error = parse_catalog_index(
            r#"{
                "skills": [
                    {"name":"duplicate"},
                    {"name":"duplicate"}
                ]
            }"#,
        )
        .expect_err("duplicate names should fail");

        assert_eq!(
            error.to_string(),
            "catalog contains duplicate Skill name duplicate"
        );
    }
}
