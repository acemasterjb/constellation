use std::{thread};
use std::default::Default;
use std::io::{
    // Error, stdin,
    stdout
};
use std::env::{var};
use std::env::consts::{OS};
use std::fs::{FileType, read_dir};
use std::path::{Path, PathBuf};
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
use tui::layout::{Layout, Constraint, Direction};
use tui::text::{Span};
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

trait ADirEntry {
    fn get_file_name<'a>(&'a self) -> String;

    fn get_path_buf(&self) -> PathBuf;

    fn get_file_type(&self) -> FileType;

    fn get_extension<'a>(&'a self) -> String;
}

trait WidgetState {
    fn selected(&self) -> Option<usize>;

    fn select_item(&mut self, index: Option<usize>);
}

impl WidgetState for ListState {
    fn selected(&self) -> Option<usize>{
        self.selected()
    }

    fn select_item(&mut self, index: Option<usize>) {
        self.select(index)
    }
}
impl WidgetState for TableState {
    fn selected(&self) -> Option<usize>{
        self.selected()
    }

    fn select_item(&mut self, index: Option<usize>) {
        self.select(index)
    }
}

// List Events to display.
struct Events<T: WidgetState + Default> {
    // `items` is the state managed by your application.
    items: Vec<String>,
    // `state` is the state that can be modified by the UI. It stores the index of the selected
    // item as well as the offset computed during the previous draw call (used to implement
    // natural scrolling).
    state: T
}

impl<T> Events<T>
where 
    T: WidgetState + Default
{
    fn new(items: Vec<String>) -> Events<T> {
        Events {
            items,
            state: T::default(),
        }
    }

    pub fn set_items(&mut self, items: Vec<String>) {
        self.items = items;
        // We reset the state as the associated items have changed. This effectively reset
        // the selection as well as the stored offset.
        self.state = T::default();
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
        self.state.select_item(Some(i));
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
        self.state.select_item(Some(i));
    }

    // Unselect the currently selected item if any. The implementation of `ListState` makes
    // sure that the stored offset is also reset.
    pub fn unselect(&mut self) {
        self.state.select_item(None);
    }
}

impl ADirEntry for WalkDirEntry {
    fn get_file_name<'a>(&'a self) -> String{
        String::from(self.file_name().to_str().unwrap())
    }

    fn get_path_buf(&self) -> PathBuf{
        self.path().to_path_buf()
    }

    fn get_file_type(&self) -> FileType{
        self.file_type()
    }

    fn get_extension<'a>(&'a self) -> String{
        String::from(
            self.path().extension()
                .unwrap()
                .to_str()
                .unwrap()
            )
    }
}

impl ADirEntry for std::fs::DirEntry {
    fn get_file_name(&self) -> String {
        String::from(self.file_name().to_str().unwrap())
    }

    fn get_path_buf(&self) -> PathBuf{
        self.path().to_path_buf()
    }

    fn get_file_type(&self) -> FileType{
        self.file_type().unwrap()
    }

