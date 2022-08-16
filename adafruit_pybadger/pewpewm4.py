# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.pewpewm4`
================================================================================

Badge-focused CircuitPython helper library for Pew Pew M4.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Pew Pew M4 <https://hackaday.io/project/165032-pewpew-m4>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import audioio
import keypad
from adafruit_pybadger.pybadger_base import PyBadgerBase, KeyStates

try:
    from typing import Type
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", ("o", "x", "z", "right", "down", "up", "left"))


class PewPewM4(PyBadgerBase):
    """Class that represents a single Pew Pew M4."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 0

    def __init__(self) -> None:
        super().__init__()

        self._keys = keypad.Keys(
            [
                board.BUTTON_O,
                board.BUTTON_X,
                board.BUTTON_Z,
                board.BUTTON_RIGHT,
                board.BUTTON_DOWN,
                board.BUTTON_UP,
                board.BUTTON_LEFT,
            ],
            value_when_pressed=False,
            pull=True,
        )

        self._buttons = KeyStates(self._keys)

    @property
    def button(self) -> Type[tuple]:
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.x:
                  print("Button X")
              elif pybadger.button.o:
                  print("Button O")
        """
        self._buttons.update()
        button_values = tuple(
            self._buttons.was_pressed(i) for i in range(self._keys.key_count)
        )
        return Buttons(
            button_values[0],
            button_values[1],
            button_values[2],
            button_values[3],
            button_values[4],
            button_values[5],
            button_values[6],
        )

    @property
    def _unsupported(self):
        """This feature is not supported on PewPew M4."""
        raise NotImplementedError("This feature is not supported on PewPew M4.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CLUE. If called while using a CLUE, they will result in the
    # NotImplementedError raised in the property above.
    light = _unsupported
    acceleration = _unsupported
    pixels = _unsupported


pewpewm4 = PewPewM4()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
