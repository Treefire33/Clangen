# pylint: disable=line-too-long
# pylint: disable=unused-import
import logging
import os
import platform
import subprocess
import traceback

import pygame
import pygame_gui
import ujson

from scripts.game_structure import image_cache
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider
from scripts.game_structure.windows import SaveError
from scripts.utility import get_text_box_theme, scale, quit  # pylint: disable=redefined-builtin
from .Screens import Screens
from ..game_structure.audio import music_manager, sound_manager
from ..housekeeping.datadir import get_data_dir
from ..housekeeping.version import get_version_info
from random import random, randrange

class PVZScreen(Screens):

    #game loop stuff
    current_sun: int = 0 # Number of sun user has
    lawn = None # A 2d array that tracks if a plant (cat) is in a tile or not.
    entities = []

    def __init__(self, name=None):
        super().__init__(name)
        self.seed_packets_bar = None
        self.sun_count = None
        self.shovel_tray = None
        self.current_sun = 50
        self.lawn = [
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False]
        ]


    def screen_switches(self):
        self.seed_packets_bar = pygame_gui.elements.UIImage(
            scale(pygame.Rect((260, 0), (1082, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(1082, 260))
        )
        self.sun_count = pygame_gui.elements.UITextBox(
            "0",
            scale(pygame.Rect((0, 0), (260, 260))),
            object_id=get_text_box_theme("#text_box_80_horizcenter_dark"),
            manager=MANAGER
        )
        self.shovel_tray = pygame_gui.elements.UIImage(
            scale(pygame.Rect((1340, 0), (260, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(260, 260))
        )
        
        # prefabs
        # self.sun_prefab = pygame_gui.elements.UIImage(
        #     scale(pygame.Rect((0, 0), (130, 130))),
        #     pygame.transform.scale(image_cache.load_image('resources/images/buttons/button_mouse.png'),(130, 130))
        # )
        return
    
    def make_sun(self, position: tuple[int, int], dest_lane, value, size):
        self.entities.append(
            Sun(
                dest_lane,
                (position[0]+size[0], (position[1]-200)),
                value
            )
        )
        return
    
    @staticmethod
    def GridToPosition(row, col) -> tuple[int, int]:
        #left-top-most = 0, 320
        #right-bottom-most = 1440, 800
        #size-of-tile = 160
        x = (col*160)
        y = 320+(row*160)
        return (x, y)
    
    @staticmethod
    def UpdateInstanceSun(value):
        return

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("the mice are coming!")
            if event.key == pygame.K_s:
                dest_lane = randrange(0, 4)
                dest_col = randrange(0, 8)
                self.make_sun(PVZScreen.GridToPosition(0, dest_col), dest_lane, 25, (75, 75))
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for entity in self.entities:
                if type(entity.sprite) == UIImageButton and event.ui_element == entity.sprite:
                    if type(entity) == Sun:
                        self.current_sun += entity.value
                        entity.sprite.kill()
                        self.entities.remove(entity)
        return
    
    def change_screen(self, new_screen):
        return
    
    def exit_screen(self):
        self.seed_packets_bar.kill()
        del self.seed_packets_bar
        self.sun_count.kill()
        del self.sun_count
        pass

    clock = pygame.Clock()
    def on_use(self):
        dt = self.clock.tick(60.0)/1000.0
        for entity in self.entities:
            entity.update(dt)
        self.sun_count.set_text(str(self.current_sun))

class Entity():
    sprite = None
    def update(self, deltaTime):
        pass

class Sun(Entity):
    value = 25
    size = (75, 75)
    dest_lane = 0

    def __init__(self, dest_lane: int, position: tuple[int, int], value):
        super().__init__()
        self.sprite = UIImageButton(
            scale(pygame.Rect((position), self.size)),
            "",
            object_id=f"#mouse_patrol_button",
            starting_height=1,
            manager=MANAGER
        )
        self.dest_lane = dest_lane
        self.value = value

    def update(self, deltaTime):
        super().update(deltaTime)
        if self.sprite.relative_rect.topleft[1] < PVZScreen.GridToPosition(self.dest_lane, 0)[1]:
            self.sprite.set_position((self.sprite.relative_rect.x, self.sprite.relative_rect.y + (45*deltaTime)))
