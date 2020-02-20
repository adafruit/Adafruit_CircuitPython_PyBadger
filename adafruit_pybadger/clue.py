# The MIT License (MIT)
#
# Copyright (c) 2020 Kattni Rembor for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
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
import digitalio
import audiopwmio
from gamepad import GamePad
import adafruit_lsm6ds
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b")

class Clue(PyBadgerBase):
    """Class that represents a single CLUE."""
    _audio_out = audiopwmio.PWMAudioOut
    _neopixel_count = 1

    def __init__(self):
        super().__init__()

        i2c = board.I2C()

        if i2c is not None:
            self._accelerometer = adafruit_lsm6ds.LSM6DS33(i2c)

        self._buttons = GamePad(digitalio.DigitalInOut(board.BUTTON_A),
                                digitalio.DigitalInOut(board.BUTTON_B))

    @property
    def button(self):
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
        button_values = self._buttons.get_pressed()
        return Buttons(button_values & PyBadgerBase.BUTTON_B,
                       button_values & PyBadgerBase.BUTTON_A)


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
