use std::{thread};
use std::error::Error;
use std::io::{
    // Error, stdin,
    stdout
};
use std::env::{var};
use std::env::consts::{OS};
use std::fs::{read_dir};
use std::path::{Path};
use std::sync::mpsc;
use std::time::{Duration, Instant};

use crossterm::{
    event::{self, Event as CEvent, KeyCode},
    terminal::{disable_raw_mode, enable_raw_mode},
};
use id3::{Tag as ID3Tag, TagLike};
use metaflac::{Tag as VorbisTag};
use tui::{
    backend::CrosstermBackend,
    Terminal,
    style::{Color, Style, Modifier}
};
use tui::layout::{Layout, Constraint, Direction, Rect};
use tui::text::{Span, Spans};
use tui::widgets::{
    Block, Borders, BorderType,
    Cell, List, ListItem,
    ListState, Row, Table,
    TableState
};
use walkdir::{DirEntry as WalkDirEntry, WalkDir, Error as WalkDirError};

enum Event<I> {
    Input(I),
    Tick,
}

#[derive(Copy, Clone, Debug)]
enum Window {
    Directory,
    Music
}

enum ConstDirEntry {
    StdDirEntry(std::fs::DirEntry),
    WlkDirEntry(WalkDirEntry)
}


// List Events to display.
struct Events {
    // `items` is the state managed by your application.
    items: Vec<ConstDirEntry>,
    // `state` is the state that can be modified by the UI. It stores the index of the selected
    // item as well as the offset computed during the previous draw call (used to implement
    // natural scrolling).
    state: ListState
}

impl Events {
    fn new(items: Vec<ConstDirEntry>) -> Events {
        Events {
            items,
            state: ListState::default(),
        }
    }

    pub fn set_items(&mut self, items: Vec<ConstDirEntry>) {
        self.items = items;
        // We reset the state as the associated items have changed. This effectively reset
        // the selection as well as the stored offset.
        self.state = ListState::default();
    }

    // Select the next item. This will not be reflected until the widget is drawn in the
    // `Terminal::draw` callback using `Frame::render_stateful_widget`.
    pub fn next(&mut self) {
        let i = match self.state.selected() {
            Some(i) => {
                if i >= self.items.len() - 1 {
                    0
                } else {
                    i + 1
                }
            }
            None => 0,
        };
        self.state.select(Some(i));
    }

    // Select the previous item. This will not be reflected until the widget is drawn in the
    // `Terminal::draw` callback using `Frame::render_stateful_widget`.
    pub fn previous(&mut self) {
        let i = match self.state.selected() {
            Some(i) => {
                if i == 0 {
                    self.items.len() - 1
                } else {
                    i - 1
                }
            }
            None => 0,
        };
        self.state.select(Some(i));
    }

    // Unselect the currently selected item if any. The implementation of `ListState` makes
    // sure that the stored offset is also reset.
    pub fn unselect(&mut self) {
        self.state.select(None);
    }
}

// Song Metadata
struct SongMetadata {
    artist: Vec<String>,
    album: String,
    name: String,
    queue: u32
}

impl SongMetadata {
    fn new (
        artist: &Vec<String>,
        album: &String,
        name: &String,
        queue: u32
    ) -> SongMetadata {
        SongMetadata{
            artist: *artist,
            album: *album,
            name: *name,
            queue
        }
    }
}

impl From<Window> for usize {
    fn from(input: Window) -> usize {
        match input {
            Window::Directory => 0,
            Window::Music => 1
        }
    }
}

fn is_hidden(entry: &WalkDirEntry) -> bool {
    entry.file_name()
         .to_str()
         .map(|s| s.starts_with("."))
         .unwrap_or(false)
}

fn is_a_music_file(entry: &WalkDirEntry) -> bool {
    let file_extension = entry.path()
         .extension()
         .unwrap()
         .to_str()
         .unwrap();
    
    let song_extensions = ["flac", "mp3", "wav"];

    song_extensions.contains(&file_extension)
}

fn is_a_dir(entry: &WalkDirEntry) -> bool {
    entry.file_type().is_dir()
}

