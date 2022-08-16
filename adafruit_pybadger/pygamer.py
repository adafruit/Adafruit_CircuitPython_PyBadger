# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.pygamer`
================================================================================

Badge-focused CircuitPython helper library for PyGamer.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyGamer <https://www.adafruit.com/product/4277>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import analogio
import digitalio
import audioio
import neopixel
import keypad
import adafruit_lis3dh
from adafruit_pybadger.pybadger_base import PyBadgerBase, KeyStates

try:
    from typing import Type, Tuple
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "b a start select right down up left")


class PyGamer(PyBadgerBase):
    """Class that represents a single PyGamer."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 5

    def __init__(self) -> None:
        super().__init__()

        i2c = board.I2C()

        int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        try:
            self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(
                i2c, address=0x19, int1=int1
            )
        except ValueError:
            self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        self._keys = keypad.ShiftRegisterKeys(
            clock=board.BUTTON_CLOCK,
            data=board.BUTTON_OUT,
            latch=board.BUTTON_LATCH,
            key_count=4,
            value_when_pressed=True,
        )
        self._buttons = KeyStates(self._keys)

        self._pygamer_joystick_x = analogio.AnalogIn(board.JOYSTICK_X)
        self._pygamer_joystick_y = analogio.AnalogIn(board.JOYSTICK_Y)

        self._light_sensor = analogio.AnalogIn(board.A7)

    @property
    def button(self) -> Type[tuple]:
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.a:
                  print("Button A")
              elif pybadger.button.b:
                  print("Button B")
              elif pybadger.button.start:
                  print("Button start")
              elif pybadger.button.select:
                  print("Button select")

        """
        self._buttons.update()
        button_values = tuple(
            self._buttons.was_pressed(i) for i in range(self._keys.key_count)
        )
        x, y = self.joystick
        return Buttons(
            button_values[0],
            button_values[1],
            button_values[2],
            button_values[3],
            x > 50000,  # RIGHT
            y > 50000,  # DOWN
            y < 15000,  # UP
            x < 15000,  # LEFT
        )

    @property
    def joystick(self) -> Tuple[int, int]:
        """The joystick on the PyGamer."""
        x = self._pygamer_joystick_x.value
        y = self._pygamer_joystick_y.value
        return x, y


pygamer = PyGamer()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
