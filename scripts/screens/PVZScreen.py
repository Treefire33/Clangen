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
        self.current_sun = 100
        self.lawn = [
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False],
            [False, False, False, False, False, False, False, False, False]
        ]
        self.lawn_tiles = []
        self.holding_plant = False
        self.current_plant = None
        self.waveManager = WaveManager(self)

    plant_types = [
        "sunflower",
        "peashooter",
        "wall-nut",
        "cherry bomb"
    ]

    def screen_switches(self):
        self.play_game = True
        self.seed_packets_bar = pygame_gui.elements.UIImage(
            scale(pygame.Rect((260, 0), (1082, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(1082, 260)),
            manager=MANAGER,
            starting_height=200,
        )
        self.sun_count = pygame_gui.elements.UITextBox(
            "0",
            scale(pygame.Rect((0, 0), (260, 260))),
            object_id=get_text_box_theme("#text_box_80_horizcenter"),
            manager=MANAGER,
            starting_height=200,
        )
        self.shovel_tray = pygame_gui.elements.UIImage(
            scale(pygame.Rect((1340, 0), (260, 260))),
            pygame.transform.scale(image_cache.load_image('resources/images/choosing_frame.png'),(260, 260)),
            manager=MANAGER,
            starting_height=200,
        )
        errorimg = image_cache.load_image(
            "resources/images/errormsg.png"
        ).convert_alpha()
        self.game_over_box = pygame_gui.elements.UIImage(
            scale(pygame.Rect((259, 300), (1180, 802))),
            pygame.transform.scale(errorimg, (1180, 802)),
            starting_height=400,
            manager=MANAGER,
        )
        self.game_over_label = pygame_gui.elements.UITextBox(
            "",
            scale(pygame.Rect((275, 370), (770, 720))),
            object_id="#text_box_22_horizleft",
            starting_height=400,
            manager=MANAGER,
        )
        self.closebtn = UIImageButton(
            scale(pygame.Rect((1386, 430), (44, 44))),
            "",
            starting_height=400,  # Hover affect works, and now allows it to be clicked more easily.
            object_id="#exit_window_button",
            manager=MANAGER,
        )
        del errorimg
        self.game_over_box.hide()
        self.game_over_label.hide()
        self.closebtn.hide()

        for i in range(5):
            temp_arr = []
            for j in range(9):
                temp_arr.append(
                    pygame_gui.elements.UIPanel(
                        scale(pygame.Rect(PVZScreen.GridToPosition(i, j, False), self.tile_size)),
                        manager=MANAGER,
                        object_id="#tileB" if j%2==0 else "#tileA"
                    )
                )
            self.lawn_tiles.append(temp_arr)
        
        self.seed_packets = []
        temp_index = 0
        translation_dict = {
            "sunflower": "leader",
            "peashooter": "warrior",
            "wall-nut": "elder",
            "cherry bomb": "newborn"
        }
        translation_dict_button = {
            "sunflower": "#mediation_button",
            "peashooter": "#paw_patrol_button",
            "wall-nut": "#events_cat_button",
            "cherry bomb": "#claws_patrol_button"
        }
        for plant in self.plant_types:
            self.seed_packets.append(
                UIImageButton(
                    scale(pygame.Rect((260+(260*temp_index), 0), (260, 260))),
                    text=translation_dict[plant],
                    object_id=translation_dict_button[plant],
                    manager=MANAGER,
                    starting_height=210,
                )
            )
            temp_index += 1
        
        del temp_index
        del translation_dict
        del translation_dict_button
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
                value,
                self
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
            self.current_plant = newPlant
        else:
            newPlant.sprite.kill()
            newPlant.shadow.kill()
            del newPlant

    def spawn_zombie(self, grid_position):
        newZombie = Zombie(grid_position, grid_position[0], self)
        self.entities.append(newZombie)

    def create_projectile(self, ownerPlant, projType):
        ownerPlant: Plant = ownerPlant
        newProj = Projectile(ownerPlant.sprite.relative_rect.topleft, ownerPlant.damage, projType, ownerPlant.grid_pos[0], self)
        self.entities.append(newProj)

    debug_enabled = False
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.closebtn:
                self.change_screen("camp screen")
        if self.play_game:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
                    self.debug_enabled = True
            if event.type == pygame.KEYDOWN and self.debug_enabled:
                if event.key == pygame.K_s:
                    dest_lane = randrange(0, 4)
                    dest_col = randrange(0, 8)
                    self.make_sun(PVZScreen.GridToPosition(0, dest_col, False), dest_lane, 25)
                if event.key == pygame.K_d:
                    for i in range(5):
                        for j in range(9):
                            self.make_sun(PVZScreen.GridToPosition(0, j, False), i, 25)
                if event.key == pygame.K_a:
                    self.current_sun = 9990
                if event.key == pygame.K_1:
                    if not self.holding_plant:
                        self.init_plant("continue")
                if event.key == pygame.K_2:
                    for i in range(5):
                        self.spawn_zombie((i, 9))
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
                    if event.ui_element == seed_packet and not self.holding_plant:
                        self.init_plant(seed_packet.text)
                    elif event.ui_element == seed_packet and self.holding_plant:
                        self.holding_plant = False
                        self.current_plant.attached_to_cursor = False
                        self.current_plant.shadow.kill()
                        del self.current_plant.shadow
                        self.current_plant.die()
    
    def exit_screen(self):
        self.seed_packets_bar.kill()
        del self.seed_packets_bar
        self.sun_count.kill()
        del self.sun_count
        self.shovel_tray.kill()
        del self.shovel_tray
        for entity in self.entities:
            entity.sprite.kill()
        self.entities.clear()
        for tile in self.lawn_tiles:
            for t in tile:
                t.kill()
        self.lawn_tiles.clear()
        for tile in self.seed_packets:
            tile.kill()
        self.seed_packets.clear()
        self.game_over_box.kill()
        del self.game_over_box
        self.game_over_label.kill()
        del self.game_over_label
        self.closebtn.kill()
        del self.closebtn

        #reset game
        self.current_sun = 100
        self.holding_plant = False
        self.current_plant = None
        self.waveManager.current_wave = 0

    clock = pygame.Clock()
    wave_cooldowns = [
        10, #intro wait period
        15, #wave 1
        28, #wave 2
        32, #wave 3
        40, #wave 4
        45  #wave 5

    ] #in seconds, multiply by 1000.
    current_wave_start = pygame.time.get_ticks()
    natural_sun_cooldown = randrange(3200, 13500)
    current_natural_sun = pygame.time.get_ticks()
    play_game = False
    def on_use(self):
        if self.play_game:
            dt = self.clock.tick(60.0)/1000.0
            if pygame.time.get_ticks() - self.current_wave_start >= (self.wave_cooldowns[self.waveManager.current_wave]*1000):
                print("start wave")
                self.current_wave_start = pygame.time.get_ticks()
                self.waveManager.spawn_wave()
            if pygame.time.get_ticks() - self.current_natural_sun >= self.natural_sun_cooldown:
                self.current_natural_sun = pygame.time.get_ticks()
                lane = randrange(0, 5)
                self.make_sun(PVZScreen.GridToPosition(lane, randrange(0, 9), False), lane, 25)
            self.waveManager.update(dt)
            for entity in self.entities:
                entity.update(dt)
            self.sun_count.set_text(str(self.current_sun))

    def game_over(self, won):
        self.play_game = False
        self.game_over_box.show()
        self.game_over_label.show()
        self.closebtn.show()
        if won:
            self.game_over_label.set_text("You won!")
        else:
            self.game_over_label.set_text("You lost...")

class WaveManager():
    waves = [
        0, #intro wait
        1,
        4,
        13,
        20,
        30
    ]
    current_wave = 0
    currentGame: PVZScreen
    spawn_cooldown = randrange(2100, 5600)
    spawn_time = pygame.time.get_ticks()
    amount_remaining = 0

    def __init__(self, currentGame):
        self.currentGame = currentGame

    def spawn_wave(self):
        if self.current_wave == len(self.waves)-1:
            self.currentGame.game_over(True)
        self.amount_remaining = self.waves[self.current_wave]
        self.spawn_time = pygame.time.get_ticks()
        self.current_wave += 1

    def update(self, deltaTime):
        if pygame.time.get_ticks() - self.spawn_time >= self.spawn_cooldown and self.amount_remaining > 0 and self.current_wave > 0:
            self.currentGame.spawn_zombie((randrange(0, 5), 9))
            self.spawn_cooldown = randrange(2100, 5600)
            self.spawn_time += randrange(2100, 5600)
            self.amount_remaining -= 1
            

class Entity():
    sprite = None
    def update(self, deltaTime):
        pass

class Sun(Entity):
    value = 50
    size = scaleTuple((125, 125))
    dest_lane = 0
    grounded = False
    grounded_time = 0
    time_til_destroy = 6000
    currentScreen:PVZScreen = None

    def __init__(self, dest_lane: int, position: tuple[int, int], value, currentGame):
        super().__init__()
        self.sprite = UIImageButton(
            pygame.Rect(scaleTuple(position), self.size),
            "",
            starting_height=300,
            object_id="#mouse_patrol_button",
            manager=MANAGER,
        )
        self.dest_lane = dest_lane
        self.value = value
        self.currentScreen = currentGame

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
            self.currentScreen.entities.remove(self)
            del self
            return
        if not self.sprite.alive():
            del self
            return

class Plant(Entity):
    damage = 10
    size = scaleTuple((340, 340))
    attack_cooldown = 1300
    health = 100
    cost = 50

    attached_to_cursor = False
    planted = False

    plantType = "sunflower"
    translation_dict_old = {
        "sunflower": "continue",
        "peashooter": "new_clan"
    }
    translation_dict = {
        "leader": "sunflower",
        "warrior": "peashooter",
        "elder": "wall-nut",
        "newborn": "cherry bomb"
    }
    cost_dict = {
        "leader": 50,
        "warrior": 100,
        "elder": 50,
        "newborn": 150
    }
    currentGame: PVZScreen = None

    grid_pos = (0, 0)
    plant_spr = None

    def getCatSpriteFromClanOfStatus(self, status):
        cats = get_alive_status_cats(Cat, [status])
        if len(cats) <= 0:
            cats = get_alive_status_cats(Cat, "warrior")
        selected_cat: Cat = choice(cats)
        return selected_cat.sprite
            

    def __init__(self, grid_pos: tuple[int, int], seed_packet, currentGame):
        super().__init__()
        currentSprite = self.getCatSpriteFromClanOfStatus(seed_packet)
        self.sprite = UIImageButton(
            scale(pygame.Rect((PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], False)), self.size)),
            "",
            object_id="#events_cat_button",
            starting_height=3,
            manager=MANAGER,
        )
        self.shadow = UIImageButton(
            scale(pygame.Rect((PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], False)), self.size)),
            "",
            starting_height=2,
            manager=MANAGER,
        )
        scaled_sprite = pygame.transform.scale(
            currentSprite, self.sprite.relative_rect.size
        )
        # self.sprite.set_image(scaled_sprite)
        # self.sprite.normal_image = scaled_sprite
        # self.sprite.hovered_image = scaled_sprite
        # self.sprite.disabled_image = scaled_sprite
        # self.shadow.set_image(scaled_sprite)
        # self.shadow.normal_image = scaled_sprite
        # self.shadow.hovered_image = scaled_sprite
        # self.shadow.disabled_image = scaled_sprite
        self.plantType = self.translation_dict[seed_packet]
        self.cost = self.cost_dict[seed_packet]
        self.attached_to_cursor = True
        if self.plantType == "cherry bomb":
            self.attack_cooldown = 500
        self.plant_spr = scaled_sprite
        self.currentGame = currentGame

    def update(self, deltaTime):
        if self.attached_to_cursor:
            mouse = pygame.mouse.get_pos()
            self.sprite.set_position((mouse[0]-(self.size[0]/4), mouse[1]-(self.size[1]/4)))

            grid_pos = PVZScreen.PositionToGrid(mouse[0]-(PVZScreen.tile_size[0]/4), mouse[1]-(PVZScreen.tile_size[1]/4), True)
            self.shadow.set_position(PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], True))
        if self.planted:
            if self.health <= 0:
                self.die()
            if pygame.time.get_ticks() - self.attack_start >= self.attack_cooldown:
                match self.plantType:
                    case "sunflower":
                        self.currentGame.make_sun(PVZScreen.GridToPosition(self.grid_pos[0], self.grid_pos[1], False), self.grid_pos[0], 25)
                        self.attack_start = pygame.time.get_ticks()+randrange(7800, 11000)
                    case "peashooter":
                        self.currentGame.create_projectile(self, "pea")
                        self.attack_start = pygame.time.get_ticks()
                    case "cherry bomb":
                        for entity in self.currentGame.entities:
                            if isinstance(entity, Zombie):
                                newDist = math.sqrt(
                                    math.pow(
                                        entity.sprite.relative_rect.topleft[0]-self.sprite.relative_rect.center[0],
                                        2
                                    )+math.pow(
                                        entity.sprite.relative_rect.topleft[1]-self.sprite.relative_rect.center[1],
                                        2
                                    )
                                )
                                if newDist <= 175:
                                    entity.health -= 1500
                        self.die()
    
    def die(self):
        self.sprite.kill()
        self.planted = False
        self.health = 0
        self.currentGame.lawn[self.grid_pos[0]][self.grid_pos[1]] = False
        self.currentGame.entities.remove(self)
        del self

    def place_plant(self, lawn):
        mouse = pygame.mouse.get_pos()
        grid_pos = PVZScreen.PositionToGrid(mouse[0]-(PVZScreen.tile_size[0]/4), mouse[1]-(PVZScreen.tile_size[1]/4), True)
        if not lawn[grid_pos[0]][grid_pos[1]]:
            lawn[grid_pos[0]][grid_pos[1]] = True
            self.attached_to_cursor = False
            self.planted = True
            self.shadow.kill()
            del self.shadow
            self.sprite.kill()
            self.sprite = pygame_gui.elements.UIImage(
                scale(pygame.Rect((0, 0), self.size)),
                pygame.transform.scale(self.plant_spr,self.size),
                starting_height=3,
            )
            if self.plantType == "wall-nut":
                self.health = 2000
            #self.sprite.disable()
            self.sprite.set_position(PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], True))
            self.attack_start = pygame.time.get_ticks()
            self.grid_pos = grid_pos
            return True
        return False

    def GetClosestZombie(self, tile):
        tile_pos = PVZScreen.GridToPosition(tile[0], tile[1], True)
        closestZombie: Zombie = None
        currentMinDist = 9999
        for entity in self.currentGame.entities:
            if isinstance(entity, Zombie):
                newDist = math.sqrt(
                    math.pow(
                        entity.sprite.relative_rect.topleft[0]-tile_pos[0],
                        2
                    )+math.pow(
                        entity.sprite.relative_rect.topleft[1]-tile_pos[1],
                        2
                    )
                )
                if newDist <= currentMinDist:
                    if entity.lane == tile[0]:
                        closestZombie = entity
                    currentMinDist = newDist
        return closestZombie, currentMinDist
    
