use std::default::Default;
use std::env::consts::OS;
use std::env::var;
use std::fs::{read_dir, File};
use std::io::{stdout, BufReader};
use std::path::Path;
use std::sync::mpsc;
use std::thread::{self};
use std::time::{Duration, Instant};

use crossterm::{
    event::{self, Event as CEvent, KeyCode},
    terminal::{disable_raw_mode, enable_raw_mode},
};
use rodio::{Decoder, OutputStream, Sink};
use tui::layout::{Constraint, Direction, Layout};
use tui::text::Span;
use tui::widgets::{
    Block, BorderType, Borders, Cell, List, ListItem, ListState, Row, Table, TableState,
};
use tui::{
    backend::CrosstermBackend,
    style::{Color, Modifier, Style},
    Terminal,
};
use walkdir::{Error as WalkDirError, WalkDir};

pub mod file_types;
pub mod local_types;
pub mod song_metadata;

fn get_songs_as_rows(songs_with_metadata: Vec<local_types::SongMetadata>) -> Vec<Row<'static>> {
    songs_with_metadata
        .iter()
        .map(|song| {
            Row::new(vec![
                Cell::from(Span::raw(song.queue.to_string())),
                Cell::from(Span::raw(song.album.to_string())),
                Cell::from(Span::raw(song.artist.join(","))),
                Cell::from(Span::raw(song.name.to_string())),
            ])
        })
        .collect()
}

