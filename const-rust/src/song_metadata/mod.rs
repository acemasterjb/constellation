
use id3::{Tag as ID3Tag, TagLike};
use metaflac::Tag as VorbisTag;

use crate::Path;
use crate::local_types;
use crate::file_types;

pub(crate) fn get_song_metadata_vorbis(song_path: &Path) -> local_types::SongMetadata {
    let vorbis_tag: VorbisTag = VorbisTag::read_from_path(song_path.to_str().unwrap()).unwrap();

    let vorbis_comment: &metaflac::block::VorbisComment = vorbis_tag.vorbis_comments().unwrap();
    local_types::SongMetadata::new(
        (*vorbis_comment.artist().unwrap()).clone(),
        vorbis_comment.album().unwrap()[0].clone(),
        vorbis_comment.title().unwrap()[0].clone(),
        vorbis_comment.track().unwrap(),
    )
}

pub(crate) fn get_song_metadata_wav_mp3(
    song_path: &Path,
) -> local_types::SongMetadata {
    let id3_tag: ID3Tag = ID3Tag::read_from_path(song_path.to_str().unwrap()).unwrap();
    let artists: Vec<&str> = vec![id3_tag.artist().unwrap()];

    local_types::SongMetadata::new(
        artists
            .into_iter()
            .map(|artist: &str| String::from(artist))
            .collect(),
        String::from(id3_tag.album().unwrap()),
        String::from(id3_tag.title().unwrap()),
        id3_tag.track().unwrap(),
    )
}

pub(crate) fn get_song_container_metadata(song_path: &Path) -> ([Option<&str>; 2], Option<&str>) {
    (
        [Some("mp3"), Some("wav")],
        song_path.extension().unwrap().to_str(),
    )
}

pub(crate) fn get_songs_with_metadata(
    raw_songs: Vec<file_types::WalkDirEntry>,
) -> Vec<local_types::SongMetadata> {
    raw_songs
        .iter()
        .map(|song: &walkdir::DirEntry| {
            let song_path: &Path = song.path();
            let (id3_options, song_extension) = get_song_container_metadata(song_path);

            if id3_options.contains(&song_extension) {
                get_song_metadata_wav_mp3(song_path)
            } else {
                get_song_metadata_vorbis(song_path)
            }
        })
        .collect()
}
