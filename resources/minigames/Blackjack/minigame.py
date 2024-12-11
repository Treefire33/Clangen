# pylint: disable=line-too-long
# pylint: disable=unused-import
import pygame
import pygame_gui
import pygame_gui.elements.ui_text_box

from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER, screen_x, screen_y
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider
from pygame_gui.elements import UITextBox
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, ui_scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from scripts.minigames.Minigame import Minigame
from scripts.minigames.Entity import Entity
from random import random, randrange, choice, sample

class Blackjack(Minigame):
    player_score: int = 0
    opponent_score: int = 0

    def load_minigame(self):
        rect = pygame.Rect(0, 200, 600, 50)
        self.create_element("player_cur_value", UITextBox(
            "Your Card Value: 0",
            ui_scale(rect),
            MANAGER,
            anchors={
                "centerx": "centerx",
            }
        ))

        rect = pygame.Rect(0, 300, 600, 50)
        self.create_element("opponent_cur_value", UITextBox(
            "Opponent Card Value: 0",
            ui_scale(rect),
            MANAGER,
            anchors={
                "centerx": "centerx",
            }
        ))
        return super().load_minigame()