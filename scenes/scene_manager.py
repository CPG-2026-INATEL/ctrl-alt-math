class SceneManager:
    def __init__(self, game):
        self.game = game
        self.scenes = {}
        self.current = None
        self.stack = []

    def add(self, name, scene_class):
        self.scenes[name] = scene_class(self.game)

    def get(self, name):
        return self.scenes.get(name)

    def switch(self, name):
        prev = self.current
        if self.current:
            self.current.exit()
        self.stack.clear()
        self.current = self.scenes[name]
        self.current.enter(prev)

    def push(self, name):
        prev = self.current
        if self.current:
            self.stack.append(self.current)
        self.current = self.scenes[name]
        self.current.enter(prev)

    def pop(self):
        if self.stack:
            if self.current:
                self.current.exit()
            self.current = self.stack.pop()
            return True
        return False
