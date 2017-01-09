# Brickly

Brickly is a port of [Blockly](https://developers.google.com/blockly/)
to the [Fischertechnik TXT](http://www.fischertechnik.de/en/desktopdefault.aspx/tabid-21/39_read-309/usetemplate-2_column_pano/). Brickly makes allows to program the TXT from any web browser
using a simple graphical user interface. If you don't have a TXT then
the [Blocly Games](https://blockly-games.appspot.com/) can give you 
a first impression how Blockly looks and works.

# Internals

Brickly code generation happens on client side. If the user hits the
"Run..." button then the Brickly app on the TXT is being launched if
it's not already running.

The browser then esablishes a websocket connection to the Brickly
app which it uses to send and receive commands. Whenever the user
hits "Run..." the code is being sent from the browser to the TXT
where it is being saved in flash memeory.

The browser then sends various further commands e.g. to set execution
speed and to permanently store the current skill level and language
on the TXT until it instructs the TXT to execute the code.

The brickly program is stored on TXT side in its own xml format
as well as in the python language used for actual execution.
