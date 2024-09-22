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
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from .Screens import Screens
from ..game_structure.audio import music_manager, sound_manager
from ..housekeeping.datadir import get_data_dir
from ..housekeeping.version import get_version_info
from random import random, randrange, choice, sample
import math

class MinigameSelectScreen(Screens):
    minigames = [
        "pvz"
    ]
    loaded_minigames = [] #holds minigame screens.

    def __init__(self, name=None):
        super().__init__(name)
        for minigame in os.listdir("resources/minigames"):
            with open(f"resources/minigames/{minigame}/minigame.py") as file:
                self.minigames.append(minigame)
                exec(file.read()+f"\n\nMinigameSelectScreen.loaded_minigames.append({minigame}(\"{minigame} screen\"))", globals())

    def screen_switches(self):
        self.show_mute_buttons()
        self.set_disabled_menu_buttons(["minigames"])
        self.update_heading_text("Minigames!")
        self.show_menu_buttons()

        self.minigame_buttons = {}
        x = 64
        y = 250
        # move scaled 128 until x >= 1400, then increment y by 128
        for minigame in self.minigames:
            self.minigame_buttons[minigame] = pygame_gui.elements.UIButton(
                scale(pygame.Rect((x, y), (128, 128))),
                minigame,
                object_id=f"#{minigame.lower().replace('screen', '').replace(' ', '')}_minigame",
                manager=MANAGER
            )
            x += 128
            if x >= 1400:
                x = 64
                y += 128
    
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            element = event.ui_element
            if element in self.minigame_buttons.values():
                for minigame, btn in self.minigame_buttons.items():
                    if element == btn:
                        self.change_screen(minigame+" screen")
            else:
                self.menu_button_pressed(event)
    
    def exit_screen(self):
        for minigame, btn in self.minigame_buttons.items():
            btn.kill()
        del self.minigame_buttons