fn render_music<'a>(songs: Vec<file_types::WalkDirEntry>) -> Table<'a> {
    let songs_with_metadata: Vec<local_types::SongMetadata> = song_metadata::get_songs_with_metadata(songs);

    let song_detail_rows: Vec<Row> = get_songs_as_rows(songs_with_metadata);

    Table::new(song_detail_rows)
        .highlight_style(Style::default().bg(Color::White).fg(Color::Black))
        .header(Row::new(vec![
            Cell::from(Span::styled(
                "#",
                Style::default().add_modifier(Modifier::BOLD),
            )),
            Cell::from(Span::styled(
                "Album",
                Style::default().add_modifier(Modifier::BOLD),
            )),
            Cell::from(Span::styled(
                "Artist",
                Style::default().add_modifier(Modifier::BOLD),
            )),
            Cell::from(Span::styled(
                "Name",
                Style::default().add_modifier(Modifier::BOLD),
            )),
        ]))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .style(Style::default().fg(Color::White))
                .title("Library")
                .border_type(BorderType::Rounded),
        )
        .widths(&[
            Constraint::Percentage(5),
            Constraint::Percentage(25),
            Constraint::Percentage(15),
            Constraint::Percentage(35),
        ])
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let home = if OS == "windows" {
        var("USERPROFILE").unwrap()
    } else {
        var("HOME").unwrap()
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

            if event::poll(timeout).expect("polling for events to work") {
                if let CEvent::Key(key) = event::read().expect("crossterm to read events") {
                    tx.send(local_types::Event::Input(key))
                        .expect("const to send events");
                }
            }

            if last_tick.elapsed() >= tick_rate {
                if let Ok(_) = tx.send(local_types::Event::Tick) {
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

    let mut music_events: local_types::Events<TableState> = local_types::Events::default();
    music_events.state = TableState::default();
    let mut events: local_types::Events<ListState> = local_types::Events::new(
        paths
            .filter_map(|path: Result<std::fs::DirEntry, std::io::Error>| {
                let entry = String::from(path.unwrap().path().to_str().unwrap());

                if !entry.contains(".") {
                    Some(entry)
                } else {
                    None
                }
            })
            .collect(),
    );
    events.state.select(Some(0)); // select the first item by default
    let mut collected_entries: Vec<file_types::WalkDirEntry> = vec![];
    let mut music_path: String;
    let mut active_window = local_types::Window::Directory;

    let (music_player_tx, music_player_rx) = mpsc::channel();
    thread::spawn(move || {
        let (_stream, stream_handle) = OutputStream::try_default().unwrap();
        let (mut music_sink, _) = Sink::new_idle();

        loop {
            match music_player_rx.recv() {
                Ok((Some(a), Some(b))) => {
                    if a == "play" {
                        if !music_sink.empty() {
                            if music_sink.is_paused() {
                                music_sink.play();
                            } else {
                                music_sink.pause();
                            }
                        } else {
                            music_sink = Sink::try_new(&stream_handle).unwrap();
                            music_sink.append(b);
                        }
                    }
                }
                Ok((Some(a), None)) => {
                    if a == "stop" {
                        if !music_sink.empty() {
                            music_sink.stop();
                        }
                    }
                }
                Ok((None, _)) => {}
                Err(_) => {}
            }
        }
    });

    loop {
        terminal.draw(|frame| {
            let size = frame.size();

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .margin(2)
                .constraints(
                    [
                        Constraint::Length(3),
                        Constraint::Min(2), // dir/music selector
                        Constraint::Length(3),
                    ]
                    .as_ref(),
                )
                .split(size);

            match active_window {
                local_types::Window::Directory => {
                    let items: Vec<ListItem> = events
                        .items
                        .iter()
                        .map(|i| {
                            ListItem::new(
                                Path::new(i.as_str()).file_name().unwrap().to_str().unwrap(),
                            )
                        })
                        .collect();

                    let list_block = Block::default()
                        .title("Pick your music directory")
                        .borders(Borders::ALL)
                        .border_type(BorderType::Rounded);
                    let list = List::new(items)
                        .block(list_block)
                        .highlight_style(Style::default().bg(Color::White).fg(Color::Black));

                    frame.render_stateful_widget(list, chunks[1], &mut events.state);
                }
                local_types::Window::Music => frame.render_stateful_widget(
                    render_music(collected_entries.clone()),
                    chunks[1],
                    &mut music_events.state,
                ),
            }
        })?;

        match rx.recv()? {
            local_types::Event::Input(event) => match event.code {
                // quit the program
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
                            read_dir(upper_level)
                                .unwrap()
                                .filter_map(|path: Result<std::fs::DirEntry, std::io::Error>| {
                                    let entry =
                                        String::from(path.unwrap().path().to_str().unwrap());

                                    if !entry.contains(".") {
                                        Some(entry)
                                    } else {
                                        None
                                    }
                                })
                                .collect(),
                        );
                    }
                }
                // go down an item
                KeyCode::Down => match active_window {
                    local_types::Window::Directory => events.next(),
                    local_types::Window::Music => music_events.next(),
                },
                // go up an item
                KeyCode::Up => match active_window {
                    local_types::Window::Directory => events.previous(),
                    local_types::Window::Music => music_events.previous(),
                },
                // enter a directory
                KeyCode::Enter => match active_window {
                    local_types::Window::Directory => {
                        let selected_item = &events.items[events.state.selected().unwrap_or(0)];
                        let selected_path = Path::new(selected_item).to_path_buf();

                        if selected_path.as_path().is_dir() {
                            events = local_types::Events::new(
                                read_dir(selected_path)
                                    .unwrap()
                                    .map(|entry: Result<std::fs::DirEntry, std::io::Error>| {
                                        String::from(entry.unwrap().path().to_str().unwrap())
                                    })
                                    .collect(),
                            );
                        }
                        events.state.select(Some(0));
                    }

                    local_types::Window::Music => {}
                },
                // choose music dir; scan it for songs
                KeyCode::Char('c') => match active_window {
                    local_types::Window::Directory => {
                        let selected_item = &events.items[events.state.selected().unwrap_or(0)];
                        music_path = selected_item.to_string();

                        if Path::new(&music_path).to_path_buf().is_dir() {
                            let walker = WalkDir::new(&music_path).into_iter();

                            let filterd_entries =
                                walker.filter_entry(|entry| !file_types::is_hidden(entry));

                            let intermediate_entries: Vec<file_types::WalkDirEntry> =
                                filterd_entries
                                    .map(|entry: Result<file_types::WalkDirEntry, WalkDirError>| {
                                        entry.unwrap()
                                    })
                                    .collect();

                            collected_entries = intermediate_entries
                                .into_iter()
                                .filter_map(|entry: file_types::WalkDirEntry| {
                                    if !file_types::is_a_dir(&entry)
                                        && file_types::is_a_music_file(&entry)
                                    {
                                        Some(entry)
                                    } else {
                                        None
                                    }
                                })
                                .collect();

                            music_events = local_types::Events::new(
                                collected_entries
                                    .clone()
                                    .into_iter()
                                    .map(|entry: file_types::WalkDirEntry| {
                                        String::from(entry.path().to_str().unwrap())
                                    })
                                    .collect(),
                            );
                        }

                        active_window = local_types::Window::Music;
                        music_events.state.select(Some(0));
                    }
                    local_types::Window::Music => {}
                },
                // pause/play as song
                KeyCode::Char('p') => match active_window {
                    local_types::Window::Directory => {}
                    local_types::Window::Music => {
                        let selected_item =
                            &music_events.items[music_events.state.selected().unwrap_or(0)];
                        let music_file = BufReader::new(File::open(selected_item).unwrap());

                        let source = Decoder::new(music_file).unwrap();

                        music_player_tx.send((Some("play"), Some(source)))?;
                    }
                },
                // stop the music player
                KeyCode::Char('s') => match active_window {
                    local_types::Window::Directory => {}
                    local_types::Window::Music => {
                        music_player_tx.send((Some("stop"), None))?;
                    }
                },
                _ => {}
            },
            local_types::Event::Tick => {}
        }
    }

    Ok(())
}
