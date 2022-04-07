use std::{thread};
use std::io::{
    // Error, stdin,
    stdout
};
use std::env::{var};
use std::env::consts::{OS};
use std::fs::{read_dir};
use std::path::Path;
use std::sync::mpsc;
use std::time::{Duration, Instant};

use crossterm::{
    event::{self, Event as CEvent, KeyCode},
    terminal::{disable_raw_mode, enable_raw_mode},
};
use tui::{
    backend::CrosstermBackend,
    layout::Constraint,
    layout::Direction,
    layout::Layout,
    Terminal,
    style::{Style, Color}
};
use tui::widgets::{
    // Widget,
    Block, Borders, BorderType, List, ListItem, ListState};
// use tui::layout::{Layout, Constraint, Direction};

enum Event<I> {
    Input(I),
    Tick,
}

#[derive(Copy, Clone, Debug)]
enum Window {
    Directory,
    Music
}

// List Events to display.
struct Events {
    // `items` is the state managed by your application.
    items: Vec<std::fs::DirEntry>,
    // `state` is the state that can be modified by the UI. It stores the index of the selected
    // item as well as the offset computed during the previous draw call (used to implement
    // natural scrolling).
    state: ListState
}

impl Events {
    fn new(items: Vec<std::fs::DirEntry>) -> Events {
        Events {
            items,
            state: ListState::default(),
        }
    }

    pub fn set_items(&mut self, items: Vec<std::fs::DirEntry>) {
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

impl From<Window> for usize {
    fn from(input: Window) -> usize {
        match input {
            Window::Directory => 0,
            Window::Music => 1
        }
    }
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
            path.unwrap()
        }).collect()
    );
    let mut curr_path = home.to_path_buf();

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

            let items: Vec<ListItem>= events.items.iter(
                ).map(
                    |i| ListItem::new(i.file_name().into_string().unwrap())
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
                                    path.unwrap()
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
                    curr_path = selected_item.path();
                    if selected_item.path().is_dir() {
                        events = Events::new(
                            read_dir(selected_item.path()).unwrap()
                            .map(
                                | path: Result<std::fs::DirEntry, std::io::Error> |
                                {
                                    path.unwrap()
                                }
                            ).collect()
                        );
                    }
                }
                _ => {}
            },
            Event::Tick => {}
        }
    };

    Ok(())
}
