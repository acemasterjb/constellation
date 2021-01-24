class ListNode:
    def __init__(self, value):
        self.value = value
        self.next = [None]
        self.down = [None]
        self.up = [None]


class DirectoryList:
    def __init__(self):
        self.head = None
        self.s = 0

    def size(self):
        return self.s

    def append(self, value):
        if type(value) is str:
            value = bytes(value, 'utf-8')
        elif type(value) is int:
            value = float(value)

        new_node = ListNode(value)

        if not self.head:
            self.head = new_node
        else:
            index = self.head

            while (index.next[0]):
                index = index.next[0]

            index.next[0] = new_node
        self.s += 1

    def pop(self, index=-1):
        popped = self[index]
        del self[index]
        return popped

    def display(self):
        index = [None]
        i = 0

        index[0] = self.head

        while index[0]:
            print(self[i].value)
            index[0] = index[0].next[0]
            i += 1

    def __len__(self):
        return self.s

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
            if type(node[0].value) is bytes:
                node[0].value = node[0].value.decode('utf-8')
        except Exception:
            pass

        try:
            """to catch index == self.s"""
            return node[0]
        except AttributeError:
            raise KeyError

    def __setitem__(self, index, value):
        node = [self.__getitem__(index)]
        node[0].value = value

    def __delitem__(self, index):
        if not self.head:
            raise KeyError

        node = [self.head]
        prev = [None]
        i = 0

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
                prev[0].next[0] = node[0].next[0]
                del node[0]
        self.s -= 1

    def __del__(self):
        node = self.head
        next_node = None

        while node:
            next_node = node.next[0]

            del node
            node = next_node


""" Tools """
