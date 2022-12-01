# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.clue`
================================================================================

Badge-focused CircuitPython helper library for CLUE.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit CLUE <https://www.adafruit.com/product/4500>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import audiopwmio
import keypad
import adafruit_lsm6ds.lsm6ds33
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase, KeyStates

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b")


class Clue(PyBadgerBase):
    """Class that represents a single CLUE."""

    _audio_out = audiopwmio.PWMAudioOut
    _neopixel_count = 1

    def __init__(self) -> None:
        super().__init__()

        i2c = board.I2C()

        if i2c is not None:
            self._accelerometer = adafruit_lsm6ds.lsm6ds33.LSM6DS33(i2c)

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        self._keys = keypad.Keys(
            [board.BUTTON_A, board.BUTTON_B], value_when_pressed=False, pull=True
        )
        self._buttons = KeyStates(self._keys)

    @property
    def button(self) -> Buttons:
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.a:
                  print("Button A")
              elif pybadger.button.b:
                  print("Button B")
        """
        self._buttons.update()
        button_values = tuple(
            self._buttons.was_pressed(i) for i in range(self._keys.key_count)
        )
        return Buttons(button_values[0], button_values[1])

    @property
    def _unsupported(self):
        """This feature is not supported on CLUE."""
        raise NotImplementedError("This feature is not supported on CLUE.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CLUE. If called while using a CLUE, they will result in the
    # NotImplementedError raised in the property above.
    play_file = _unsupported
    light = _unsupported


clue = Clue()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
