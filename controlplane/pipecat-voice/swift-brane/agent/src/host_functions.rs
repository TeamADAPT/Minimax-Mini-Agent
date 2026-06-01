//! L010 host function gate for wasm64 tools.
//!
//! These functions are the only way a wasm64 tool touches the outside world.
//! All side effects such as file I/O, clock, and entropy pass through here.

use std::fs;
use std::path::{Component, Path, PathBuf};

use crate::tool_interface;

/// Result of a host function call.
pub enum HostResult {
    /// The host function completed and returned bytes.
    Success(Vec<u8>),
    /// The requested resource does not exist or is outside the sandbox.
    NotFound,
    /// The host function failed for an I/O reason.
    IoError(String),
}

/// Host function: read a file on behalf of the wasm64 tool.
///
/// L010 mandate: The wasm64 tool cannot do I/O. All file access goes through
/// this function, which the host provides at instantiation.
///
/// Security: paths are resolved under `SWIFT_BRANE_ROOT`, defaulting to the
/// current working directory. Absolute paths are allowed only when their
/// canonical target remains under that root.
pub fn host_file_read(path_str: &str) -> HostResult {
    let requested = Path::new(path_str);
    if has_parent_component(requested) {
        return HostResult::NotFound;
    }

    let path = match resolve_sandboxed_path(requested) {
        Ok(path) => path,
        Err(result) => return result,
    };
    match fs::read(path) {
        Ok(data) => HostResult::Success(data),
        Err(e) => match e.kind() {
            std::io::ErrorKind::NotFound => HostResult::NotFound,
            _ => HostResult::IoError(e.to_string()),
        },
    }
}

/// Validate a path using the wasm64 tool's validation logic.
/// Returns the tool's status code.
pub fn validate_path_with_tool(path: &str) -> u64 {
    match tool_interface::validate_path(path) {
        Ok(()) => tool_interface::FILE_READ_OK,
        Err(code) => code,
    }
}

fn resolve_sandboxed_path(requested: &Path) -> Result<PathBuf, HostResult> {
    let root = sandbox_root()?;
    let candidate = if requested.is_absolute() {
        requested.to_path_buf()
    } else {
        root.join(requested)
    };
    let canonical = candidate
        .canonicalize()
        .map_err(|error| match error.kind() {
            std::io::ErrorKind::NotFound => HostResult::NotFound,
            _ => HostResult::IoError(error.to_string()),
        })?;
    if canonical.starts_with(&root) {
        Ok(canonical)
    } else {
        Err(HostResult::NotFound)
    }
}

fn sandbox_root() -> Result<PathBuf, HostResult> {
    let root = std::env::var("SWIFT_BRANE_ROOT").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(root)
        .canonicalize()
        .map_err(|error| HostResult::IoError(error.to_string()))
}

fn has_parent_component(path: &Path) -> bool {
    path.components()
        .any(|component| matches!(component, Component::ParentDir | Component::Prefix(_)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    static ENV_LOCK: Mutex<()> = Mutex::new(());

    #[test]
    fn host_file_read_allows_files_inside_sandbox() {
        let _guard = ENV_LOCK.lock().expect("env lock should not be poisoned");
        let root = create_test_root("inside");
        fs::write(root.join("ok.txt"), "swift").expect("test file should be writable");
        std::env::set_var("SWIFT_BRANE_ROOT", &root);

        match host_file_read("ok.txt") {
            HostResult::Success(bytes) => assert_eq!(bytes, b"swift"),
            _ => panic!("expected sandboxed read to succeed"),
        }

        cleanup_test_root(&root);
    }

    #[test]
    fn host_file_read_blocks_parent_traversal() {
        let _guard = ENV_LOCK.lock().expect("env lock should not be poisoned");
        let root = create_test_root("traversal");
        std::env::set_var("SWIFT_BRANE_ROOT", &root);

        assert!(matches!(
            host_file_read("../secret.txt"),
            HostResult::NotFound
        ));

        cleanup_test_root(&root);
    }

    #[test]
    fn host_file_read_blocks_absolute_paths_outside_sandbox() {
        let _guard = ENV_LOCK.lock().expect("env lock should not be poisoned");
        let root = create_test_root("outside");
        std::env::set_var("SWIFT_BRANE_ROOT", &root);

        assert!(matches!(host_file_read("/etc/hosts"), HostResult::NotFound));

        cleanup_test_root(&root);
    }

    fn create_test_root(name: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "swift-brane-host-functions-{}-{}",
            name,
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).expect("test root should be creatable");
        root
    }

    fn cleanup_test_root(root: &Path) {
        let _ = fs::remove_dir_all(root);
        std::env::remove_var("SWIFT_BRANE_ROOT");
    }
}
