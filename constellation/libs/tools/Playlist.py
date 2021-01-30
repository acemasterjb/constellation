class Node:
    def __init__(self, track, song):
        self.track = track
        self.song = song
        self.next = (None,)


def swap(Set, i1, i2):
    temp = Set[i1]
    Set[i1] = Set[i2]
    Set[i2] = temp


def partition(Set, start, stop):
    mid = (start + stop) / 2
    swap(Set, start, mid)
    pivot_i = start
    pivot_val = ord(Set[start])

    for scan in range(start + 1, stop):
        if ord(Set[scan]) < pivot_val:
            pivot_i += 1
            swap(Set, pivot_i, scan)

    swap(Set, start, pivot_i)
    return pivot_i


def sort_alpha(Set, start, stop):
    if start < stop:
        pivot = partition(Set, start, stop)
        sort_alpha(Set, start, pivot - 1)
        sort_alpha(Set, pivot + 1, stop)


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
        pass

    def __iter__(self):
        return self

    def __next__(self):

