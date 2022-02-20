# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.cpb_gizmo`
================================================================================

Badge-focused CircuitPython helper library for Circuit Playground Bluefruit with TFT Gizmo.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Circuit Playground Bluefruit <https://www.adafruit.com/product/4333>`_
* `Adafruit TFT Gizmo <https://www.adafruit.com/product/4367>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import digitalio
import analogio
import busio
import audiopwmio
import keypad
from adafruit_gizmo import tft_gizmo
import adafruit_lis3dh
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase, KeyStates

try:
    from typing import Type
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b")


class CPB_Gizmo(PyBadgerBase):
    """Class that represents a single Circuit Playground Bluefruit with TFT Gizmo."""

    display = None
    _audio_out = audiopwmio.PWMAudioOut
    _neopixel_count = 10

    def __init__(self) -> None:
        super().__init__()

        _i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
        _int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        self.accelerometer = adafruit_lis3dh.LIS3DH_I2C(_i2c, address=0x19, int1=_int1)
        self.accelerometer.range = adafruit_lis3dh.RANGE_8_G

        self.display = tft_gizmo.TFT_Gizmo()
        self._display_brightness = 1.0

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        self._keys = keypad.Keys(
            [board.BUTTON_A, board.BUTTON_B], value_when_pressed=True, pull=True
        )
        self._buttons = KeyStates(self._keys)
        self._light_sensor = analogio.AnalogIn(board.LIGHT)

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
        """
        self._buttons.update()
        button_values = tuple(
            self._buttons.was_pressed(i) for i in range(self._keys.key_count)
        )
        return Buttons(button_values[0], button_values[1])

    @property
    def _unsupported(self):
        """This feature is not supported on CPB Gizmo."""
        raise NotImplementedError("This feature is not supported on CPB Gizmo.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CPB Gizmo. If called while using a CPB Gizmo, they will result in the
    # NotImplementedError raised in the property above.


cpb_gizmo = CPB_Gizmo()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
