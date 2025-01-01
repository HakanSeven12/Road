# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2025 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD, FreeCADGui
from pivy import coin

class ViewTracker:
    def __init__(self, eventid="Event", key=None, state="Down", function=None, cancelable=True):
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.eventid = eventid
        self.key = key
        self.state = state
        self.function = function
        self.cancelable = cancelable

        self.eventids = {
            "Event": coin.SoEvent.getClassTypeId(),
            "Button": coin.SoButtonEvent.getClassTypeId(),
            "Keyboard": coin.SoKeyboardEvent.getClassTypeId(),
            "Location": coin.SoLocation2Event.getClassTypeId(),
            "Mouse": coin.SoMouseButtonEvent.getClassTypeId()}

        self.states = {
            "Up": coin.SoMouseButtonEvent.UP,
            "Down": coin.SoMouseButtonEvent.DOWN,
            "Unknown": coin.SoMouseButtonEvent.UNKNOWN}

        self.buttons = {
            "Any": coin.SoMouseButtonEvent.ANY,
            "Left": coin.SoMouseButtonEvent.BUTTON1,
            "Middle": coin.SoMouseButtonEvent.BUTTON2,
            "Right": coin.SoMouseButtonEvent.BUTTON3,
            "Well Up": coin.SoMouseButtonEvent.BUTTON4,
            "Well Down": coin.SoMouseButtonEvent.BUTTON5}

        self.keys = {
            "Any": coin.SoKeyboardEvent.ANY,
            "Undefined": coin.SoKeyboardEvent.UNDEFINED,
            "Left Shift": coin.SoKeyboardEvent.LEFT_SHIFT,
            "Right Shift": coin.SoKeyboardEvent.RIGHT_SHIFT,
            "Left Control": coin.SoKeyboardEvent.LEFT_CONTROL,
            "Right Control": coin.SoKeyboardEvent.RIGHT_CONTROL,
            "Left Alt": coin.SoKeyboardEvent.LEFT_ALT,
            "Right Alt": coin.SoKeyboardEvent.RIGHT_ALT,
            "0": coin.SoKeyboardEvent.NUMBER_0,
            "1": coin.SoKeyboardEvent.NUMBER_1,
            "2": coin.SoKeyboardEvent.NUMBER_2,
            "3": coin.SoKeyboardEvent.NUMBER_3,
            "4": coin.SoKeyboardEvent.NUMBER_4,
            "5": coin.SoKeyboardEvent.NUMBER_5,
            "6": coin.SoKeyboardEvent.NUMBER_6,
            "7": coin.SoKeyboardEvent.NUMBER_7,
            "8": coin.SoKeyboardEvent.NUMBER_8,
            "9": coin.SoKeyboardEvent.NUMBER_9,
            "A": coin.SoKeyboardEvent.A,
            "B": coin.SoKeyboardEvent.B,
            "C": coin.SoKeyboardEvent.C,
            "D": coin.SoKeyboardEvent.D,
            "E": coin.SoKeyboardEvent.E,
            "F": coin.SoKeyboardEvent.F,
            "G": coin.SoKeyboardEvent.G,
            "H": coin.SoKeyboardEvent.H,
            "I": coin.SoKeyboardEvent.I,
            "J": coin.SoKeyboardEvent.J,
            "K": coin.SoKeyboardEvent.K,
            "L": coin.SoKeyboardEvent.L,
            "M": coin.SoKeyboardEvent.M,
            "N": coin.SoKeyboardEvent.N,
            "O": coin.SoKeyboardEvent.O,
            "P": coin.SoKeyboardEvent.P,
            "Q": coin.SoKeyboardEvent.Q,
            "R": coin.SoKeyboardEvent.R,
            "S": coin.SoKeyboardEvent.S,
            "T": coin.SoKeyboardEvent.T,
            "U": coin.SoKeyboardEvent.U,
            "V": coin.SoKeyboardEvent.V,
            "W": coin.SoKeyboardEvent.W,
            "X": coin.SoKeyboardEvent.X,
            "Y": coin.SoKeyboardEvent.Y,
            "Z": coin.SoKeyboardEvent.Z,
            "Home": coin.SoKeyboardEvent.HOME,
            "Left Arrow": coin.SoKeyboardEvent.LEFT_ARROW,
            "Up Arrow": coin.SoKeyboardEvent.UP_ARROW,
            "Right Arrow": coin.SoKeyboardEvent.RIGHT_ARROW,
            "Down Arrow": coin.SoKeyboardEvent.DOWN_ARROW,
            "Page Up": coin.SoKeyboardEvent.PAGE_UP,
            "Page Down": coin.SoKeyboardEvent.PAGE_DOWN,
            "End": coin.SoKeyboardEvent.END,
            "Prior": coin.SoKeyboardEvent.PRIOR,
            "Next": coin.SoKeyboardEvent.NEXT,
            "Pad Enter": coin.SoKeyboardEvent.PAD_ENTER,
            "Pad F1": coin.SoKeyboardEvent.PAD_F1,
            "Pad F2": coin.SoKeyboardEvent.PAD_F2,
            "Pad F3": coin.SoKeyboardEvent.PAD_F3,
            "Pad F4": coin.SoKeyboardEvent.PAD_F4,
            "Pad 0": coin.SoKeyboardEvent.PAD_0,
            "Pad 1": coin.SoKeyboardEvent.PAD_1,
            "Pad 2": coin.SoKeyboardEvent.PAD_2,
            "Pad 3": coin.SoKeyboardEvent.PAD_3,
            "Pad 4": coin.SoKeyboardEvent.PAD_4,
            "Pad 5": coin.SoKeyboardEvent.PAD_5,
            "Pad 6": coin.SoKeyboardEvent.PAD_6,
            "Pad 7": coin.SoKeyboardEvent.PAD_7,
            "Pad 8": coin.SoKeyboardEvent.PAD_8,
            "Pad 9": coin.SoKeyboardEvent.PAD_9,
            "Pad Add": coin.SoKeyboardEvent.PAD_ADD,
            "Pad Subtract": coin.SoKeyboardEvent.PAD_SUBTRACT,
            "Pad Multiply": coin.SoKeyboardEvent.PAD_MULTIPLY,
            "Pad Divide": coin.SoKeyboardEvent.PAD_DIVIDE,
            "Pad Space": coin.SoKeyboardEvent.PAD_SPACE,
            "Pad Tab": coin.SoKeyboardEvent.PAD_TAB,
            "Pad Insert": coin.SoKeyboardEvent.PAD_INSERT,
            "Pad Delete": coin.SoKeyboardEvent.PAD_DELETE,
            "Pad Period": coin.SoKeyboardEvent.PAD_PERIOD,
            "F1": coin.SoKeyboardEvent.F1,
            "F2": coin.SoKeyboardEvent.F2,
            "F3": coin.SoKeyboardEvent.F3,
            "F4": coin.SoKeyboardEvent.F4,
            "F5": coin.SoKeyboardEvent.F5,
            "F6": coin.SoKeyboardEvent.F6,
            "F7": coin.SoKeyboardEvent.F7,
            "F8": coin.SoKeyboardEvent.F8,
            "F9": coin.SoKeyboardEvent.F9,
            "F10": coin.SoKeyboardEvent.F10,
            "F11": coin.SoKeyboardEvent.F11,
            "F12": coin.SoKeyboardEvent.F12,
            "Backspace": coin.SoKeyboardEvent.BACKSPACE,
            "Tab": coin.SoKeyboardEvent.TAB,
            "Return": coin.SoKeyboardEvent.RETURN,
            "Enter": coin.SoKeyboardEvent.ENTER,
            "Pause": coin.SoKeyboardEvent.PAUSE,
            "Scroll Lock": coin.SoKeyboardEvent.SCROLL_LOCK,
            "Escape": coin.SoKeyboardEvent.ESCAPE,
            "Delete": coin.SoKeyboardEvent.DELETE,
            "Key Delete": coin.SoKeyboardEvent.KEY_DELETE,
            "Print": coin.SoKeyboardEvent.PRINT,
            "Insert": coin.SoKeyboardEvent.INSERT,
            "Num Lock": coin.SoKeyboardEvent.NUM_LOCK,
            "Caps Lock": coin.SoKeyboardEvent.CAPS_LOCK,
            "Shift Lock": coin.SoKeyboardEvent.SHIFT_LOCK,
            "Space": coin.SoKeyboardEvent.SPACE,
            "Apostrophe": coin.SoKeyboardEvent.APOSTROPHE,
            "Comma": coin.SoKeyboardEvent.COMMA,
            "Minus": coin.SoKeyboardEvent.MINUS,
            "Period": coin.SoKeyboardEvent.PERIOD,
            "Slash": coin.SoKeyboardEvent.SLASH,
            "Semicolon": coin.SoKeyboardEvent.SEMICOLON,
            "Equal": coin.SoKeyboardEvent.EQUAL,
            "Bracketleft": coin.SoKeyboardEvent.BRACKETLEFT,
            "Backslash": coin.SoKeyboardEvent.BACKSLASH,
            "Bracketright": coin.SoKeyboardEvent.BRACKETRIGHT,
            "Grave": coin.SoKeyboardEvent.GRAVE}

    def start(self):
        self.callback = self.view.addEventCallbackPivy(
            self.eventids[self.eventid], self.tracker)

        self.cancel = self.view.addEventCallbackPivy(
            self.eventids["Keyboard"], self.tracker)

    def tracker(self, callback):
        event = callback.getEvent()

        if event.getTypeId().isDerivedFrom(self.eventids["Location"]):
            if self.eventid == "Location" and self.function: self.function(callback)
    
        elif event.getTypeId().isDerivedFrom(self.eventids["Keyboard"]):
            if event.getKey() == self.keys.get("Escape") and event.getState() == self.states.get("Down"):
                if self.cancelable: self.stop(True)

            elif event.getKey() == self.keys.get(self.key) and event.getState() == self.states.get(self.state):
                print(f"Key '{self.key}' pressed with state '{self.state}'")
                if self.eventid == "Keyboard" and self.function: self.function(callback)

        elif event.getTypeId().isDerivedFrom(self.eventids["Mouse"]):
            if event.getButton() == self.buttons.get(self.key) and event.getState() == self.states.get(self.state):
                print(f"Mouse button '{self.key}' clicked with state '{self.state}'")
                if self.eventid == "Mouse" and self.function: self.function(callback)

    def stop(self, canceled=False):
        self.view.removeEventCallbackPivy(
            self.eventids[self.eventid], self.callback)
        self.view.removeEventCallbackPivy(
            self.eventids["Keyboard"], self.cancel)
        if canceled: FreeCAD.Console.PrintWarning("Canceled")