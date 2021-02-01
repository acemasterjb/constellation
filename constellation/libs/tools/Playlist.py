def swap(Set, i1, i2):
    next_node = Set[i2].next[0]
    temp_node = Set[i1]
    prev_node = Set[i1 - 1]
    del Set[i2].next
    del prev_node.next
    prev_node.next = (Set[i2],)
    Set[i2].next = (temp_node,)
    del temp_node.next
    temp_node.next = (next_node,)


def partition(Set, start, stop, by):
    mid = (start + stop) / 2
    swap(Set, start, mid)
    pivot_i = start
    pivot_val = Set[start]

    for scan in range(start + 1, stop):
        attrs = {"album": (Set[scan].album, pivot_val.album),
                 "artist": (Set[scan].artist, pivot_val.artist),
                 "track": (Set[scan].track, pivot_val.track),
                 "name": (Set[scan], pivot_val)}

        if attrs[by][0] < attrs[by][1]:
            pivot_i += 1
            swap(Set, pivot_i, scan)

    swap(Set, start, pivot_i)
    return pivot_i


def quicksortsong(Set, start, stop, by):
    if start < stop:
        pivot = partition(Set, start, stop, by)
        quicksortsong(Set, start, pivot - 1, by)
        quicksortsong(Set, pivot + 1, stop, by)


class Node:
    def __init__(self, track, song):
        self.track = track
        self.song = song
        self.next = (None,)


class Playlist:
    """
        This is a data structure designed to hold song queues.

        tagobj - Tag object. Any object that supports attributes, such
                 as a dictionary, pandas or python object.
                 Only tagobj.album, tagobj.artist, tag.title and tag.track
                 is required.

        It is a linked-list-like data structure, where each node has a
        `track` and `song` property.

        Playlist.track - The track number for the song, stripped from song
                        metadata.
        Playlist.song  - Song name, stripped from song metadata.

        This class contains methods for sorting songs by artist, then album,
        then track.
    """

    def __init__(self, tagobj):
        self.tag = tagobj
        self.head = None
        self.s = 0

    def append(self, tag_value):
        track = tag_value.track
        song = tag_value.title
        new_node = Node(track, song)

        if not self.head:
            self.head = new_node
        else:
            index = self.head

            while index.next[0] and (track > index.track):
                index = index.next[0]

            if track > index.track:
                next_node = index.next[0]
                del index.next
                index.next = (new_node,)
                del new_node.next
                new_node.next = (next_node,)
            elif not index.next[0]:
                del index.next
                index.next = (new_node,)
            else:
                return

            self.s += 1

    def sort(self, by):
        quicksortsong(self, 0, self.s - 1, by)

    def __getitem__(self, index):
        if isinstance(index, slice):
            indices = range(*index.indices(self.s))
            return [self[i].value for i in indices]
        elif type(index) is not int:
            raise ValueError
            return
        elif abs(index) > self.s:
            raise IndexError
            return

        i = 0
        node = [None]
        node[0] = self.head

        if index <= -1:
            index = self.s + index

        while i != index:
            node[0] = node[0].next[0]
            i += 1

        try:
            """to catch index == self.s"""
            return node[0]
        except AttributeError:
            raise KeyError

    def __setitem__(self, index, value):
        node = [self.__getitem__(index)]
        node[0].value = value

    def __iter__(self):
        return self

    def __next__(self):
        if (self.s > 0) and (self.curr is None):
            raise StopIteration
        else:
            if type(self.curr.value) is bytes:
                self.curr.value = self.curr.value.decode('utf-8')
            current = self.curr
            self.curr = self.curr.next[0]
            return current

    def __delitem__(self, index):
        if not self.head:
            raise KeyError

        node = [self.head]
        prev = [None]
        i = 0

        if index < 0:
            if abs(index) > self.s:
                raise IndexError
                return
            else:
                index = self.s + index

        if index == 0:
            node[0] = self.head.next[0]
            del self.head
            self.head = node[0]
        else:
            while node[0] and i != index:
                prev[0] = node[0]
                node[0] = node[0].next[0]
                i += 1

            if node[0]:
                del prev[0].next
                prev[0].next = (node[0].next[0],)
                del node[0]
        self.s -= 1

    def __del__(self):
        node = self.head
        next_node = None

        while node:
            next_node = node.next[0]

            del node
            node = next_node