fn render_music<'a>(songs: Vec<WalkDirEntry>) -> Table<'a> {
    let music_section = Block::default()
        .borders(Borders::ALL)
        .style(Style::default().fg(Color::White))
        .title("Music")
        .border_type(BorderType::Rounded);

    let song_items: Vec<_> = songs.iter()
        .map(
            | song |{
                ListItem::new(Spans::from(vec![Span::styled(
                    song.path().to_string_lossy(),
                    Style::default()
                )]))
            }
        ).collect();
        
    let songs_with_meta: Vec<SongMetadata> = songs.iter()
    .map(
        | song |{
            let id3_options = [Some("mp3"), Some("wav")];
            let song_path = song.path();
            let song_extension = song_path.extension().unwrap().to_str();
            if id3_options.contains(&song_extension){
                let id3_tag = ID3Tag::read_from_path(
                    song_path.to_str().unwrap()
                ).unwrap();
                
                SongMetadata::new(
                    vec![String::from(id3_tag.artist().unwrap())],
                    &String::from(id3_tag.album().unwrap()),
                    &String::from(id3_tag.title().unwrap()),
                    id3_tag.track().unwrap()
                )
            } else {
                let vorbis_tag = VorbisTag::read_from_path(
                    song_path.to_str().unwrap()
                ).unwrap();

                let vorbis_comment = vorbis_tag.vorbis_comments().unwrap();
                SongMetadata::new(
                    vorbis_comment.artist().unwrap(),
                    &vorbis_comment.album().unwrap()[0],
                    &vorbis_comment.title().unwrap()[0],
                    vorbis_comment.track().unwrap()
                )
            }
        }
    ).collect();
    
    Table::new(
        songs_with_meta.iter().map(
            | song |{
                Row::new(vec![
                    Cell::from(Span::raw(song.queue.to_string())),
                    Cell::from(Span::raw(song.album)),
                    Cell::from(Span::raw(song.artist.join(","))),
                    Cell::from(Span::raw(song.name)),
                ])
            }
        ).collect()
    )
    .header(Row::new(
        vec![
            Cell::from(
                Span::styled("#", Style::default().add_modifier(Modifier::BOLD))
            ),
            Cell::from(
                Span::styled("Album", Style::default().add_modifier(Modifier::BOLD))
            ),
            Cell::from(
                Span::styled("Artist", Style::default().add_modifier(Modifier::BOLD))
            ),
            Cell::from(
                Span::styled("Name", Style::default().add_modifier(Modifier::BOLD))
            )
        ]
    ))
    .block(
        Block::default()
            .borders(Borders::ALL)
            .style(Style::default().fg(Color::White))
            .title("Music Details")
            .border_type(BorderType::Rounded)
    )
    .widths(&[
        Constraint::Percentage(5),
        Constraint::Percentage(25),
        Constraint::Percentage(15),
        Constraint::Percentage(35),
    ])
}

