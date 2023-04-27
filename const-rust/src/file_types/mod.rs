pub use walkdir::DirEntry as WalkDirEntry;

pub fn is_hidden(entry: &WalkDirEntry) -> bool {
    entry.file_name()
         .to_str()
         .map(|s: &str| s.starts_with("."))
         .unwrap_or(false)
}

pub fn is_a_music_file(entry: &WalkDirEntry) -> bool {
    let file_extension: &str = entry.path()
         .extension()
         .unwrap()
         .to_str()
         .unwrap();
    
    let song_extensions: [&str; 3] = ["flac", "mp3", "wav"];

    song_extensions.contains(&file_extension)
}

pub fn is_a_dir(entry: &WalkDirEntry) -> bool {
    entry.file_type().is_dir()
}