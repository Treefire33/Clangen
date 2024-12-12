class Entity:
    sprite = None

    def update(self, deltaTime):
        pass

    def kill(self):
        self.sprite.kill()
        self.sprite = None