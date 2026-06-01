//! ABI contract between wasm64 tool binaries and the NEXUS host adapter.

/// file_read validation status codes
pub const FILE_READ_OK: u64 = 0;
pub const FILE_READ_ERR_NULL: u64 = 1;
pub const FILE_READ_ERR_UTF8: u64 = 2;

/// Validate a path string: must be non-empty UTF-8 with no path traversal.
pub fn validate_path(path: &str) -> Result<(), u64> {
    if path.is_empty() {
        return Err(FILE_READ_ERR_NULL);
    }
    if path.contains("..") {
        return Err(FILE_READ_ERR_UTF8);
    }
    Ok(())
}
