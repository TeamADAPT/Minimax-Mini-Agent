#![cfg_attr(target_arch = "wasm64", no_std)]

#[cfg(target_arch = "wasm64")]
use core::panic::PanicInfo;

// ---------------------------------------------------------------------------
// Host function imports (L010 sandbox gate)
//
// These functions are PROVIDED by the NEXUS host at instantiation.
// The wasm64 tool cannot do I/O — it calls these when it needs side effects.
//
// In the cdylib / native FFI path, these are resolved at link time.
// In the wasmtime path, these are declared in the import section of the .wasm.
//
// For the file_read pilot, the tool does NOT currently call host functions
// because it only validates paths (pure computation). Future tools will
// import host_file_read, host_clock, host_entropy, etc.
// ---------------------------------------------------------------------------

const FILE_READ_OK: u64 = 0;
const _FILE_READ_ERR_NULL: u64 = 1;
const _FILE_READ_ERR_UTF8: u64 = 2;

// ---------------------------------------------------------------------------
// Tool exports: the wasm64 tool provides these to the host
// ---------------------------------------------------------------------------

/// Validate a file path and return a status code.
///
/// This is a PURE function — no I/O, no side effects.
/// Actual file reading is done by the host via host function imports (L010).
///
/// Arguments:
///   path_ptr — offset of path string in wasm linear memory
///   path_len — byte length of the path string
///
/// Returns:
///   0 = valid UTF-8 path
///   1 = null or empty path
///   2 = invalid UTF-8
#[no_mangle]
pub extern "C" fn file_read(path_ptr: u64, path_len: u64) -> u64 {
    if path_ptr == 0 || path_len == 0 {
        return 1;
    }
    let path_bytes =
        unsafe { core::slice::from_raw_parts(path_ptr as *const u8, path_len as usize) };
    match core::str::from_utf8(path_bytes) {
        Ok(_path) => FILE_READ_OK,
        Err(_) => 2,
    }
}

/// Abort on panic for the bare wasm64 target.
#[cfg(target_arch = "wasm64")]
#[panic_handler]
fn panic(_info: &PanicInfo<'_>) -> ! {
    loop {}
}
