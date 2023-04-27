use tui::widgets::{ListState, TableState};

pub enum Event<I> {
    Input(I),
    Tick,
}

#[derive(Copy, Clone, Debug)]
pub enum Window {
    Directory,
    Music,
}

pub trait WidgetState {
    fn selected(&self) -> Option<usize>;

    fn select_item(&mut self, index: Option<usize>);
}

impl WidgetState for ListState {
    fn selected(&self) -> Option<usize> {
        self.selected()
    }

    fn select_item(&mut self, index: Option<usize>) {
        self.select(index)
    }
}
impl WidgetState for TableState {
    fn selected(&self) -> Option<usize> {
        self.selected()
    }

    fn select_item(&mut self, index: Option<usize>) {
        self.select(index)
    }
}

// List Events to display.
#[derive(Default)]
pub(crate) struct Events<T: WidgetState + Default> {
    // `items` is the state managed by your application.
    pub items: Vec<String>,
    // `state` is the state that can be modified by the UI. It stores the index of the selected
    // item as well as the offset computed during the previous draw call (used to implement
    // natural scrolling).
    pub state: T,
}

impl<T> Events<T>
where
    T: WidgetState + Default,
{
    pub(crate) fn new(items: Vec<String>) -> Events<T> {
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
        let i: usize = match self.state.selected() {
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
        let i: usize = match self.state.selected() {
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

// // Music Player
// struct Player {

// }

// Song Metadata
pub(crate) struct SongMetadata {
    pub artist: Vec<String>,
    pub album: String,
    pub name: String,
    pub queue: u32,
}

impl SongMetadata {
    pub(crate) fn new(artist: Vec<String>, album: String, name: String, queue: u32) -> SongMetadata {
        SongMetadata {
            artist,
            album,
            name,
            queue,
        }
    }
}

impl From<Window> for usize {
    fn from(input: Window) -> usize {
        match input {
            Window::Directory => 0,
            Window::Music => 1,
        }
    }
}
