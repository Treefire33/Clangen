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
from scripts.game_structure.ui_elements import UISurfaceImageButton
from scripts.game_structure.windows import SaveError
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, ui_scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from pygame_gui.elements import UIWindow
from ..game_structure.screen_settings import MANAGER
from ..game_structure.audio import music_manager, sound_manager
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..housekeeping.datadir import get_data_dir
from ..housekeeping.version import get_version_info
from scripts.ui.get_arrow import get_arrow
from random import random, randrange, choice, sample
import math
from scripts.minigames.Minigame import Minigame
from pygame_gui.core.interfaces import IUIElementInterface

class MinigameSelectWindow(UIWindow):
    loaded_minigames : dict[str, Minigame] = {} #holds minigame screens.\
    current_minigame = ""
    minigame_open = False

    def __init__(self, rect, manager):
        super().__init__(
            rect,
            manager,
            "Minigames!",
            object_id="#debug_console"
        )

        self.hide()

        for minigame in os.listdir("resources/minigames"):
            if minigame == '.Catch':
                continue
            with open(f"resources/minigames/{minigame}/minigame.py") as file:
                try:
                    exec(file.read()+f"\n\nMinigameSelectWindow.loaded_minigames[\"{minigame}\"] = {minigame}()", globals())
                except Exception as e:
                    print(f"failed to load minigame: {minigame}. {repr(e)}")

        self.minigame_buttons = {}
        x = 0
        y = 0
        self.minigame_buttons_container = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((24, 24), (776, 676))),
            allow_scroll_x=False,
            container=self,
            manager=MANAGER,
        )
        for minigame in self.loaded_minigames:
            self.minigame_buttons[minigame] = UISurfaceImageButton(
                ui_scale(pygame.Rect((x, y), (64, 64))),
                minigame,
                container=self.minigame_buttons_container,
                image_dict=get_button_dict(ButtonStyles.ICON, (64, 64)),
                object_id="@buttonstyles_icon",
                manager=MANAGER
            )
            x += 64
            if x >= 768:
                x = 0
                y += 64

        # A container that the minigames load into.
        self.minigame_container = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect(0, 0, 800, 700)),
            manager,
            container=self
        )

        Minigame.minigame_container = self.minigame_container

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 470), (152, 30))),
            get_arrow(3) + " Main Menu",
            get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_squoval",
            container=self,
            starting_height=600
        )
        self.back_button.hide()
    
    def toggle_self(self, minigame_open):
        if minigame_open:
            self.back_button.show()
            self.minigame_buttons_container.hide()
        else:
            self.back_button.hide()
            self.minigame_buttons_container.show()

    def open_minigame(self, minigame: str):
        self.loaded_minigames[minigame].load_minigame()
        for name, element in self.loaded_minigames[minigame].elements.items():
            if element.ui_container is not None and element.ui_container is not element:
                element.set_container(self.minigame_container)
        self.minigame_open = True
        self.current_minigame = minigame
        self.toggle_self(self.minigame_open)

    def exit_minigame(self):
        if self.minigame_open:
            self.loaded_minigames[self.current_minigame].exit_minigame()
            self.current_minigame = ""
            self.minigame_open = False
            self.back_button.hide()
        self.toggle_self(self.minigame_open)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            element = event.ui_element
            for minigame, btn in self.minigame_buttons.items():
                if element == btn:
                    self.open_minigame(minigame)
            if element == self.back_button:
                self.exit_minigame()
        if self.minigame_open:
            self.loaded_minigames[self.current_minigame].handle_event(event)

    def update(self, delta_time):
        if self.minigame_open:
            self.loaded_minigames[self.current_minigame].update(delta_time)
            # force set the container of entities
            for element in self.loaded_minigames[self.current_minigame].entities:
                if element.sprite.ui_container is not None and element.sprite.ui_container is not element.sprite:
                    element.sprite.set_container(self.minigame_container)
        super().update(delta_time)

    def toggle_window(self):
        if self.visible:
            self.hide()
        else:
            self.show()
            self.toggle_self(self.minigame_open)
        

minigame_window = MinigameSelectWindow(
    ui_scale(pygame.Rect(0, 0, 600, 500)),
    MANAGER
)
