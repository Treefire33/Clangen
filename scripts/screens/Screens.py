from threading import current_thread
from typing import Dict, Optional, Union

import pygame
import pygame_gui
from pygame_gui.core import ObjectID

import scripts.game_structure.screen_settings
import scripts.screens.screens_core.screens_core
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.propagating_thread import PropagatingThread
from scripts.game_structure.screen_settings import (
    MANAGER,
    screen,
)
from scripts.game_structure.ui_elements import UIImageButton
from scripts.game_structure.windows import SaveCheck, EventLoading
from scripts.utility import (
    update_sprite,
    ui_scale,
    ui_scale_dimensions,
    ui_scale_blit,
    get_current_season,
)


class Screens:
    name = None
    game_screen = screen
    last_screen = ""

    # Looking for the shared assets across all screens (game frame, menu buttons etc.)?
    # Due to fullscreen shenanigans, this now lives here:
    # scripts/ui/screen_core/screen_core.py

    menu_buttons = scripts.screens.screens_core.screens_core.menu_buttons
    game_frame = scripts.screens.screens_core.screens_core.game_frame

    active_bg: Optional[str] = None

    def change_screen(self, new_screen):
        """Use this function when switching screens.
        It will handle keeping track of the last screen and cur screen.
        Last screen must be tracked to ensure a clear transition between screens."""
        # self.exit_screen()
        game.last_screen_forupdate = self.name

        # This keeps track of the last list-like screen for the back button on cat profiles
        if self.name in ["camp screen", "list screen", "events screen"]:
            game.last_screen_forProfile = self.name

        elif self.name not in [
            "list screen",
            "profile screen",
            "sprite inspect screen",
        ]:
            game.last_list_forProfile = None

        game.switches["cur_screen"] = new_screen
        game.switch_screens = True
        game.rpc.update_rpc.set()

    def __init__(self, name=None):
        self.previous_season = ""
        self.bg_transition = False
        self.bg_transition_time = 5
        self.name = name
        if name is not None:
            game.all_screens[name] = self

        # Place to store the loading window(s)
        self.loading_window = {}

        # Dictionary of work done, keyed by the target function name
        self.work_done = {}

        bg = pygame.Surface(scripts.game_structure.screen_settings.game_screen_size)
        bg.fill(game.config["theme"]["light_mode_background"])
        bg_dark = pygame.Surface(
            scripts.game_structure.screen_settings.game_screen_size
        )
        bg_dark.fill(game.config["theme"]["dark_mode_background"])

        self.game_bgs = {}
        self.fullscreen_bgs = {}

    def loading_screen_start_work(
        self, target: callable, thread_name: str = "work_thread", args: tuple = tuple()
    ) -> PropagatingThread:
        """Creates and starts the work_thread.
        Returns the started thread."""

        work_thread = PropagatingThread(
            target=self._work_target, args=(target, args), name=thread_name, daemon=True
        )

        work_thread.start()

        return work_thread

    def _work_target(self, target, args):
        exp = None
        try:
            target(*args)
        except Exception as e:
            exp = e

        self.work_done[current_thread().name] = True
        if exp:
            raise exp

    def loading_screen_on_use(
        self,
        work_thread: PropagatingThread,
        final_actions: callable,
        loading_screen_pos: tuple = None,
        delay: float = 0.7,
    ) -> None:
        """Handles all actions that must be run every frame for the loading window to work.
        Also handles creating and killing the loading window.
        """

        if not isinstance(work_thread, PropagatingThread):
            return

        # Handled the loading animation, both creating and killing it.
        if (
            not self.loading_window.get(work_thread.name)
            and work_thread.is_alive()
            and work_thread.get_time_from_start() > delay
        ):
            self.loading_window[work_thread.name] = EventLoading(loading_screen_pos)
        elif self.loading_window.get(work_thread.name) and not work_thread.is_alive():
            self.loading_window[work_thread.name].kill()
            self.loading_window.pop(work_thread.name)

        # Handles displaying the events once timeskip is done.
        if self.work_done.get(work_thread.name, False):
            # By this time, the thread should have already finished.
            # This line allows exceptions in the work thread to be
            # passed to the main thread, so issues in the work thread are not
            # silent failures.
            work_thread.join()

            self.work_done.pop(work_thread.name)

            final_actions()

        return

    def on_use(self):
        """Runs every frame this screen is used."""
        self.show_bg()

    def screen_switches(self):
        """Runs when this screen is switched to."""
        Screens.menu_buttons = scripts.screens.screens_core.screens_core.menu_buttons
        Screens.game_frame = scripts.screens.screens_core.screens_core.game_frame
        Screens.update_heading_text(game.clan.name + "Clan")
        if self.active_bg is None or "default" in self.active_bg:
            self.set_bg(None)
        self.bg_transition = True

    def handle_event(self, event):
        """This is where events that occur on this page are handled.
        For the pygame_gui rewrite, button presses are also handled here."""

    def exit_screen(self):
        """Runs when screen exits"""
        pass

    # Functions to deal with the menu.
    #   The menu is used very often, so I don't want to keep
    #   recreating and killing it. Lots of changes for bugs there.

    @classmethod
    def hide_menu_buttons(cls):
        """This hides the menu buttons, so they are no longer visible
        or interact-able. It does not delete the buttons from memory."""
        for button in cls.menu_buttons.values():
            button.hide()

    @classmethod
    def show_menu_buttons(cls):
        """This shows all menu buttons, and makes them interact-able."""
        # Check if the setting for moons and seasons UI is on so stats button can be moved
        cls.update_mns()
        for name, button in cls.menu_buttons.items():
            if name == "dens":
                if (
                    game.clan.clan_settings["moons and seasons"]
                    and game.switches["cur_screen"] == "events screen"
                ):
                    button.show()
                elif (
                    not game.clan.clan_settings["moons and seasons"]
                    and game.switches["cur_screen"] != "camp screen"
                ):
                    button.show()
            if name in [
                "moons_n_seasons",
                "moons_n_seasons_arrow",
                "dens",
                "med_cat_den",
                "lead_den",
                "clearing",
                "warrior_den",
                "dens_bar",
            ]:
                continue
            else:
                button.show()

    @classmethod
    def set_disabled_menu_buttons(cls, disabled_buttons=()):
        """This sets all menu buttons as interact-able, except buttons listed in disabled_buttons."""
        for name, button in cls.menu_buttons.items():
            button.disable() if name in disabled_buttons else button.enable()

    def menu_button_pressed(self, event):
        """This is a short-up to deal with menu button presses.
        This will fail if event.type != pygame_gui.UI_BUTTON_START_PRESS"""
        if event.ui_element == Screens.menu_buttons["events_screen"]:
            self.change_screen("events screen")
        elif event.ui_element == Screens.menu_buttons["camp_screen"]:
            self.change_screen("camp screen")
        elif event.ui_element == Screens.menu_buttons["catlist_screen"]:
            self.change_screen("list screen")
        elif event.ui_element == Screens.menu_buttons["patrol_screen"]:
            self.change_screen("patrol screen")
        elif event.ui_element == Screens.menu_buttons["main_menu"]:
            SaveCheck(
                game.switches["cur_screen"], True, Screens.menu_buttons["main_menu"]
            )
        elif event.ui_element == Screens.menu_buttons["allegiances"]:
            self.change_screen("allegiances screen")
        elif event.ui_element == Screens.menu_buttons["clan_settings"]:
            self.change_screen("clan settings screen")
        elif event.ui_element == Screens.menu_buttons["moons_n_seasons_arrow"]:
            if game.settings["mns open"]:
                game.settings["mns open"] = False
            else:
                game.settings["mns open"] = True
            self.update_mns()
        elif event.ui_element == Screens.menu_buttons["dens"]:
            self.update_dens()
        elif event.ui_element == Screens.menu_buttons["lead_den"]:
            self.change_screen("leader den screen")
        elif event.ui_element == Screens.menu_buttons["clearing"]:
            self.change_screen("clearing screen")
        elif event.ui_element == Screens.menu_buttons["med_cat_den"]:
            self.change_screen("med den screen")
        elif event.ui_element == Screens.menu_buttons["warrior_den"]:
            self.change_screen("warrior den screen")

    @classmethod
    def update_dens(cls):
        dens = [
            "dens_bar",
            "lead_den",
            "med_cat_den",
            "warrior_den",
            "clearing",
        ]

        for den in dens:
            # if dropdown is visible, hide
            if cls.menu_buttons[den].visible:
                cls.menu_buttons[den].hide()
            else:  # else, show
                if game.clan.game_mode != "classic":
                    cls.menu_buttons[den].show()
                else:  # classic doesn't get access to clearing, so we can't show its button here
                    if den == "clearing":
                        # redraw this to be shorter
                        cls.menu_buttons["dens_bar"].kill()
                        cls.menu_buttons.update(
                            {
                                "dens_bar": pygame_gui.elements.UIImage(
                                    ui_scale(pygame.Rect((40, 60), (10, 125))),
                                    pygame.transform.scale(
                                        image_cache.load_image(
                                            "resources/images/vertical_bar.png"
                                        ).convert_alpha(),
                                        ui_scale_dimensions((10, 125)),
                                    ),
                                    visible=True,
                                    starting_height=1,
                                    manager=MANAGER,
                                )
                            }
                        )
                    else:
                        cls.menu_buttons[den].show()

    @classmethod
    def update_heading_text(cls, text):
        """Updates the menu heading text"""
        cls.menu_buttons["heading"].set_text(text)

        # Update if moons and seasons UI is on

    @classmethod
    def update_mns(cls):
        if (
            game.clan.clan_settings["moons and seasons"]
            and game.switches["cur_screen"] != "events screen"
        ):
            cls.menu_buttons["moons_n_seasons_arrow"].kill()
            cls.menu_buttons["moons_n_seasons"].kill()
            if game.settings["mns open"]:
                if cls.name == "events screen":
                    cls.mns_close()
                else:
                    cls.mns_open()
            else:
                cls.mns_close()
        else:
            cls.menu_buttons["moons_n_seasons"].hide()
            cls.menu_buttons["moons_n_seasons_arrow"].hide()

    # open moons and seasons UI (AKA wide version)
    @classmethod
    def mns_open(cls):
        cls.menu_buttons["moons_n_seasons_arrow"] = UIImageButton(
            ui_scale(pygame.Rect((174, 80), (22, 34))),
            "",
            manager=MANAGER,
            object_id="#arrow_mns_button",
        )
        cls.menu_buttons["moons_n_seasons"] = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((25, 60), (153, 75))),
            allow_scroll_x=False,
            manager=MANAGER,
        )
        cls.moons_n_seasons_bg = UIImageButton(
            ui_scale(pygame.Rect((0, 0), (153, 75))),
            "",
            manager=MANAGER,
            object_id="#mns_bg",
            container=cls.menu_buttons["moons_n_seasons"],
        )

        if game.clan.age == 1:
            moons_text = "moon"
        else:
            moons_text = "moons"

        cls.moons_n_seasons_moon = UIImageButton(
            ui_scale(pygame.Rect((14, 10), (24, 24))),
            "",
            manager=MANAGER,
            object_id="#mns_image_moon",
            container=cls.menu_buttons["moons_n_seasons"],
        )
        cls.moons_n_seasons_text = pygame_gui.elements.UITextBox(
            f"{game.clan.age} {moons_text}",
            ui_scale(pygame.Rect((42, 6), (100, 30))),
            container=cls.menu_buttons["moons_n_seasons"],
            manager=MANAGER,
            object_id="#text_box_30_horizleft_light",
        )

        if game.clan.current_season == "Newleaf":
            season_image_id = "#mns_image_newleaf"
        elif game.clan.current_season == "Greenleaf":
            season_image_id = "#mns_image_greenleaf"
        elif game.clan.current_season == "Leaf-bare":
            season_image_id = "#mns_image_leafbare"
        elif game.clan.current_season == "Leaf-fall":
            season_image_id = "#mns_image_leaffall"
        else:
            season_image_id = MANAGER.get_universal_empty_surface()

        cls.moons_n_seasons_season = UIImageButton(
            ui_scale(pygame.Rect((14, 41), (24, 24))),
            "",
            manager=MANAGER,
            object_id=season_image_id,
            container=cls.menu_buttons["moons_n_seasons"],
        )
        cls.moons_n_seasons_text2 = pygame_gui.elements.UITextBox(
            f"{game.clan.current_season}",
            ui_scale(pygame.Rect((42, 36), (100, 30))),
            container=cls.menu_buttons["moons_n_seasons"],
            manager=MANAGER,
            object_id=ObjectID("#text_box_30_horizleft", "#dark"),
        )

    # close moons and seasons UI (AKA narrow version)
    @classmethod
    def mns_close(cls):
        cls.menu_buttons["moons_n_seasons_arrow"] = UIImageButton(
            ui_scale(pygame.Rect((71, 80), (22, 34))),
            "",
            object_id="#arrow_mns_closed_button",
        )
        if cls.name == "events screen":
            cls.menu_buttons["moons_n_seasons_arrow"].kill()

        cls.menu_buttons["moons_n_seasons"] = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((25, 60), (50, 75))),
            allow_scroll_x=False,
            manager=MANAGER,
        )
        cls.moons_n_seasons_bg = UIImageButton(
            ui_scale(pygame.Rect((0, 0), (50, 75))),
            "",
            manager=MANAGER,
            object_id="#mns_bg_closed",
            container=cls.menu_buttons["moons_n_seasons"],
        )

        if game.clan.age == 1:
            moons_text = "moon"
        else:
            moons_text = "moons"

        cls.moons_n_seasons_moon = UIImageButton(
            ui_scale(pygame.Rect((14, 10), (24, 24))),
            "",
            manager=MANAGER,
            object_id="#mns_image_moon",
            container=cls.menu_buttons["moons_n_seasons"],
            starting_height=2,
            tool_tip_text=f"{game.clan.age} {moons_text}",
        )

        if game.clan.current_season == "Newleaf":
            season_image_id = "#mns_image_newleaf"
        elif game.clan.current_season == "Greenleaf":
            season_image_id = "#mns_image_greenleaf"
        elif game.clan.current_season == "Leaf-bare":
            season_image_id = "#mns_image_leafbare"
        elif game.clan.current_season == "Leaf-fall":
            season_image_id = "#mns_image_leaffall"
        else:
            season_image_id = MANAGER.get_universal_empty_surface()

        cls.moons_n_seasons_season = UIImageButton(
            ui_scale(pygame.Rect((14, 41), (24, 24))),
            "",
            manager=MANAGER,
            object_id=season_image_id,
            container=cls.menu_buttons["moons_n_seasons"],
            starting_height=2,
            tool_tip_text=f"{game.clan.current_season}",
        )

    def add_bgs(
        self,
        bgs: Dict[str, pygame.Surface],
        blur_bgs: Dict[str, Union[pygame.Surface, None]] = None,
        radius: int = 5,
        vignette_alpha: int = 0,
    ):
        """
        Add custom backgrounds to the Screen.
        :param bgs: A dictionary of names and Surfaces representing the game window background
        :param blur_bgs: A dictionary of names and Surfaces/None representing the fullscreen backdrop.
        If a key is supplied with a None value, the default clan season background will be used.
        If no matching key is supplied, the input bg will be appropriately scaled and blurred to fit. Optional.
        :param radius: If a bg is missing a corresponding blur_bg value, this value determines how much
        to blur the bg to make the background. Default 10.
        :param vignette_alpha: Change the strength of the vignette. Value must be between 0 and 255. Default 0 (disabled/none).
        :return: None
        """

        # intialise the vignette strength
        vignette = scripts.screens.screens_core.screens_core.vignette
        if not (0 <= vignette_alpha <= 255):
            raise Exception("Vignette alpha out of range. Permitted values: 0-255.")
        vignette.set_alpha(vignette_alpha)

        # add the bg to the game bgs.
        for name, bg in bgs.items():
            self.game_bgs[name] = pygame.transform.scale(
                bg, scripts.game_structure.screen_settings.game_screen_size
            )

            # if blur_bgs exists
            if blur_bgs is not None and name in blur_bgs:
                if blur_bgs[name] is None:
                    self.fullscreen_bgs[name] = "default"
                    continue

                # there's an input blur_bg here, so scale it
                self.fullscreen_bgs[name] = pygame.transform.scale(
                    blur_bgs[name], screen.get_size()
                )

                # blit the vignette & game frame over the top for performance
                self.fullscreen_bgs[name].blits(
                    (
                        (vignette, (0, 0)),
                        (self.game_frame, ui_scale_blit((-10, -10))),
                    )
                )
                continue

            # no blur_bg, so blur the input bg to become the fullscreen backing
            self.fullscreen_bgs[name] = pygame.transform.box_blur(
                pygame.transform.scale(bg, screen.get_size()), radius
            )
            # also blit the vignette & game frame over the top of that for performance
            self.fullscreen_bgs[name].blits(
                (
                    (vignette, (0, 0)),
                    (self.game_frame, ui_scale_blit((-10, -10))),
                )
            )

    def set_bg(self, bg: Optional[str] = None):
        """
        Set the currently active background for a screen.
        :param bg: "default", or a key in either the game_bgs or default_game_bgs dictionaries.
        :return: None
        """
        # if the input is default, select the right default for the display mode
        if bg is None:
            self.active_bg = (
                "default_dark" if game.settings["dark mode"] else "default_light"
            )
        elif (
            bg in self.game_bgs
            or bg in scripts.screens.screens_core.screens_core.default_game_bgs
        ):
            self.active_bg = bg
        else:
            raise Exception(f"Unidentified background requested: '{bg}'")

        # enable the transition to get that sweet, sweet fullscreen fade.
        self.bg_transition = True

    def show_bg(self):
        """Blit the currently selected blur_bg and bg. Must be called somewhere in on_use."""
        # handle custom screen backgrounds (non-default)
        current_season = get_current_season()
        if self.active_bg in self.game_bgs:
            bg = self.game_bgs[self.active_bg]

            # if the blur_bg associated with this is "default", select the blurred current season
            # otherwise, select the custom blur_bg
            blur_bg = (
                scripts.screens.screens_core.screens_core.default_fullscreen_bgs[
                    current_season
                ]
                if self.fullscreen_bgs[self.active_bg] == "default"
                else self.fullscreen_bgs[self.active_bg]
            )

            # show transition if the season has just changed
            if (
                self.previous_season != current_season
                and self.fullscreen_bgs[self.active_bg] == "default"
            ):
                self.bg_transition_time = 10  # doubled transition time for the Vibes
                self.previous_season = current_season

        # handle default screen backgrounds
        elif (
            self.active_bg in scripts.screens.screens_core.screens_core.default_game_bgs
        ):
            bg = scripts.screens.screens_core.screens_core.default_game_bgs[
                self.active_bg
            ]

            # if we're in the main menu, don't display the clan season BG. just show default mode-appropriate colour.
            if self.name in [
                "make clan screen",
                "settings screen",
                "switch clan screen",
            ]:
                blur_bg = (
                    scripts.screens.screens_core.screens_core.default_fullscreen_bgs[
                        "default_dark"
                        if game.settings["dark mode"]
                        else "default_light"
                    ]
                )
            else:
                # otherwise, season bg as before
                blur_bg = (
                    scripts.screens.screens_core.screens_core.default_fullscreen_bgs[
                        current_season
                    ]
                )
                if self.previous_season != current_season:
                    self.bg_transition_time = (
                        10  # doubled transition time for the Vibes
                    )
                    self.previous_season = current_season
        else:
            raise Exception(
                f"Selected background not recognised! '{self.active_bg}' not in default or custom bgs"
            )

        # onto the actual blitting
        # handle the blur bg
        if game.settings["fullscreen"]:
            # enable the transition if required
            if self.bg_transition:
                # this determines how many frames the fade can show for
                # in order to remove visual artifacts
                self.bg_transition_time = 5
                self.bg_transition = False

            # actually run the transition
            if self.bg_transition_time > 0:
                temp = blur_bg.copy()
                temp.set_alpha(
                    255 // self.bg_transition_time
                )  # this determines the actual fade rate
                scripts.game_structure.screen_settings.screen.blit(temp, (0, 0))
                self.bg_transition_time -= 1
            else:
                # if we've done the transition, just blit the full-alpha version on top to remove artifacts.
                scripts.game_structure.screen_settings.screen.blit(blur_bg, (0, 0))

        # now blit the foreground.
        scripts.game_structure.screen_settings.screen.blit(bg, ui_scale_blit((0, 0)))

    def display_change_save(self) -> Dict:
        """
        Used to save a dictionary of data to help rebuild the screen the way it was when we return.
        :return: A dictionary of data to be used later to rebuild the screen
        """
        return {
            "heading": scripts.screens.screens_core.screens_core.menu_buttons[
                "heading"
            ].html_text
        }

    def display_change_load(self, variable_dict: Dict):
        """
        Used to load the screen back to how it was following a display change.
        :return: None
        """
        try:
            scripts.screens.screens_core.screens_core.menu_buttons["heading"].set_text(
                variable_dict.pop("heading")
            )
        except KeyError:
            pass


# CAT PROFILES
def cat_profiles():
    """Updates every cat's sprites"""
    game.choose_cats.clear()

    for x in Cat.all_cats:
        update_sprite(Cat.all_cats[x])
