#Imports
import pygame
import pygame_gui
import os, configparser #not ujson because .ini files are better for config
from requests.exceptions import RequestException, Timeout

from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from .base_screens import Screens
from scripts.game_structure.image_button import UIImageButton
from scripts.game_structure.windows import DeleteCheck, UpdateAvailablePopup, ChangelogPopup, SaveError
from scripts.utility import get_text_box_theme, scale, quit  # pylint: disable=redefined-builtin
from ..housekeeping.datadir import get_data_dir, get_cache_dir, get_themes_dir
from re import sub

class ThemeCreationScreen(Screens):

    theme_name = ""
    lightmode_color = ""
    darkmode_color = ""

    def __init__(self, name=None):
        super().__init__(name)
        screen.fill((150,189,212))
        
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.submit_button:
                new_name = sub(r'[^A-Za-z0-9_,]+', "", self.theme_name_field.get_text()).strip()
                new_lightcolor = sub(r'[^A-Za-z0-9_,]+', "", self.lightmode_color_field.get_text()).strip()
                new_darkcolor = sub(r'[^A-Za-z0-9_,]+', "", self.darkmode_color_field.get_text()).strip()
                self.theme_name = new_name
                self.lightmode_color = new_lightcolor
                self.darkmode_color = new_darkcolor
                if self.create_theme_file() == 0:
                    self.change_screen('start screen')
                    print('successful')
                    self.theme_name_field.kill()
                    self.title.kill()
                    self.theme_name_label.kill()
                    self.darkmode_color_field.kill()
                    self.darkmode_color_label.kill()
                    self.lightmode_color_field.kill()
                    self.lightmode_color_label.kill()
                    self.submit_button.kill()
                else:
                    print('error, whoops')
    
    def screen_switches(self):
        #Other
        self.title = pygame_gui.elements.UITextBox(
            "Theme Creator",
            scale(pygame.Rect((screen_x-(screen_x/2), 0), (screen_x, 80))),
            object_id="#text_box_100_horizcenter_dark",
            manager=MANAGER,
            starting_height=1
        )
        #Creation
        self.theme_name_label = pygame_gui.elements.UITextBox(
            "Theme Name:",
            scale(pygame.Rect((100, 370), (280, 58))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
        )
        self.theme_name_field = pygame_gui.elements.UITextEntryLine(
            scale(pygame.Rect((100, 428), ((screen_x*2)-200, 58))), 
            manager=MANAGER
        )
        self.lightmode_color_label = pygame_gui.elements.UITextBox(
            'Light Mode Color (Format as "num,num,num"):',
            scale(pygame.Rect((100, 535), (screen_x*2, 58))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
        )
        self.lightmode_color_field = pygame_gui.elements.UITextEntryLine(
            scale(pygame.Rect((100, 593), ((screen_x*2)-200, 58))), 
            manager=MANAGER
        )
        self.darkmode_color_label = pygame_gui.elements.UITextBox(
            'Dark Mode Color (Format as "num,num,num"):',
            scale(pygame.Rect((100, 639), (screen_x*2, 58))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
        )
        self.darkmode_color_field = pygame_gui.elements.UITextEntryLine(
            scale(pygame.Rect((100, 697), ((screen_x*2)-200, 58))), 
            manager=MANAGER
        )
        #Submission of theme
        self.submit_button = UIImageButton(
            scale(pygame.Rect((screen_x-(400/2), screen_y+400), (400, 80))),
            "Submit",
            object_id="#submit_button",
            manager=MANAGER,
            starting_height=0,
        )
        #Error
        errorimg = image_cache.load_image(
            'resources/images/errormsg.png').convert_alpha()
        self.error_box = pygame_gui.elements.UIImage(
            scale(pygame.Rect((259, 300), (1180, 802))),
            pygame.transform.scale(errorimg, (1180, 802)),
            manager=MANAGER
        )

        self.error_box.disable()

        self.error_label = pygame_gui.elements.UITextBox(
            "",
            scale(pygame.Rect((275, 370), (770, 720))),
            object_id="#text_box_22_horizleft",
            manager=MANAGER,
            starting_height=3
        )

        self.error_box.hide()
        self.error_label.hide()

    def create_theme_file(self):
        config = configparser.RawConfigParser()
        config.optionxform = str
        try:
            if not os.path.exists(get_themes_dir()+"/"+self.theme_name):
                os.makedirs(get_themes_dir()+"/"+self.theme_name)
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/images")
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/images/camp_bg")
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites")
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/dicts")
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/faded")
                os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/paralyzed")
                config["Light_Mode"] = {"Fill": self.lightmode_color}
                config["Dark_Mode"] = {"Fill": self.darkmode_color}
                config["Background"] = {"Path": 'images/camp_bg/'}
                config["Sprites"] = {"Path": 'sprites/', 'Replace': 'False'}
                config.write(open(get_themes_dir()+"/"+self.theme_name+"/"+'theme.ini', 'w'))
            else:
                config["Light_Mode"] = {"Fill": self.lightmode_color}
                config["Dark_Mode"] = {"Fill": self.darkmode_color}
                config["Background"] = {"Path": 'images/camp_bg/'}
                config["Sprites"] = {"Path": 'sprites/', 'Replace': 'False'}
                config.write(open(get_themes_dir()+"/"+self.theme_name+"/"+'theme.ini', 'w'))
            return 0
        except Exception as error:
            print(error)
            return 1

    