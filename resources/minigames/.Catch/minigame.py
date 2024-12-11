# pylint: disable=line-too-long
# pylint: disable=unused-import
import pygame
import pygame_gui
import pygame_gui.elements.ui_text_box

from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER, screen_x, screen_y
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, ui_scale, quit, get_alive_status_cats  # pylint: disable=redefined-builtin
from scripts.minigames.Minigame import Minigame
from scripts.minigames.Entity import Entity
from random import random, randrange, choice, sample
import math

class Catch(Minigame):
    player = None
    score = 0
    lives = 5

    def load_minigame(self):
        self.play_game = True
        self.player = Player(self)
        self.current_drop_cooldown = pygame.time.get_ticks()
        self.entities.append(self.player)

        self.elements["score_label"] = pygame_gui.elements.UITextBox(
            "Score: "+str(self.score),
            minigame_scale(pygame.Rect((0, 0), (800, 50))),
            object_id=get_text_box_theme("#text_box_40")
        )
        self.elements["lives_label"] = pygame_gui.elements.UITextBox(
            "Lives: "+str(self.lives),
            minigame_scale(pygame.Rect((0, 50), (800, 50))),
            object_id=get_text_box_theme("#text_box_40")
        )
        errorimg = image_cache.load_image(
            "resources/images/errormsg.png"
        ).convert_alpha()
        self.elements["game_over_box"] = pygame_gui.elements.UIImage(
            minigame_scale(pygame.Rect((130, 150), (590, 401))),
            pygame.transform.scale(errorimg, (590, 401)),
            starting_height=400,
            manager=MANAGER,
        )
        self.elements["game_over_label"] = pygame_gui.elements.UITextBox(
            "",
            minigame_scale(pygame.Rect((138, 185), (385, 360))),
            object_id="#text_box_40",
            starting_height=400,
            manager=MANAGER,
        )
        del errorimg
        self.elements["game_over_box"].hide()
        self.elements["game_over_label"].hide()
    
    debug_game = False
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and self.play_game and self.debug_game:
                self.spawn_prey()

    def spawn_prey(self):
        new_prey = Prey(self)
        self.entities.append(new_prey)

    drop_cooldown = 2100
    def update(self, delta_time):
        if self.play_game:
            if pygame.time.get_ticks() - self.current_drop_cooldown >= self.drop_cooldown:
                self.current_drop_cooldown = pygame.time.get_ticks()
                self.spawn_prey()
                self.drop_cooldown = max(self.drop_cooldown-delta_time*(460), 620)
            
            self.elements["score_label"].set_text(f"Score: {self.score}")
            self.elements["lives_label"].set_text(f"Lives: {self.lives}")
            if self.lives <= 0:
                self.play_game = False
                self.game_over_box.show()
                self.game_over_label.show()
                self.game_over_label.set_text("You lost...")
            super().update(delta_time)
    
    def exit_minigame(self):
        self.play_game = False
        super().exit_minigame()

class Prey(Entity):
    speed = 125
    size = (50, 50)

    prey_types = {
        "mtn_hunt_shrew": 5,
        "fst_hunt_vole": 10,
        "pln_hunt_prairiedog1": 15
    }
    selected_sprite = "mtn_hunt_shrew"
    def __init__(self, cur_game):
        self.selected_sprite = choice(list(self.prey_types.keys()))
        self.sprite = pygame_gui.elements.UIImage(
            minigame_scale(pygame.Rect((randrange(0+(self.size[0]), 800-(self.size[0])), 0), self.size)),
            pygame.transform.scale(image_cache.load_image(f'resources/images/patrol_art/{self.selected_sprite}.png'),self.size),
            manager=MANAGER,
            starting_height=3
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
    size = (125, 125)

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