OSPy Readme
====

An improved Python port of the Arduino based OpenSprinkler firmware.

Because the web interface is based on the original firmware,
the basics described in the [user manual](http://rayshobby.net/opensprinkler/svc-use/svc-web) are still applicable.  
This is my fork from Rimco/OSPy (https://github.com/Rimco/OSPy) with My modifications.

## Installation

### Preferred option (using Git)
(This option does support automatic updating.)

1. Ensure git is installed (and the git executable is in your path).
2. Use git to clone https://github.com/martinpihrt/OSPy.git to a location of your choice.

### Second option (without Git)
(This option does *not* support automatic updating.)

1. Download a copy of the program from https://github.com/martinpihrt/OSPy/archive/master.zip.
2. Extract the contents to a location of your choice.

## Setup
A setup file has been provided to help you setting up your environment to contain all required packages.
This setup also helps you in case you want to run the program as a service (on Raspbian).

1. Go to the folder where the setup.py file is located.
2. Execute: python setup.py install
3. Follow the procedures of the script.

## License
OpenSprinkler Py (OSPy) Interval Program

Creative Commons Attribution-ShareAlike 3.0 license

## Acknowledgements
Full credit goes to Dan for his generous contributions in porting the microcontroller firmware to Python.

The program makes use of web.py (http://webpy.org) for the web interface.

The program makes use of gfm (https://github.com/dart-lang/py-gfm) to render the help pages written in GitHub flavored markdown.

The program makes use of pygments (http://pygments.org) to provide syntax highlighting in the help pages.

