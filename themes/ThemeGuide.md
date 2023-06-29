# How to setup .ini file:
## Sections:
[Light_Mode], [Dark_Mode] -These sections are seperate because they require some different sprites. <br>
Attributes of above sections: <br>
Fill - number,number,number (no spaces, must be valid RGB) - fill color for solid color screens. <br>
[Backgrounds] -Select backgrounds <br>
Attributes: <br>
Path - path to backgrounds - Check default theme if you want to know how to structure the backgrounds folder.<br>
[Sprites] -Change sprites and replace them<br>
Attributes: <br>
Path - path to sprites - This folder should be structured the same as included sprites folder<br>
Replace - boolean - When true, replaces sprites, when false, doesn't<br>
<br>
Example:<br>
[Light_Mode]<br>
Fill = 206,194,168<br>
[Dark_Mode]<br>
Fill = 57,50,36<br>
[Backgrounds]<br>
Path = images/camp_bg/<br>
[Sprites]<br>
Path = sprites/<br>
Replace = False<br>

## Modifying your game_config.json:
Scroll until you find the "theme" config.<br>
Change "current_theme" to the name of the theme. Example: "default" or "test"<br>
<br>

<b>Now you can experience a themed Clangen!</b>

<b>More features are coming soon</b>