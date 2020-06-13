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
`adafruit_pybadger.pyportal`
================================================================================

Badge-focused CircuitPython helper library for PyPortal.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyPortal <https://www.adafruit.com/product/4116>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import audioio
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"


class PyPortal(PyBadgerBase):
    """Class that represents a single PyPortal."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 1

    @property
    def _unsupported(self):
        """This feature is not supported on PyPortal."""
        raise NotImplementedError("This feature is not supported on PyPortal.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for PyPortal. If called while using a PyPortal, they will result in the
    # NotImplementedError raised in the property above.
    play_file = _unsupported
    light = _unsupported
    button = _unsupported


pyportal = PyPortal()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
