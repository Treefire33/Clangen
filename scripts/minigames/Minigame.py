# pylint: disable=line-too-long
# pylint: disable=unused-import
import pygame
import pygame_gui.elements.ui_text_box

from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider
from scripts.utility import get_text_box_theme, scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from scripts.screens.Screens import Screens
from .Entity import Entity

class Minigame(Screens):
    entities: list[Entity] = []
    play_game = False
    deltaTime = 0

    def screen_switches(self):
        self.back_button = UIImageButton(
            scale(pygame.Rect((0, 1340), (210, 60))),
            "",
            object_id="#back_button",
            manager=MANAGER,
            starting_height=600
        )

    clock = pygame.Clock()
    def on_use(self):
        self.deltaTime = self.clock.tick(60.0)/1000.0
        for entity in self.entities:
            entity.update(self.deltaTime)
        super().on_use()