# Brickly

Brickly code generation happens on client side. If the user hits the
"Run..." button then the code is POSTed into a python CGI script. That
script stored the code in a file on server side. It then forks a 
background process, starts a python wrapper and reports the process
id of the wrapper to the client. The client then repeatedly tries to
connect to a websocket server.

The wrapper sets up a websocket server which is from then on used to
send all redirected output from stdout to. The wrapper ten loads and
runs the code.

The client receives the text output from the code via websocket and
displays it.

The client can stop the running code by sending the PID to a stop
script on the server.

If the TXT launcher is present on the system then a Qt app will be 
started to run the blockly code in a local GUI as well.

The blockly program is stored on server side in xml format.
