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

def scaleValue(isWidth, value):
    if isWidth:
        return value / 1600 * screen_x
    else:
        return value / 1400 * screen_y
def scaleTuple(tuple):
    return (
       (tuple[0]/1600*screen_x),
       (tuple[1]/1400*screen_y),
    )

class PVZScreen(Screens):

    #game loop stuff
    current_sun: int = 0 # Number of sun user has
    lawn = None # A 2d array that tracks if a plant (cat) is in a tile or not.
    entities = []
    tile_size = scaleTuple((340, 360))

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
        self.lawn_tiles = []
        self.holding_plant = False

    plant_types = [
        "sunflower",
        "peashooter"
        #wall-nut,
        #cherry bomb
    ]

    def screen_switches(self):
        self.seed_packets_bar = pygame_gui.elements.UIImage(
            scale(pygame.Rect((260, 0), (1082, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(1082, 260)),
            starting_height=200,
        )
        self.sun_count = pygame_gui.elements.UITextBox(
            "0",
            scale(pygame.Rect((0, 0), (260, 260))),
            object_id=get_text_box_theme("#text_box_80_horizcenter_dark"),
            manager=MANAGER,
            starting_height=200,
        )
        self.shovel_tray = pygame_gui.elements.UIImage(
            scale(pygame.Rect((1340, 0), (260, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(260, 260)),
            starting_height=200,
        )

        for i in range(5):
            temp_arr = []
            for j in range(9):
                temp_arr.append(
                    pygame_gui.elements.UIPanel(
                        scale(pygame.Rect(PVZScreen.GridToPosition(i, j, False), self.tile_size)),
                        object_id="panel_darker" if j%2==0 else "panel"
                    )
                )
            self.lawn_tiles.append(temp_arr)
        
        self.seed_packets = []
        temp_index = 0
        translation_dict = {
            "sunflower": "continue",
            "peashooter": "new_clan"
        }
        for plant in self.plant_types:
            self.seed_packets.append(
                UIImageButton(
                    scale(pygame.Rect((260+(135.25*temp_index), 0), (135.25, 260))),
                    text=translation_dict[plant],
                    object_id="#random_dice_button",
                    starting_height=210,
                )
            )
            temp_index += 1
        
        del temp_index
        del translation_dict
        # prefabs
        # self.sun_prefab = pygame_gui.elements.UIImage(
        #     scale(pygame.Rect((0, 0), (130, 130))),
        #     pygame.transform.scale(image_cache.load_image('resources/images/buttons/button_mouse.png'),(130, 130))
        # )
        return
    
    def make_sun(self, position: tuple[int, int], dest_lane, value):
        self.entities.append(
            Sun(
                dest_lane,
                (position[0], 0),
                value
            )
        )
        return
    
    @staticmethod
    def GridToPosition(row, col, doScale) -> tuple[int, int]:
        #left-most tile: 0, 300
        x = col*PVZScreen.tile_size[0]
        y = 300+row*PVZScreen.tile_size[1]
        return (x, y) if not doScale else scaleTuple((x, y))
    
    @staticmethod
    def PositionToGrid(x, y, doScale) -> tuple[int, int]:
        #left-most tile: 0, 300
        x *= 2
        y *= 2
        row = min(max(round((y-300)/PVZScreen.tile_size[1]), 0), 4) #y
        col = min(max(round(x/PVZScreen.tile_size[0]), 0), 8) #x
        return (row, col)
    
    @staticmethod
    def UpdateInstanceSun(value):
        return
    
    def init_plant(self, seed_packet):
        newPlant = Plant((0, 0), seed_packet, self)
        if self.current_sun >= newPlant.cost:
            self.entities.append(newPlant)
            self.holding_plant = True
        else:
            newPlant.sprite.kill()
            newPlant.shadow.kill()
            del newPlant

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("the mice are coming!")
            if event.key == pygame.K_s:
                dest_lane = randrange(0, 4)
                dest_col = randrange(0, 8)
                self.make_sun(PVZScreen.GridToPosition(0, dest_col, False), dest_lane, 25)
            if event.key == pygame.K_d:
                for i in range(5):
                    for j in range(9):
                        self.make_sun(PVZScreen.GridToPosition(0, j, False), i, 25)
            if event.key == pygame.K_1:
                if not self.holding_plant:
                    self.init_plant("continue")
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for entity in self.entities:
                if isinstance(entity.sprite, UIImageButton) and event.ui_element == entity.sprite:
                    if isinstance(entity, Sun):
                        self.current_sun += entity.value
                        entity.sprite.kill()
                        self.entities.remove(entity)
                    if isinstance(entity, Plant) and not entity.planted:
                        if entity.place_plant(self.lawn):
                            self.current_sun -= entity.cost
                            self.holding_plant = False
                        else:
                            print("something is on this tile already!")
            for seed_packet in self.seed_packets:
                if event.ui_element == seed_packet:
                    self.init_plant(seed_packet.text)
                        
                        
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
    size = scaleTuple((125, 125))
    dest_lane = 0
    grounded = False
    grounded_time = 0
    time_til_destroy = 6000

    def __init__(self, dest_lane: int, position: tuple[int, int], value):
        super().__init__()
        self.sprite = UIImageButton(
            pygame.Rect(scaleTuple(position), self.size),
            "",
            starting_height=100,
            object_id="#mouse_patrol_button",
            manager=MANAGER,
        )
        self.dest_lane = dest_lane
        self.value = value

    def update(self, deltaTime):
        super().update(deltaTime)
        current_pos_zeroed = self.sprite.relative_rect.topleft[1] if self.sprite.relative_rect.topleft[1] >= 0 else 0
        if current_pos_zeroed < PVZScreen.GridToPosition(self.dest_lane, 0, True)[1]:
            self.sprite.set_position((self.sprite.relative_rect.x, self.sprite.relative_rect.y + (50*deltaTime)))
            self.grounded = True
            self.grounded_time = pygame.time.get_ticks()
            return
        if pygame.time.get_ticks() - self.grounded_time >= self.time_til_destroy:
            self.sprite.kill()
            del self
            return
        if not self.sprite.alive():
            del self
            return

class Plant(Entity):
    damage = 10
    size = scaleTuple((250, 250))
    attack_cooldown = 2000
    health = 200
    cost = 50

    attached_to_cursor = False
    planted = False

    plantType = "sunflower"
    translation_dict_old = {
        "sunflower": "continue",
        "peashooter": "new_clan"
    }
    translation_dict = {
        "continue": "sunflower",
        "new_clan": "peashooter"
    }
    currentGame: PVZScreen = None

    grid_pos = (0, 0)

    def __init__(self, grid_pos: tuple[int, int], seed_packet, currentGame):
        super().__init__()
        self.sprite = UIImageButton(
            scale(pygame.Rect((PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], False)), self.size)),
            "",
            starting_height=2,
            object_id=f"#{seed_packet}_button",
            manager=MANAGER,
        )
        self.shadow = UIImageButton(
            scale(pygame.Rect((PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], False)), self.size)),
            "",
            starting_height=2,
            object_id=f"#{seed_packet}_button",
            manager=MANAGER,
        )
        self.plantType = self.translation_dict[seed_packet]
        self.attached_to_cursor = True
        self.currentGame = currentGame

    def update(self, deltaTime):
        if self.attached_to_cursor:
            mouse = pygame.mouse.get_pos()
            self.sprite.set_position((mouse[0]-(self.size[0]/4), mouse[1]-(self.size[1]/4)))

            grid_pos = PVZScreen.PositionToGrid(mouse[0]-(PVZScreen.tile_size[0]/4), mouse[1]-(PVZScreen.tile_size[1]/4), True)
            self.shadow.set_position(PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], True))
        if self.planted:
            match self.plantType:
                case "sunflower":
                    if pygame.time.get_ticks() - self.attack_start >= self.attack_cooldown:
                        self.currentGame.make_sun(PVZScreen.GridToPosition(self.grid_pos[0], self.grid_pos[1], False), self.grid_pos[0], 25)
                        self.attack_start = pygame.time.get_ticks()+randrange(7500, 11000)
                case "peashooter":
                    if pygame.time.get_ticks() - self.attack_start >= self.attack_cooldown:
                        self.attack_start = pygame.time.get_ticks()
                        

    def place_plant(self, lawn):
        mouse = pygame.mouse.get_pos()
        grid_pos = PVZScreen.PositionToGrid(mouse[0]-(PVZScreen.tile_size[0]/4), mouse[1]-(PVZScreen.tile_size[1]/4), True)
        if not lawn[grid_pos[0]][grid_pos[1]]:
            lawn[grid_pos[0]][grid_pos[1]] = True
            self.attached_to_cursor = False
            self.planted = True
            self.shadow.kill()
            del self.shadow
            self.sprite.disable()
            self.sprite.set_position(PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], True))
            self.attack_start = pygame.time.get_ticks()
            self.grid_pos = grid_pos
            return True
        return False
