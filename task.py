from copy import deepcopy

class Task:
    """Représente une tâche (trajet) avec un point de départ et une destination."""
    def __init__(self, start, destination, id=None):
        self.id = id
        self.start = start          # (x, y)
        self.destination = destination

    def __repr__(self):
        return f"Task(id={self.id}, start={self.start}, destination={self.destination})"