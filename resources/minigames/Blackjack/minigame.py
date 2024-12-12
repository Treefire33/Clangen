# pylint: disable=line-too-long
# pylint: disable=unused-import
import pygame
import pygame_gui
import pygame_gui.elements.ui_text_box
import os
import time

from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER, screen_x, screen_y
from scripts.game_structure.ui_elements import UIImageButton, UIImageHorizontalSlider, UISurfaceImageButton
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from pygame_gui.elements import UITextBox, UIImage, UIWindow
from scripts.cat.cats import Cat
from scripts.utility import get_text_box_theme, ui_scale, quit, get_alive_status_cats, ui_scale_offset  # pylint: disable=redefined-builtin
from scripts.minigames.Minigame import Minigame
from scripts.minigames.Entity import Entity
from random import random, randrange, choice, sample
from enum import Enum

class Blackjack(Minigame):
    player_hand_value: int = 0
    opponent_hand_value: int = 0
    _turn = False
    opponent_hand = []
    player_hand = []

    current_deck = []

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, state):
        self._turn = state
        self.elements["hit_button"].visible = state
        self.elements["stay_button"].visible = state
        

    DECK = None

    @staticmethod
    def instance_deck():
        if Blackjack.DECK is None:
            Blackjack.DECK = []
            Blackjack.DECK += [CardType.ACE]*4
            Blackjack.DECK += [CardType.TWO]*4
            Blackjack.DECK += [CardType.THREE]*4
            Blackjack.DECK += [CardType.FOUR]*4
            Blackjack.DECK += [CardType.FIVE]*4
            Blackjack.DECK += [CardType.SIX]*4
            Blackjack.DECK += [CardType.SEVEN]*4
            Blackjack.DECK += [CardType.EIGHT]*4
            Blackjack.DECK += [CardType.NINE]*4
            Blackjack.DECK += [CardType.TEN]*4
            Blackjack.DECK += [CardType.JACK]*4
            Blackjack.DECK += [CardType.QUEEN]*4
            Blackjack.DECK += [CardType.KING]*4

    def load_minigame(self):
        Blackjack.instance_deck()
        self.current_deck = Blackjack.DECK.copy()
        self.player_hand_value = 0
        self.opponent_hand_value = 0
        self._turn = False
        self.opponent_hand = []
        self.player_hand = []
        self.create_element("player_cur_value", UITextBox(
            "Hand Value: 0",
            ui_scale(pygame.Rect(0, 200, 600, 50)),
            MANAGER,
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            anchors={
                "center": "center",
            }
        ))

        self.create_element("opponent_cur_value", UITextBox(
            "Opponent Hand Value: 0",
            ui_scale(pygame.Rect(0, -200, 600, 50)),
            MANAGER,
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            anchors={
                "center": "center",
            }
        ))
        #self.elements["opponent_cur_value"].hide()

        self.create_element("hit_button", UISurfaceImageButton(
            ui_scale(pygame.Rect(-80, 150, 100, 30)),
            "Hit",
            get_button_dict(ButtonStyles.SQUOVAL, (100, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_rounded_rect",
            anchors={
                "center": "center"
            }
        ))

        self.create_element("stay_button", UISurfaceImageButton(
            ui_scale(pygame.Rect(80, 150, 100, 30)),
            "Stay",
            get_button_dict(ButtonStyles.SQUOVAL, (100, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_rounded_rect",
            anchors={
                "center": "center",
            }
        ))
        self.elements["hit_button"].hide()
        self.elements["stay_button"].hide()

        self.deal_card()
        self.deal_card()
        self.turn = True
        return super().load_minigame()

    def deal_card(self):
        selected_card : CardType = self.current_deck.pop(randrange(0, len(self.current_deck)))
        if not self.turn:
            if selected_card == CardType.ACE:
                selected_card = choice([CardType.ACE, CardType.ACE_11])
            self.opponent_hand.append(selected_card)
        else:
            if selected_card == CardType.ACE:
                # self.prompt_ace_value()
                selected_card = choice([CardType.ACE, CardType.ACE_11])
            self.player_hand.append(selected_card)

        self.calculate_hand_value()

    # prompt_open = False
    # def prompt_ace_value(self):
    #     self.create_element("ace_prompt_window", AcePrompt(self))
    #     self.prompt_open = True
  
    def calculate_hand_value(self):
        self.opponent_hand_value = 0
        self.player_hand_value = 0

        for card in self.opponent_hand:
            if card in (CardType.JACK, CardType.QUEEN, CardType.KING):
                self.opponent_hand_value += 10
            self.opponent_hand_value += card.value

        for card in self.player_hand:
            if card in (CardType.JACK, CardType.QUEEN, CardType.KING):
                self.player_hand_value += 10
            self.player_hand_value += card.value

        self.elements["player_cur_value"].set_text("Hand Value: " + str(self.player_hand_value))
        self.elements["opponent_cur_value"].set_text("Opponent Hand Value: " + str(self.opponent_hand_value))
  
    def handle_event(self, event):
        if self.play_game:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if self.turn:
                    if event.ui_element == self.elements["hit_button"]:
                        self.deal_card()
                    elif event.ui_element == self.elements["stay_button"]:
                        self.turn = False
        return super().handle_event(event)
    
    def update(self, delta_time):
        if self.play_game:
            if not self.turn and 0 <= self.opponent_hand_value <= 13:
                self.deal_card()
                self.turn = True
        super().update(delta_time)

class CardType(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ACE_11 = 11 # reserve 11 for an ace
    JACK = 12
    QUEEN = 13
    KING = 14

class Card(Entity):
    card_type : CardType = CardType.ACE
    card_size = (50, 100)

    def __init__(self, value: CardType, cur_game: Blackjack):
        self.card_type = value
        self.sprite = UIImage(
            ui_scale(pygame.Rect((0, 0), self.card_size)),
            pygame.transform.scale(image_cache.load_image(cur_game.minigame_path + "card.png"), self.card_size),
            manager=MANAGER,
            anchors={
                "center": "center"
            }
        )
        self.card_text = UITextBox(
            str(value),
            ui_scale(pygame.Rect((0, 0), self.card_size)),
            object_id=get_text_box_theme("#text_box_30_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={
                "center": "center"
            }
        )
        super().__init__()
    
    def kill(self):
        self.card_text.kill()
        self.card_text = None
        super().kill()

# class AcePrompt(UIWindow):
#     decided_value = 0
#     decided = False

#     cur_game = None

#     def __init__(self, cur_game):
#         self.cur_game = cur_game
#         super().__init__(
#             ui_scale(pygame.Rect(250, 200, 300, 200)),
#             window_display_title="Ace Prompt",
#             object_id="#save_check_window",
#             resizable=False,
#             always_on_top=True
#         )

#         self.info = UITextBox(
#             "You drew an ace, 1 or 11?",
#             ui_scale(pygame.Rect(0, 0, 300, 100)),
#             manager=MANAGER,
#             object_id=get_text_box_theme("#text_box_22_horizcenter"),
#             anchors={
#                 "centerx": "centerx"
#             }
#         )

#         self.yes_button = UISurfaceImageButton(
#             ui_scale(pygame.Rect(-125, 0, 125, 100)),
#             "1",
#             image_dict=get_button_dict(ButtonStyles.SQUOVAL, (125, 100)),
#             manager=MANAGER,
#             anchors={
#                 "centerx": "centerx"
#             }
#         )

#         self.no_button = UISurfaceImageButton(
#             ui_scale(pygame.Rect(-125, 0, 125, 100)),
#             "11",
#             image_dict=get_button_dict(ButtonStyles.SQUOVAL, (125, 100)),
#             manager=MANAGER,
#             anchors={
#                 "centerx": "centerx"
#             }
#         )

#         self.set_blocking(True)

#     def process_event(self, event):
#         if event.type == pygame_gui.UI_BUTTON_START_PRESS:
#             if event.ui_element == self.yes_button:
#                 self.decided_value = 1
#                 self.hide()
#                 self.decided = True
#                 self.cur_game.prompt_open = False
#             elif event.ui_element == self.no_button:
#                 self.decided_value = 11
#                 self.hide()
#                 self.decided = True
#                 self.cur_game.prompt_open = False
#         return super().process_event(event)

