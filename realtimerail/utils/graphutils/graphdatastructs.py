
class DirectedPath():

    def __init__(self):
        self.vertices = []

    def __init__(self, label_list):
        self.vertices = [DirectedPathVertex(label) for label in label_list]
        for i in range(len(self.vertices)-1):
            self.vertices[i].next = self.vertices[i+1]
            self.vertices[i+1].prev = self.vertices[i]

class DirectedPathVertex():

    def __init__(self, label):
        self.label = label
        self.prev = None
        self.next = None
