# pylint: disable=line-too-long
# pylint: disable=unused-import
import pygame
import pygame_gui

from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.game_essentials import game
from scripts.game_structure.ui_elements import UISurfaceImageButton
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.get_arrow import get_arrow
from scripts.utility import get_text_box_theme, ui_scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from scripts.screens.Screens import Screens
from .Entity import Entity
from pygame_gui.core.interfaces import IUIElementInterface

class Minigame():
    default_minigame_container = MANAGER.get_root_container()

    entities: list[Entity] = []
    elements: dict[str, IUIElementInterface] = {}
    play_game = False

    def create_element(self, name, element):
        if element.ui_container is not None and element.ui_container is not element:
            element.set_container(Minigame.default_minigame_container)
        self.elements[name] = element

    def create_entity(self, entity):
        if entity.sprite.ui_container is not None and entity.sprite.ui_container is not entity.sprite:
            entity.sprite.ui_container.set_container(Minigame.default_minigame_container)
        self.entities.append(entity)

    def load_minigame(self):
        pass

    def exit_minigame(self):
        for name, element in self.elements.items():
            element.kill()

        for enitity in self.entities:
            enitity.sprite.kill()
        
        self.elements.clear()

    def handle_event(self, event: pygame.Event):
        pass

    def update(self, delta_time):
        for entity in self.entities:
            entity.update(delta_time)

base_minigame = Minigame()
