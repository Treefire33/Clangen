#Imports
import pygame
import pygame_gui
import os
import configparser
import shutil
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
    background_path = ""
    sprites_path = ""
    bkgr_not_provided = False
    spr_not_provived = False

    def __init__(self, name=None):
        ThemeRelatedFunctions.load_owned_themes()
        super().__init__(name)
        screen.fill((150,189,212))
        
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.submit_button:
                new_name = sub(r'[^A-Za-z0-9_,]+', "", self.theme_name_field.get_text()).strip()
                new_lightcolor = sub(r'[^A-Za-z0-9_,]+', "", self.lightmode_color_field.get_text()).strip()
                new_darkcolor = sub(r'[^A-Za-z0-9_,]+', "", self.darkmode_color_field.get_text()).strip()
                if not self.background_path_field.get_text() == None:
                    temp_backgroundpath = sub(r'[^A-Za-z0-9_,\\:]+', "", self.background_path_field.get_text()).strip()
                    new_backgroundpath = temp_backgroundpath.replace("\\", "/")
                else:
                    self.bkgr_not_provided = True
                if not self.sprite_path_field.get_text() == None:
                    temp_spritespath = sub(r'[^A-Za-z0-9_,\\:]+', "", self.sprite_path_field.get_text()).strip()
                    new_spritespath = temp_spritespath.replace("\\", "/")
                else:
                    self.spr_not_provived = True
                self.theme_name = new_name
                self.lightmode_color = new_lightcolor
                self.darkmode_color = new_darkcolor
                self.background_path = new_backgroundpath
                self.sprites_path = new_spritespath
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
                    self.background_path_label.kill()
                    self.background_path_field.kill()
                    self.sprite_path_field.kill()
                    self.sprite_path_label.kill()
                    self.notice_label.kill()
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
        self.background_path_label = pygame_gui.elements.UITextBox(
            'Background Images (Only camp backgrounds so far, optional):',
            scale(pygame.Rect((100, 743), (screen_x*2, 58))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
        )
        self.background_path_field = pygame_gui.elements.UITextEntryLine(
            scale(pygame.Rect((100, 801), ((screen_x*2)-200, 58))), 
            manager=MANAGER
        )
        self.sprite_path_label = pygame_gui.elements.UITextBox(
            'Sprites (Sprites folder should be structured like the main sprites folder, optional):',
            scale(pygame.Rect((100, 847), (screen_x*2, 58))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
        )
        self.sprite_path_field = pygame_gui.elements.UITextEntryLine(
            scale(pygame.Rect((100, 905), ((screen_x*2)-200, 58))), 
            manager=MANAGER
        )
        self.notice_label = pygame_gui.elements.UITextBox(
            'Important: Sprites and background folders are copied to the theme folder.<br>Please use paths starting with C:\.',
            scale(pygame.Rect((100, 951), (screen_x*2, 150))),
            object_id="#text_box_34_horizleft_dark",
            manager=MANAGER,
            starting_height=1
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
                if self.bkgr_not_provided == True:
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/images")
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/images/camp_bg")
                if self.spr_not_provived == True:
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites")
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/dicts")
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/faded")
                    os.makedirs(get_themes_dir()+"/"+self.theme_name+"/sprites/paralyzed")
                shutil.copytree(self.background_path, get_themes_dir()+"/"+self.theme_name+"/images", copy_function = shutil.copy)
                shutil.copytree(self.sprites_path, get_themes_dir()+"/"+self.theme_name+"/sprites", copy_function = shutil.copy)
                config["Light_Mode"] = {"Fill": self.lightmode_color}
                config["Dark_Mode"] = {"Fill": self.darkmode_color}
                config["Background"] = {"Path": 'images/camp_bg/'}
                config["Sprites"] = {"Path": 'sprites/', 'Replace': 'False'}
                config.write(open(get_themes_dir()+"/"+self.theme_name+"/"+'theme.ini', 'w'))
            else:
                shutil.copytree(self.background_path, get_themes_dir()+"/"+self.theme_name+"/images", copy_function = shutil.copy)
                shutil.copytree(self.sprites_path, get_themes_dir()+"/"+self.theme_name+"/sprites", copy_function = shutil.copy)
                config["Light_Mode"] = {"Fill": self.lightmode_color}
                config["Dark_Mode"] = {"Fill": self.darkmode_color}
                config["Background"] = {"Path": 'images/camp_bg/'}
                config["Sprites"] = {"Path": 'sprites/', 'Replace': 'False'}
                config.write(open(get_themes_dir()+"/"+self.theme_name+"/"+'theme.ini', 'w'))
            return 0
        except Exception as error:
            print(error)
            return 1

class ThemeRelatedFunctions():
    def load_owned_themes():
        for root, dirs, files in os.walk(get_themes_dir()):
            print(dirs)
            return dirs
    def copy_default_themes():
        if not os.path.exists(get_themes_dir()+"/default"):
            shutil.copytree("./themes/default", get_themes_dir())
            shutil.copytree("./themes/cooler_colors", get_themes_dir())