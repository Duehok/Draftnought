# Draftnought
Editor for the top-view of the ships from the game Rule The Waves

## Use:
#### With the compiled releases:
start draftnought.exe

#### With python:
start main.py

  Use the "load ship file" or the menu option File => Open File, or the shortcut Ctrl-O to open a .<xy>d file.
  They can be found in your game folder, under /Save/Game<x>/
  
  
  Then draw to your heart content! you can pan the side view by holding the moise's left button and dragging and you can zoom this view with the mouse's scroll wheel. A grid to help align structures can be toggled under the Menu => View => Grid.
  
  You can move the vertexes of the superstructures by selecting them in the lists and editing their coordinates or clicking on the top view.
  The funnels can be toggled on/off, oval/round and placed by clicking on the top view or editing their coordinate.
  
  The coordinate system is:
  -origin in the middle of the ship
  - first coordinates along the axis bow-stern, increasing toward the stern
  - second coordinates along port-starboard, increasing toward starboard
  
  Don't forget to save! The last saved file is automatically loaded on the next start.

## Requirements
Python>=3.6
Windows 7+ for the build batch file
Tested on win 7 and 8.1, nothing else.

## Build:
run build.bat