    fn get_extension(&self) -> String {
        String::from(
            self.path().extension()
                .unwrap()
                .to_str()
                .unwrap()
            )
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
        artist: Vec<String>,
        album: String,
        name: String,
        queue: u32
    ) -> SongMetadata {
        SongMetadata{
            artist: artist,
            album: album,
            name: name,
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
    // let music_section = Block::default()
    // .borders(Borders::ALL)
    // .style(Style::default().fg(Color::White))
    // .title("Music")
    // .border_type(BorderType::Rounded);

    // let song_items: Vec<_> = songs.iter()
    //     .map(
    //         | song |{
    //             ListItem::new(Spans::from(vec![Span::styled(
    //                 song.path().to_string_lossy(),
    //                 Style::default()
    //             )]))
    //         }
    //     ).collect();
        
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
                
                let artists = vec![id3_tag.artist().unwrap()];
                SongMetadata::new(
                    artists.into_iter().map(| artist | String::from(artist)).collect(),
                    String::from(id3_tag.album().unwrap()),
                    String::from(id3_tag.title().unwrap()),
                    id3_tag.track().unwrap()
                )
            } else {
                let vorbis_tag = VorbisTag::read_from_path(
                    song_path.to_str().unwrap()
                ).unwrap();

                let vorbis_comment = vorbis_tag.vorbis_comments().unwrap();
                SongMetadata::new(
                    (*vorbis_comment.artist().unwrap()).clone(),
                    vorbis_comment.album().unwrap()[0].clone(),
                    vorbis_comment.title().unwrap()[0].clone(),
                    vorbis_comment.track().unwrap()
                )
            }
        }
    ).collect();

    let song_details_rows: Vec<Row> = songs_with_meta.iter().map(
        | song |{
            Row::new(vec![
                Cell::from(Span::raw(song.queue.to_string())),
                Cell::from(Span::raw(song.album.to_string())),
                Cell::from(Span::raw(song.artist.join(","))),
                Cell::from(Span::raw(song.name.to_string())),
            ])
        }
    ).collect();

    Table::new(
        song_details_rows
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

    let mut events: Events<ListState> = Events::new(
        paths.map(| path: Result<std::fs::DirEntry, std::io::Error> | {
            String::from(path.unwrap().path().to_str().unwrap())
        }).collect()
    );
    events.state.select(Some(0));  // select the first item by default
    // let mut curr_path = home.to_path_buf();
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
                    ).map(|i| ListItem::new(
                        Path::new(i.as_str())
                            .file_name().unwrap().to_str().unwrap()
                        )
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
                    let selected_item = &events.items[events.state.selected().unwrap_or(0)];
                    let selected_path = Path::new(selected_item).to_path_buf();

                    if selected_path.parent().unwrap().eq(home) {
                        events.unselect();
                        terminal.clear()?;
                        disable_raw_mode()?;
                        terminal.show_cursor()?;
                        break;
                    } else {
                        let current_path = selected_path.parent().unwrap();
                        let upper_level = current_path.parent().unwrap();
                        events.set_items(
                            read_dir(upper_level).unwrap()
                            .map(
                                | path: Result<std::fs::DirEntry, std::io::Error> |
                                {
                                    String::from(path.unwrap().path().to_str().unwrap())
                                }
                            ).collect()
                        );
                    }
                }
                KeyCode::Down => {
                    events.next()
                }
                KeyCode::Up => {
                    events.previous()
                }
                KeyCode::Enter => {
                    let selected_item = &events.items[events.state.selected().unwrap_or(0)];
                    let selected_path = Path::new(selected_item).to_path_buf();
                    // println!("Path: {}", selected_path.to_str().unwrap());


                    if selected_path.as_path().is_dir() {
                        events = Events::new(
                            read_dir(selected_path).unwrap()
                            .map(
                                | entry: Result<std::fs::DirEntry, std::io::Error> |
                                {
                                    String::from(entry.unwrap().path().to_str().unwrap())
                                }
                            ).collect()
                        );
                    }
                    events.state.select(Some(0));
                }
                KeyCode::Char('c') => {
                    let selected_item = &events.items[events.state.selected().unwrap_or(0)];

                    let selected_path = Path::new(selected_item).to_path_buf();
                    if selected_path.is_dir(){
                        let walker = WalkDir::new(selected_item).into_iter();

                        let filterd_entries = walker.filter_entry(
                            | entry |{
                                !is_hidden(entry)
                            }
                        );

                        let collected_entries: Vec<WalkDirEntry> = filterd_entries.map(
                            | entry: Result<WalkDirEntry, WalkDirError> | {
                                entry.unwrap()
                            }
                        ).collect();

                        events = Events::new(
                            collected_entries.into_iter()
                                .filter(
                                    | entry: &WalkDirEntry | {
                                        !is_a_dir(entry) &&
                                        is_a_music_file(entry)
                                    }
                                ).map(
                                    | path: WalkDirEntry | {
                                        String::from(path.path().to_str().unwrap())
                                    }
                                ).collect()
                        )
                    }
                }
                _ => {}
            },
            Event::Tick => {}
        }
    };

    Ok(())
}
