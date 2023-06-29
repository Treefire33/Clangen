# How to setup .ini file:
## Sections:
[Light_Mode], [Dark_Mode] -These sections are seperate because they require some different sprites. <br>
Attributes of above sections: <br>
Fill - number,number,number (no spaces, must be valid RGB) - fill color for solid color screens. <br>
[Backgrounds] -Select backgrounds <br>
Attributes: <br>
Path - path to backgrounds - Check default theme if you want to know how to structure the backgrounds folder.<br>
<br>
Example:<br>
[Light_Mode]<br>
Fill = 0,0,0<br>
[Dark_Mode]<br>
Fill = 255,255,255<br>
[Backgrounds]<br>
Path = images/camp_bg<br>

## Modifying your game_config.json:
Scroll until you find the "theme" config.<br>
Change "current_theme" to the path where the theme folder is. Example: "themes/default/" or "C:/.../Downloads/default/" (The last slash in the path is necessary).<br>
<br>

<b>Now you can experience a themed Clangen!</b>

<b>More features are coming soon</b>