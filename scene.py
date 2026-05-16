class Scene:
    overlay = False

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

    def enter(self, prev_scene=None):
        pass

    def exit(self):
        pass
