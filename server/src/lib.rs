//! Boom Online (VBNB_116) server emulator. Spec: docs/ + tools/fakeserver.py (the Python fake server this crate
//! replaces); every S->C builder is checked byte for byte against it by tests/golden.rs.

pub mod hub;
pub mod maps;
pub mod packets;
pub mod proto;
pub mod session;
pub mod strings;