fn main()
    -> Result<(), Box<dyn std::error::Error>>
{
    let home = if OS == "windows" {
        var("USERPROFILE").unwrap() } else { var("HOME").unwrap()
    };
    let home = Path::new(&home);
    enable_raw_mode().expect("raw mode");

    let (tx, rx) = mpsc::channel();
    let tick_rate = Duration::from_millis(200);
    thread::spawn(move || {
        let mut last_tick = Instant::now();
        loop {
            let timeout = tick_rate
                .checked_sub(last_tick.elapsed())
                .unwrap_or_else(|| Duration::from_secs(0));

            if event::poll(timeout).expect("poll works") {
                if let CEvent::Key(key) = event::read().expect("can read events") {
                    tx.send(Event::Input(key)).expect("can send events");
                }
            }

            if last_tick.elapsed() >= tick_rate {
                if let Ok(_) = tx.send(Event::Tick) {
                    last_tick = Instant::now();
                }
            }
        }
    });

    let stdout = stdout();
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    terminal.clear()?;

    let working_dir = home.to_path_buf();
    let paths: std::fs::ReadDir = read_dir(working_dir).unwrap();

    let mut events = Events::new(
        paths.map(| path: Result<std::fs::DirEntry, std::io::Error> | {
            ConstDirEntry::StdDirEntry(path.unwrap())
        }).collect()
    );
    events.state.select(Some(0));  // select the first item by default
    let mut curr_path = home.to_path_buf();
    let mut active_window = Window::Directory;

    loop {
        terminal.draw(|frame| {
            let size = frame.size();

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .margin(2)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Min(2),
                    Constraint::Length(3)
                ].as_ref(),).split(size)
                
            ;

            match active_window {
                Window::Directory => {
                    let items: Vec<ListItem>= events.items.iter(
                    ).map(
                        |i| {
                            match i {
                                ConstDirEntry::StdDirEntry (i) => {
                                    ListItem::new(i.file_name().into_string().unwrap())
                                }
                                ConstDirEntry::WlkDirEntry (j) => {
                                    ListItem::new(j.file_name().to_str().unwrap())
                                }
                            }
                            
                        }
                    ).collect();
                    let lister = Block::default()
                    .title("Pick your music directory")
                    .borders(Borders::ALL)
                    .border_type(BorderType::Rounded);
                    let list = List::new(items)
                        .block(lister)
                        .highlight_style(
                            Style::default()
                            .bg(Color::White)
                            .fg(Color::Black)
                        );
                    frame.render_stateful_widget(list, chunks[1], &mut events.state);
                }
                Window::Music => {
                    // frame.render_stateful_widget(
                    //     render_music(
                    //         events.items.iter().map(
                    //             | event |{
                    //                 ConstDirEntry::WlkDirEntry(event)
                    //             }
                    //         )
                    //     ),
                    //     chunks[1],

                    // )
                }
            }
        })?;

        match rx.recv()? {
            Event::Input(event) => match event.code {
                KeyCode::Char('q') => {
                    let home = home;
                    if curr_path.eq(&home) {
                        events.unselect();
                        terminal.clear()?;
                        disable_raw_mode()?;
                        terminal.show_cursor()?;
                        break;
                    } else {
                        let upper_level = curr_path.parent().unwrap();
                        events.set_items(
                            read_dir(upper_level).unwrap()
                            .map(
                                | path: Result<std::fs::DirEntry, std::io::Error> |
                                {
                                    ConstDirEntry::StdDirEntry(path.unwrap())
                                }
                            ).collect()
                        );
                        curr_path = upper_level.to_path_buf();
                    }
                }
                KeyCode::Down => {
                    events.next()
                }
                KeyCode::Up => {
                    events.previous()
                }
                KeyCode::Enter => {
                    let selected_item = &events.items[events.state.selected().unwrap()];
                    match selected_item {
                        ConstDirEntry::StdDirEntry(i) => {
                            curr_path = i.path();
                            if i.path().is_dir() {
                                events = Events::new(
                                    read_dir(i.path()).unwrap()
                                    .map(
                                        | path: Result<std::fs::DirEntry, std::io::Error> |
                                        {
                                            ConstDirEntry::StdDirEntry(path.unwrap())
                                        }
                                    ).collect()
                                );
                            }
                            events.state.select(Some(0));
                        }
                        ConstDirEntry::WlkDirEntry(j) => {
                            curr_path = j.path().to_path_buf();
                            if j.path().is_dir() {
                                events = Events::new(
                                    read_dir(j.path()).unwrap()
                                    .map(
                                        | path: Result<std::fs::DirEntry, std::io::Error> |
                                        {
                                            ConstDirEntry::StdDirEntry(path.unwrap())
                                        }
                                    ).collect()
                                )
                            }
                            events.state.select(Some(0));
                        }
                    }
                }
                KeyCode::Char('c') => {
                    let selected_item = &events.items[events.state.selected().unwrap()];
                    match selected_item {
                        ConstDirEntry::StdDirEntry(i) => {
                            let selected_path = i.path();
                            if selected_path.is_dir(){
                                let walker = WalkDir::new(
                                    selected_path.to_str().unwrap()
                                ).into_iter();

                                let filterd_entries= walker.filter_entry(
                                    | entry | {
                                        !is_hidden(entry)
                                    }
                                );

                                let collected_entries: Vec<WalkDirEntry> = filterd_entries.map(
                                    | entry: Result<WalkDirEntry, WalkDirError> | { 
                                    entry.unwrap()
                                }).collect();
                                events = Events::new(
                                    collected_entries.into_iter()
                                    .filter(
                                        | entry: &WalkDirEntry |
                                        {
                                            !is_a_dir(entry) &&
                                            is_a_music_file(entry)
                                        }
                                    )
                                    .map(
                                        | path: WalkDirEntry |
                                        {
                                            ConstDirEntry::WlkDirEntry(path)
                                        }
                                    ).collect()
                                );

                            };
                            active_window = Window::Music;
                        }
                        ConstDirEntry::WlkDirEntry(j) => {
                            let selected_path = j.path();
                            if selected_path.is_dir() {
                                let walker = WalkDir::new(
                                    selected_path.to_str().unwrap()
                                ).into_iter();

                                let filterd_entries= walker.filter_entry(
                                    | entry | {
                                        !is_hidden(entry)
                                    }
                                );

                                let collected_entries: Vec<WalkDirEntry> = filterd_entries.map(
                                    | entry: Result<WalkDirEntry, WalkDirError> | { 
                                    entry.unwrap()
                                }).collect();
                                events = Events::new(
                                    collected_entries.into_iter()
                                    .filter(
                                        | entry: &WalkDirEntry |
                                        {
                                            !is_a_dir(entry) &&
                                            is_a_music_file(entry)
                                        }
                                    )
                                    .map(
                                        | path: WalkDirEntry |
                                        {
                                            ConstDirEntry::WlkDirEntry(path)
                                        }
                                    ).collect()
                                );
                            };
                            active_window = Window::Music;
                        }
                    }
                }
                _ => {}
            },
            Event::Tick => {}
        }
    };

    Ok(())
}
