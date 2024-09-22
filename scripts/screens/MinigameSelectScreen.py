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
    def screen_switches(self):
        self.show_mute_buttons()
        self.set_disabled_menu_buttons(["minigames"])
        self.update_heading_text("Minigames!")
        self.show_menu_buttons()

        self.pvz_minigame = UIImageButton(
            scale(pygame.Rect((64, 250), (128, 128))),
            "pvz",
            object_id="#pvz_minigame"
        )
    
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            element = event.ui_element
            if element == self.pvz_minigame:
                self.change_screen("pvz screen")
            else:
                self.menu_button_pressed(event)
    
    def exit_screen(self):
        self.pvz_minigame.kill()
        del self.pvz_minigame
