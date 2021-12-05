# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.pybadge`
================================================================================

Badge-focused CircuitPython helper library for PyBadge, PyBadge LC and EdgeBadge.
All three boards are included in this module as there is no difference in the
CircuitPython builds at this time, and therefore no way to differentiate
the boards from within CircuitPython.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyBadge <https://www.adafruit.com/product/4200>`_
* `Adafruit PyBadge LC <https://www.adafruit.com/product/3939>`_
* `Adafruit EdgeBadge <https://www.adafruit.com/product/4400>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import digitalio
import analogio
import audioio
import keypad
import adafruit_lis3dh
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase, KeyStates

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "b a start select right down up left")


class PyBadge(PyBadgerBase):
    """Class that represents a single PyBadge, PyBadge LC, or EdgeBadge."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 5

    def __init__(self):
        super().__init__()

        i2c = None

        if i2c is None:
            try:
                i2c = board.I2C()
            except RuntimeError:
                self._accelerometer = None

        if i2c is not None:
            while not i2c.try_lock():
                pass
            _i2c_devices = i2c.scan()
            i2c.unlock()

            # PyBadge LC doesn't have accelerometer
            if int(0x18) in _i2c_devices or int(0x19) in _i2c_devices:
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
            key_count=8,
            value_when_pressed=True,
        )
        self._buttons = KeyStates(self._keys)

        self._light_sensor = analogio.AnalogIn(board.A7)

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
              elif pybadger.button.start:
                  print("Button start")
              elif pybadger.button.select:
                  print("Button select")

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
            button_values[7],
        )


pybadge = PyBadge()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
