Rubiks Cube Solver
==================

This is the source code of the Rubiks cube solver shown at 

https://www.youtube.com/watch?v=Maiqnr2TZks

The machanics
-------------

The cube resides on a turn table. The table can be turned in steps
of 90 degrees. The turn table is driven by a encoder motor (M). But the 
encoders are not used. A switch (SW) is used to determine when the cube 
reaches one of the four positions. The motor will run while the switch is
not pressed. If the switch is being pressed and the TXT's O4 output is
of the motor will stop immediately (both motor inputs tied to GND). If the
TXT drives O4 high then the motor will run. The TXT can monitor via
input I1 if the motor is still running or of it has reached the next
stop position.


```
 +--------------------| GND 
 |
(M)    +--------------> +9V
 |     |  
 |     o   o----------< TXT-O4
 |      \
 |    V--\  (SW)
 |        \
 +---------o----------> TXT-I1
```

A "pusher" arm can tilt the whole cube. The pusher consists of two 
pneumatic cylinders in series to allow it to extend sufficiently. The
pusher is controlled via a magnetic valve connected to the TXTs output O3.

A "grabber" allows the robot to grab the middle section of the cube
enabling the turn table to only turn the cubes bottom face while 
holding the middle and upper layers in position. The grabbers pneumatic
cylinder is also controlled via magnetic valve on TXT's output O2.

The compressor for the pneumatics is connected to the TXTs output O1.
