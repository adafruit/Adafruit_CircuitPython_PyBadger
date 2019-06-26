# The MIT License (MIT)
#
# Copyright (c) 2019 Kattni Rembor for Adafruit Industries
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
`adafruit_pybadger`
================================================================================

Badge-focused CircuitPython helper library for PyBadge and PyGamer.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s). Use unordered list & hyperlink rST
   inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

.. todo:: Uncomment or remove the Bus Device and/or the Register library dependencies based on the library's use of either.

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import board
import time
import adafruit_lis3dh
import array
import audioio
import displayio
import digitalio
from gamepadshift import GamePadShift
from micropython import const
import math
import neopixel
import analogio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
import terminalio
from collections import namedtuple
import adafruit_miniqr

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "b a start select right down up left")


class PyBadger:
    # Button Constants
    BUTTON_LEFT = const(128)
    BUTTON_UP = const(64)
    BUTTON_DOWN = const(32)
    BUTTON_RIGHT = const(16)
    BUTTON_SELECT = const(8)
    BUTTON_START = const(4)
    BUTTON_A = const(2)
    BUTTON_B = const(1)

    def __init__(self, i2c=None):
        # Accelerometer
        if i2c is None:
            i2c = board.I2C()
        int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
        self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19, int1=int1)

        # Buttons
        self._buttons = GamePadShift(digitalio.DigitalInOut(board.BUTTON_CLOCK),
                                     digitalio.DigitalInOut(board.BUTTON_OUT),
                                     digitalio.DigitalInOut(board.BUTTON_LATCH))

        # Display
        self.display = board.DISPLAY

        # Light sensor
        self._light_sensor = analogio.AnalogIn(board.A7)

        # PyGamer joystick
        if hasattr(board, "JOYSTICK_X"):
            self._pygamer_joystick_x = analogio.AnalogIn(board.JOYSTICK_X)
            self._pygamer_joystick_y = analogio.AnalogIn(board.JOYSTICK_Y)

        # NeoPixels
        # Todo: Tie pixelcount to automatically figuring out which board is being used
        neopixel_count = 5
        self._neopixels = neopixel.NeoPixel(board.NEOPIXEL, neopixel_count,
                                            pixel_order=neopixel.GRB)

        # Auto dim display based on movement
        self._last_accelerometer = None
        self._start_time = time.monotonic()

        # Define audio:
        self._speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
        self._speaker_enable.switch_to_output(value=False)
        self._sample = None
        self._sine_wave = None
        self._sine_wave_sample = None

    def check_for_movement(self, movement_threshold=1.5):
        current_accelerometer = self.acceleration
        if self._last_accelerometer is None:
            self._last_accelerometer = current_accelerometer
            return False
        acceleration_delta = sum([abs(self._last_accelerometer[n] - current_accelerometer[n]) for n
                                  in range(3)])
        self._last_accelerometer = current_accelerometer
        return acceleration_delta > movement_threshold

    def auto_dim_display(self, delay=5.0):
        if not self.check_for_movement():
            current_time = time.monotonic()
            if current_time - self._start_time > delay:
                self.display.brightness = 0.1
                self._start_time = current_time
        else:
            self.display.brightness = 1

    @property
    def pixels(self):
        return self._neopixels

    @property
    def joystick(self):
        if hasattr(board, "JOYSTICK_X"):
            x = self._pygamer_joystick_x.value
            y = self._pygamer_joystick_y.value
            return x, y
        else:
            raise RuntimeError("This board does not have a built in joystick.")

    @property
    def button(self):
        button_values = self._buttons.get_pressed()
        return Buttons(*[button_values & button for button in
                         (BUTTON_B, BUTTON_A, BUTTON_START, BUTTON_SELECT, BUTTON_RIGHT,
                          BUTTON_DOWN, BUTTON_UP, BUTTON_LEFT)])

    @property
    def light(self):
        return self._light_sensor.value

    @property
    def acceleration(self):
        return self._accelerometer.acceleration

    @property
    def brightness(self):
        return self.display.brightness

    @brightness.setter
    def brightness(self, value):
        self.display.brightness = value

    def badge(self, *, background_color=0xFF0000, foreground_color=0xFFFFFF,
              background_text_color=0xFFFFFF, foreground_text_color=0x000000, hello_scale=1,
              hello_string="HELLO", my_name_is_scale=1, my_name_is_string="MY NAME IS",
              name_scale=1, name_string="Blinka"):
        # Make the Display Background
        splash = displayio.Group(max_size=20)

        color_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = background_color

        bg_sprite = displayio.TileGrid(color_bitmap,
                                       pixel_shader=color_palette,
                                       x=0, y=0)
        splash.append(bg_sprite)

        # Draw a Foreground Rectangle where the name goes
        # x, y, width, height
        rect = Rect(0, (int(self.display.height * 0.4)), self.display.width,
                    (int(self.display.height * 0.5)), fill=foreground_color)
        splash.append(rect)

        hello_scale = hello_scale
        hello_group = displayio.Group(scale=hello_scale)
        # Setup and Center the Hello Label
        hello_label = Label(terminalio.FONT, text=hello_string)
        (x, y, w, h) = hello_label.bounding_box
        hello_label.x = ((self.display.width // (2 * hello_scale)) - w // 2)
        hello_label.y = int(h // (1.2 * hello_scale))
        hello_label.color = background_text_color
        hello_group.append(hello_label)

        my_name_is_scale = my_name_is_scale
        my_name_is_group = displayio.Group(scale=my_name_is_scale)
        # Setup and Center the "My Name Is" Label
        my_name_is_label = Label(terminalio.FONT, text=my_name_is_string)
        (x, y, w, h) = my_name_is_label.bounding_box
        my_name_is_label.x = ((self.display.width // (2 * my_name_is_scale)) - w // 2)
        my_name_is_label.y = int(h // (0.42 * my_name_is_scale))
        my_name_is_label.color = background_text_color
        my_name_is_group.append(my_name_is_label)

        name_scale = name_scale
        name_group = displayio.Group(scale=name_scale)
        # Setup and Center the Name Label
        name_label = Label(terminalio.FONT, text=name_string)
        (x, y, w, h) = name_label.bounding_box
        name_label.x = ((self.display.width // (2 * name_scale)) - w // 2)
        name_label.y = int(h // (0.17 * name_scale))
        name_label.color = foreground_text_color
        name_group.append(name_label)

        group = displayio.Group()
        group.append(splash)
        group.append(hello_group)
        group.append(my_name_is_group)
        group.append(name_group)
        self.display.show(group)

    @staticmethod
    def bitmap_qr(matrix):
        # monochome (2 color) palette
        border_pixels = 2

        # bitmap the size of the screen, monochrome (2 colors)
        bitmap = displayio.Bitmap(matrix.width + 2 * border_pixels,
                                  matrix.height + 2 * border_pixels, 2)
        # raster the QR code
        for y in range(matrix.height):  # each scanline in the height
            for x in range(matrix.width):
                if matrix[x, y]:
                    bitmap[x + border_pixels, y + border_pixels] = 1
                else:
                    bitmap[x + border_pixels, y + border_pixels] = 0
        return bitmap

    def qr_code(self, data=b'https://circuitpython.org', dwell=20):
        qr = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
        qr.add_data(data)
        qr.make()
        qr_bitmap = self.bitmap_qr(qr.matrix)
        palette = displayio.Palette(2)
        palette[0] = 0xFFFFFF
        palette[1] = 0x000000
        qr_code_scale = min(self.display.width // qr_bitmap.width, self.display.height // qr_bitmap.height)
        qr_position_x = int(((self.display.width / qr_code_scale) - qr_bitmap.width) / 2)
        qr_position_y = int(((self.display.height / qr_code_scale) - qr_bitmap.height) / 2)
        qr_img = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=qr_position_x, y=qr_position_y)
        qr_code = displayio.Group(scale=qr_code_scale)
        qr_code.append(qr_img)
        self.display.show(qr_code)
        time.sleep(dwell)

    @staticmethod
    def _sine_sample(length):
        tone_volume = (2 ** 15) - 1
        shift = 2 ** 15
        for i in range(length):
            yield int(tone_volume * math.sin(2*math.pi*(i / length)) + shift)

    def _generate_sample(self, length=100):
        if self._sample is not None:
            return
        self._sine_wave = array.array("H", PyBadger._sine_sample(length))
        self._sample = audioio.AudioOut(board.SPEAKER)
        self._sine_wave_sample = audioio.RawSample(self._sine_wave)

    def play_tone(self, frequency, duration):
        """ Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone.

        :param int frequency: The frequency of the tone in Hz
        :param float duration: The duration of the tone in seconds

        """
        # Play a tone of the specified frequency (hz).
        self.start_tone(frequency)
        time.sleep(duration)
        self.stop_tone()

    def start_tone(self, frequency):
        """ Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone.

        :param int frequency: The frequency of the tone in Hz

        """
        self._speaker_enable.value = True
        length = 100
        if length * frequency > 350000:
            length = 350000 // frequency
        self._generate_sample(length)
        # Start playing a tone of the specified frequency (hz).
        self._sine_wave_sample.sample_rate = int(len(self._sine_wave) * frequency)
        if not self._sample.playing:
            self._sample.play(self._sine_wave_sample, loop=True)

    def stop_tone(self):
        """ Use with start_tone to stop the tone produced.

        """
        # Stop playing any tones.
        if self._sample is not None and self._sample.playing:
            self._sample.stop()
            self._sample.deinit()
            self._sample = None
        self._speaker_enable.value = False

    def play_file(self, file_name):
        """ Play a .wav file using the onboard speaker.

        :param file_name: The name of your .wav file in quotation marks including .wav

        """
        # Play a specified file.
        self.stop_tone()
        self._speaker_enable.value = True
        with audioio.AudioOut(board.SPEAKER) as audio:
            wavefile = audioio.WaveFile(open(file_name, "rb"))
            audio.play(wavefile)
            while audio.playing:
                pass
        self._speaker_enable.value = False
