#![no_std]

extern crate alloc;

#[no_mangle]
pub extern "C" fn file_read(path_ptr: u64, path_len: u64) -> u64 {
    let path = unsafe { core::slice::from_raw_parts(path_ptr as *const u8, path_len as usize) };
    let _ok = core::str::from_utf8(path);
    42
}