class Zombie(Entity):
    health = 100
    damage = 10
    attack_cooldown = 750
    size = scaleTuple((250, 250))
    lane = 0
    currentGame: PVZScreen

    eating = False
    eating_plant = None

    def __init__(self, grid_pos, current_lane, current_game):
        self.sprite = pygame_gui.elements.UIImage(
            pygame.Rect(PVZScreen.GridToPosition(grid_pos[0], grid_pos[1], True), self.size),
            pygame.transform.scale(image_cache.load_image('resources/images/patrol_art/fst_hunt_vole.png'),self.size),
            manager=MANAGER,
            starting_height=3,
        )
        self.lane = current_lane
        self.currentGame = current_game

    def update(self, deltaTime):
        current_zeroed_pos = max(self.sprite.relative_rect.topleft[0], 0)
        if current_zeroed_pos >= 0 and not self.eating:
            self.sprite.set_position((self.sprite.relative_rect.topleft[0]-(7.5*deltaTime), self.sprite.relative_rect.topleft[1])) 
            plant, dist = self.GetClosestPlant()
            if dist <= 20 and plant and plant.planted:
                self.eating = True
                self.eating_plant = plant
                self.attack_start = pygame.time.get_ticks()
        if self.eating:
            if pygame.time.get_ticks() - self.attack_start >= self.attack_cooldown:
                self.attack_start = pygame.time.get_ticks()
                self.eating_plant.health -= self.damage
        if self.eating_plant and self.eating_plant.health <= 0:
            self.eating = False
            self.eating_plant = None
        if self.health <= 0:
            self.sprite.set_position((9999, 9999))
            self.sprite.kill()
            self.eating = False
            self.eating_plant = None
            self.attack_start = -1
            self.currentGame.entities.remove(self)
            del self
        if current_zeroed_pos <= 0:
            self.currentGame.game_over(False)
            self.sprite.set_position((9999, 9999))
            self.sprite.kill()
            self.eating = False
            self.eating_plant = None
            self.attack_start = -1
            self.currentGame.entities.remove(self)
            del self
    
    def GetClosestPlant(self): #copied from projectile class lol
        closestZombie: Plant = None
        currentMinDist = 9999
        for entity in self.currentGame.entities:
            if isinstance(entity, Plant):
                newDist = math.sqrt(
                    math.pow(
                        entity.sprite.relative_rect.topleft[0]-self.sprite.relative_rect.topleft[0],
                        2
                    )+math.pow(
                        entity.sprite.relative_rect.topleft[1]-self.sprite.relative_rect.topleft[1],
                        2
                    )
                )
                if newDist <= currentMinDist:
                    if entity.grid_pos[0] == self.lane:
                        closestZombie = entity
                    currentMinDist = newDist
        return closestZombie, currentMinDist

