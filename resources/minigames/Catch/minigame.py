# pylint: disable=line-too-long
# pylint: disable=unused-import
import logging
import os
import platform
import subprocess
import traceback

import pygame
import pygame_gui
import pygame_gui.elements.ui_text_box
import ujson

from scripts.game_structure import image_cache
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider
from scripts.game_structure.windows import SaveError
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from scripts.screens.Minigame import Minigame, Entity
from scripts.game_structure.audio import music_manager, sound_manager
from scripts.housekeeping.datadir import get_data_dir
from scripts.housekeeping.version import get_version_info
from random import random, randrange, choice, sample
import math

def scaleTuple(tuple):
    return (
       (tuple[0]/1600*screen_x),
       (tuple[1]/1400*screen_y),
    )

class Catch(Minigame):
    player = None
    score = 0
    lives = 5

    def __init__(self, name=None):
        super().__init__(name)

    def screen_switches(self):
        self.play_game = True
        self.player = Player(self)
        self.current_drop_cooldown = pygame.time.get_ticks()
        self.entities.append(self.player)
        self.hide_menu_buttons()

        self.score_label = pygame_gui.elements.UITextBox(
            "Score: "+str(self.score),
            scale(pygame.Rect((0, 0), (1600, 100))),
            object_id=get_text_box_theme("#text_box_40")
        )
        self.lives_label = pygame_gui.elements.UITextBox(
            "Lives: "+str(self.lives),
            scale(pygame.Rect((0, 100), (1600, 100))),
            object_id=get_text_box_theme("#text_box_40")
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
            object_id="#text_box_40",
            starting_height=400,
            manager=MANAGER,
        )
        del errorimg
        self.game_over_box.hide()
        self.game_over_label.hide()
        super().screen_switches()
    
    debug_game = False
    def handle_event(self, event):
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.back_button:
                    self.change_screen("minigame select screen")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 and self.play_game and self.debug_game:
                    self.spawn_prey()

    def spawn_prey(self):
        new_prey = Prey(self)
        self.entities.append(new_prey)

    drop_cooldown = 2100
    def on_use(self):
        if self.play_game:
            if pygame.time.get_ticks() - self.current_drop_cooldown >= self.drop_cooldown:
                self.current_drop_cooldown = pygame.time.get_ticks()
                self.spawn_prey()
                self.drop_cooldown = max(self.drop_cooldown-self.deltaTime*(460), 620)
            
            self.score_label.set_text(f"Score: {self.score}")
            self.lives_label.set_text(f"Lives: {self.lives}")
            if self.lives <= 0:
                self.play_game = False
                self.game_over_box.show()
                self.game_over_label.show()
                self.game_over_label.set_text("You lost...")
            super().on_use()
    
    def exit_screen(self):
        self.play_game = False
        self.back_button.kill()
        del self.back_button
        self.score_label.kill()
        del self.score_label
        self.lives_label.kill()
        del self.lives_label
        self.score = 0
        self.lives = 5
        for entity in self.entities:
            entity.sprite.kill()
        self.entities.clear()
        self.game_over_box.kill()
        self.game_over_label.kill()
        del self.game_over_box
        del self.game_over_label
        # self.player.sprite.kill()
        # del self.player

class Prey(Entity):
    speed = 125
    size = (200, 200)

    prey_types = {
        "mtn_hunt_shrew": 5,
        "fst_hunt_vole": 10,
        "pln_hunt_prairiedog1": 15
    }
    selected_sprite = "mtn_hunt_shrew"
    def __init__(self, cur_game):
        self.selected_sprite = choice(list(self.prey_types.keys()))
        self.sprite = pygame_gui.elements.UIImage(
            scale(pygame.Rect((randrange(0+(self.size[0]), 1600-(self.size[0])), 0), self.size)),
            pygame.transform.scale(image_cache.load_image(f'resources/images/patrol_art/{self.selected_sprite}.png'),self.size),
            manager=MANAGER,
            starting_height=3,
        )
        self.current_game = cur_game
        self.speed = randrange(110, 220)
    
    def distance(self, obj2):
        newDist = math.sqrt(
                    math.pow(
                        self.sprite.relative_rect.center[0]-obj2.sprite.relative_rect.center[0],
                        2
                    )+math.pow(
                        self.sprite.relative_rect.center[1]-obj2.sprite.relative_rect.center[1],
                        2
                    )
                )
        return newDist

    def update(self, deltaTime):
        self.sprite.set_position((self.sprite.relative_rect.topleft[0], self.sprite.relative_rect.topleft[1]+((self.speed)*deltaTime)))
        distance = self.distance(self.current_game.player)
        if distance <= (135/1400)*screen_y:
            self.sprite.kill()
            self.current_game.score += self.prey_types[self.selected_sprite]
            self.current_game.entities.remove(self)
        if self.sprite.relative_rect.topleft[1] >= (1400/1400)*screen_y:
            self.sprite.kill()
            self.current_game.score -= int(self.prey_types[self.selected_sprite]/2)
            self.current_game.lives -= 1
            self.current_game.entities.remove(self)

            

class Player(Entity):
    speed = 150
    size = (225, 225)

    def getCatSpriteFromClanOfStatus(self, status):
        if status == "all":
            cats = get_alive_status_cats(Cat, [
                "leader",
                "deputy",
                "medicine cat",
                "medicine cat apprentice",
                "warrior",
                "apprentice",
                "queen",
                "elder",
                "kitten",
                "mediator",
                "mediator apprentice",
                "newborn",
            ])
        else:
            cats = get_alive_status_cats(Cat, [status])
        if len(cats) <= 0:
            cats = get_alive_status_cats(Cat, "warrior")
        selected_cat: Cat = choice(cats)
        return selected_cat.sprite

    def __init__(self, cur_game):
        current_sprite = self.getCatSpriteFromClanOfStatus("all")
        self.sprite = pygame_gui.elements.UIImage(
            scale(pygame.Rect((800, 1100), self.size)),
            pygame.transform.scale(
                current_sprite, self.size
            ),
            manager=MANAGER
        )
        self.current_game = cur_game

    def update(self, deltaTime):
        mouse = pygame.mouse.get_pos()
        current_zeroed_position = min(max(mouse[0], 0), 1600)
        self.sprite.set_position((current_zeroed_position-(self.size[0]/4), self.sprite.relative_rect.topleft[1]))