class Projectile(Entity):
    damage = 10
    projectile_types = {
        "pea": "cursor",
        "explosive_pea": "dot_big"
    }
    current_type = "pea"
    size = scaleTuple((80, 80))
    collided = False
    lane = 0

    def __init__(self, position: tuple[int, int], damage, projectileType, current_lane, currentGame: PVZScreen):
        super().__init__()
        self.sprite = pygame_gui.elements.UIImage(
            pygame.Rect(position, self.size),
            pygame.transform.scale(image_cache.load_image(f'resources/images/{self.projectile_types[projectileType]}.png'), self.size),
            manager=MANAGER,
            starting_height=4,
        )
        self.damage = damage
        self.currentGame = currentGame
        self.lane = current_lane

    def update(self, deltaTime):
        current_zeroed_pos = max(self.sprite.relative_rect.topleft[0], 0)
        if current_zeroed_pos <= 900:
            self.sprite.set_position((self.sprite.relative_rect.topleft[0] + (250*deltaTime), self.sprite.relative_rect.topleft[1]))
            zombie, dist = self.GetClosestZombie()
            if dist <= 20 and zombie and not self.collided:
                self.collided = True
                self.collide(zombie)
    
    def collide(self, zombie: Zombie):
        zombie.health -= self.damage
        self.sprite.kill()
        self.currentGame.entities.remove(self)
        del self

    def GetClosestZombie(self):
        closestZombie: Zombie = None
        currentMinDist = 9999
        for entity in self.currentGame.entities:
            if isinstance(entity, Zombie):
                newDist = math.sqrt(
                    math.pow(
                        entity.sprite.relative_rect.topleft[0]-self.sprite.relative_rect.topleft[0],
                        2
                    )+math.pow(
                        entity.sprite.relative_rect.topleft[1]-self.sprite.relative_rect.topleft[1],
                        2
                    )
                )
                if newDist <= currentMinDist:
                    if entity.lane == self.lane:
                        closestZombie = entity
                    currentMinDist = newDist
        return closestZombie, currentMinDist