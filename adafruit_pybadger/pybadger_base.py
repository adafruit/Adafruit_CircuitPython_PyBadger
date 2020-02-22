# The MIT License (MIT)
#
# Copyright (c) 2019-2020 Kattni Rembor for Adafruit Industries
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
`adafruit_pybadger.pybadger_base`
================================================================================

Base class for badge-focused CircuitPython helper library.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit CLUE <https://www.adafruit.com/product/4500>`_
* `Adafruit PyBadge <https://www.adafruit.com/product/4200>`_
* `Adafruit PyBadge LC <https://www.adafruit.com/product/3939>`_
* `Adafruit PyGamer <https://www.adafruit.com/product/4277>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import time
import array
import math
import board
from micropython import const
import digitalio
try:
    import audiocore
except ImportError:
    import audioio as audiocore
import displayio
import neopixel
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import terminalio
import adafruit_miniqr

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

def load_font(fontname, text):
    """Load a font and glyphs in the text string

    :param str fontname: The full path to the font file.
    :param str text: The text containing the glyphs we want to load.

    """
    font = bitmap_font.load_font(fontname)
    font.load_glyphs(text.encode('utf-8'))
    return font

class _PyBadgerCustomBadge:
    """Easily display lines of text on CLUE display."""
    def __init__(self, background_group):
        self._label = label
        self.display = board.DISPLAY

        self.custom_badge_group = displayio.Group(max_size=20)

        self.text_group = displayio.Group(max_size=20)

        self._lines = []
        for _ in range(1):
            self._lines.append(self._add_text_line())

        self.custom_badge_group.append(background_group)
        self.custom_badge_group.append(self.text_group)

    def __getitem__(self, item):
        """Fetch the Nth text line Group"""
        if len(self._lines) - 1 < item:
            for _ in range(item - (len(self._lines) - 1)):
                self._lines.append(self._add_text_line())
        return self._lines[item]

    def _add_text_line(self, color=0xFFFFFF):
        """Adds a line on the display of the specified color and returns the label object."""
        text_label = self._label.Label(font=terminalio.FONT, text="", max_glyphs=45, color=color)
        self.text_group.append(text_label)
        return text_label

    def show(self):
        """Call show() to display the badge lines."""
        self.display.show(self.custom_badge_group)

# pylint: disable=too-many-instance-attributes
class PyBadgerBase:
    """PyBadger base class."""

    _audio_out = None
    _neopixel_count = None

    # Color variables available for import.
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 150, 0)
    GREEN = (0, 255, 0)
    TEAL = (0, 255, 120)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)
    MAGENTA = (255, 0, 150)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    GOLD = (255, 222, 30)
    PINK = (242, 90, 255)
    AQUA = (50, 255, 255)
    JADE = (0, 255, 40)
    AMBER = (255, 100, 0)
    VIOLET = (255, 0, 255)
    SKY = (0, 180, 255)

    RAINBOW = (RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE)

    # Button Constants
    BUTTON_LEFT = const(128)
    BUTTON_UP = const(64)
    BUTTON_DOWN = const(32)
    BUTTON_RIGHT = const(16)
    BUTTON_SELECT = const(8)
    BUTTON_START = const(4)
    BUTTON_A = const(2)
    BUTTON_B = const(1)

    def __init__(self, *, pixels_brightness=1.0):
        self._light_sensor = None
        self._accelerometer = None
        self._label = label
        self.custom_badge_object = None
        self._y_position = 1
        self._line_number = 0
        self._background_group = None

        # Display
        self.display = board.DISPLAY
        self._display_brightness = 1.0

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(board.NEOPIXEL, self._neopixel_count,
                                            brightness=pixels_brightness, pixel_order=neopixel.GRB)

        # Auto dim display based on movement
        self._last_accelerometer = None
        self._start_time = time.monotonic()

        # Define audio:
        if hasattr(board, "SPEAKER_ENABLE"):
            self._speaker_enable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
            self._speaker_enable.switch_to_output(value=False)
        self._sample = None
        self._sine_wave = None
        self._sine_wave_sample = None

    def _custom_badge(self):
        background_group = self._background_group
        if not background_group:
            background_group = self._badge_background()
        return _PyBadgerCustomBadge(background_group)

    def badge_background(self, background_color=(255, 0, 0), rectangle_color=(255, 255, 255),
                         rectangle_drop=0.4, rectangle_height=0.5):
        self._background_group = self._badge_background(background_color, rectangle_color,
                                                        rectangle_drop, rectangle_height)
        return self._background_group

    @classmethod
    def _badge_background(cls, background_color=(255, 0, 0), rectangle_color=(255, 255, 255),
                          rectangle_drop=0.4, rectangle_height=0.5):
        """Populate the background color, and rectangle color block over it as the background for
         a name badge."""
        background_group = displayio.Group(max_size=2)
        color_bitmap = displayio.Bitmap(board.DISPLAY.width, board.DISPLAY.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = background_color

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        background_group.append(bg_sprite)

        rectangle = Rect(0, (int(board.DISPLAY.height * rectangle_drop)), board.DISPLAY.width,
                         (int(board.DISPLAY.height * rectangle_height)), fill=rectangle_color)
        background_group.append(rectangle)
        return background_group

    # pylint: disable=too-many-arguments
    def badge_line(self, text=" ", color=(0, 0, 0), scale=1, font=terminalio.FONT,
                   left_justify=False):
        if isinstance(font, str):
            font = load_font(font, text)

        if self.custom_badge_object is None:
            self.custom_badge_object = self._custom_badge()

        self.custom_badge_object[self._line_number].font = font
        self.custom_badge_object[self._line_number].scale = scale
        self.custom_badge_object[self._line_number].text = text
        self.custom_badge_object[self._line_number].color = color

        _, _, width, height = self.custom_badge_object[self._line_number].bounding_box
        if not left_justify:
            self.custom_badge_object[self._line_number].x = (self.display.width // 2) - \
                                                        ((width * scale) // 2)
        else:
            self.custom_badge_object[self._line_number].x = 0

        trim_y = 0
        if font is terminalio.FONT:
            trim_y = 4 * scale
        self.custom_badge_object[self._line_number].y = self._y_position + ((height // 2) *
                                                                            scale) - trim_y
        if font is terminalio.FONT:
            self._y_position += height * scale - trim_y
        else:
            self._y_position += height * scale + 4
        self._line_number += 1

    def show(self):
        return self.custom_badge_object.show()

    # pylint: disable=too-many-arguments
    def _create_label_group(self, text, font,
                            scale, height_adjustment,
                            color=0xFFFFFF, width_adjustment=2, line_spacing=0.75):
        """Create a label group with the given text, font, and spacing"""
        # If the given font is a string, treat it as a file path and try to load it
        if isinstance(font, str):
            font = load_font(font, text)

        create_label_group = displayio.Group(scale=scale)
        create_label = self._label.Label(font, text=text, line_spacing=line_spacing)
        _, _, width, _ = create_label.bounding_box
        create_label.x = ((self.display.width // (width_adjustment * scale)) - width // 2)
        create_label.y = int(self.display.height * (height_adjustment / scale))
        create_label.color = color
        create_label_group.append(create_label)
        return create_label_group

    def _check_for_movement(self, movement_threshold=10):
        """Checks to see if board is moving. Used to auto-dim display when not moving."""
        current_accelerometer = self.acceleration
        if self._last_accelerometer is None:
            self._last_accelerometer = current_accelerometer
            return False
        acceleration_delta = sum([abs(self._last_accelerometer[n] - current_accelerometer[n]) for n
                                  in range(3)])
        self._last_accelerometer = current_accelerometer
        return acceleration_delta > movement_threshold

    def auto_dim_display(self, delay=5.0, movement_threshold=10):
        """Auto-dim the display when board is not moving.

        :param int delay: Time in seconds before display auto-dims after movement has ceased.
        :param int movement_threshold: Threshold required for movement to be considered stopped.
                                       Change to increase or decrease sensitivity.

        """
        if not self._check_for_movement(movement_threshold=movement_threshold):
            current_time = time.monotonic()
            if current_time - self._start_time > delay:
                self.display.brightness = 0.1
                self._start_time = current_time
        else:
            self.display.brightness = self._display_brightness

    @property
    def pixels(self):
        """Sequence like object representing the NeoPixels on the board."""
        return self._neopixels

    @property
    def light(self):
        """Light sensor data."""
        return self._light_sensor.value

    @property
    def acceleration(self):
        """Accelerometer data, +/- 2G sensitivity."""
        return self._accelerometer.acceleration if self._accelerometer is not None else None

    @property
    def brightness(self):
        """Display brightness."""
        return self.display.brightness

    @brightness.setter
    def brightness(self, value):
        self._display_brightness = value
        self.display.brightness = value

    # pylint: disable=too-many-locals
    def show_business_card(self, *, image_name=None, name_string=None, name_scale=1,
                           name_font=terminalio.FONT, email_string_one=None,
                           email_scale_one=1, email_font_one=terminalio.FONT,
                           email_string_two=None, email_scale_two=1,
                           email_font_two=terminalio.FONT):
        """Display a bitmap image and a text string, such as a personal image and email address.

        :param str image_name: REQUIRED. The name of the bitmap image including .bmp, e.g.
                               ``"Blinka.bmp"``.
        :param str name_string: A name string to display along the bottom of the display, e.g.
                                 ``"Blinka"``.
        :param int name_scale: The scale of ``name_string``. Defaults to 1.
        :param name_font: The font for the name string. Defaults to ``terminalio.FONT``.
        :param str email_string_one: A string to display along the bottom of the display, e.g.
                                 ``"blinka@adafruit.com"``.
        :param int email_scale_one: The scale of ``email_string_one``. Defaults to 1.
        :param email_font_one: The font for the first email string. Defaults to ``terminalio.FONT``.
        :param str email_string_two: A second string to display along the bottom of the display.
                                     Use if your email address is longer than one line or to add
                                     more space between the name and email address,
                                     e.g. (blinka@) ``"adafruit.com"``.
        :param int email_scale_two: The scale of ``email_string_two``. Defaults to 1.
        :param email_font_two: The font for the second email string. Defaults to
                               ``terminalio.FONT``.

        """
        business_card_label_groups = []
        if name_string:
            name_group = self._create_label_group(text=name_string,
                                                  font=name_font,
                                                  scale=name_scale,
                                                  height_adjustment=0.73)
            business_card_label_groups.append(name_group)
        if email_string_one:
            email_one_group = self._create_label_group(text=email_string_one,
                                                       font=email_font_one,
                                                       scale=email_scale_one,
                                                       height_adjustment=0.84)
            business_card_label_groups.append(email_one_group)
        if email_string_two:
            email_two_group = self._create_label_group(text=email_string_two,
                                                       font=email_font_two,
                                                       scale=email_scale_two,
                                                       height_adjustment=0.91)
            business_card_label_groups.append(email_two_group)

        business_card_splash = displayio.Group(max_size=4)
        self.display.show(business_card_splash)
        with open(image_name, "rb") as file_name:
            on_disk_bitmap = displayio.OnDiskBitmap(file_name)
            face_image = displayio.TileGrid(on_disk_bitmap, pixel_shader=displayio.ColorConverter())
            business_card_splash.append(face_image)
            for group in business_card_label_groups:
                business_card_splash.append(group)
            try:
                # Refresh display in CircuitPython 5
                self.display.refresh()
            except AttributeError:
                # Refresh display in CircuitPython 4
                self.display.wait_for_frame()

    # pylint: disable=too-many-locals
    def show_badge(self, *, background_color=0xFF0000, foreground_color=0xFFFFFF,
                   background_text_color=0xFFFFFF, foreground_text_color=0x000000,
                   hello_font=terminalio.FONT, hello_scale=1, hello_string="HELLO",
                   my_name_is_font=terminalio.FONT, my_name_is_scale=1,
                   my_name_is_string="MY NAME IS", name_font=terminalio.FONT, name_scale=1,
                   name_string="Blinka"):
        """Create a "Hello My Name is"-style badge.

        :param background_color: The color of the background. Defaults to 0xFF0000.
        :param foreground_color: The color of the foreground rectangle. Defaults to 0xFFFFFF.
        :param background_text_color: The color of the "HELLO MY NAME IS" text. Defaults to
                                      0xFFFFFF.
        :param foreground_text_color: The color of the name text. Defaults to 0x000000.
        :param hello_font: The font for the "HELLO" string. Defaults to ``terminalio.FONT``.
        :param hello_scale: The size scale of the "HELLO" string. Defaults to 1.
        :param hello_string: The first string of the badge. Defaults to "HELLO".
        :param my_name_is_font: The font for the "MY NAME IS" string. Defaults to
                                ``terminalio.FONT``.
        :param my_name_is_scale: The size scale of the "MY NAME IS" string. Defaults to 1.
        :param my_name_is_string: The second string of the badge. Defaults to "MY NAME IS".
        :param name_font: The font for the name string. Defaults to ``terminalio.FONT``.
        :param name_scale: The size scale of the name string. Defaults to 1.
        :param name_string: The third string of the badge - change to be your name. Defaults to
                            "Blinka".

        """
        hello_group = self._create_label_group(text=hello_string,
                                               font=hello_font,
                                               scale=hello_scale,
                                               height_adjustment=0.117,
                                               color=background_text_color)

        my_name_is_group = self._create_label_group(text=my_name_is_string,
                                                    font=my_name_is_font,
                                                    scale=my_name_is_scale,
                                                    height_adjustment=0.28,
                                                    color=background_text_color)

        name_group = self._create_label_group(text=name_string,
                                              font=name_font,
                                              scale=name_scale,
                                              height_adjustment=0.65,
                                              color=foreground_text_color)

        group = displayio.Group()
        group.append(self._badge_background(background_color=background_color,
                                            rectangle_color=foreground_color))
        group.append(hello_group)
        group.append(my_name_is_group)
        group.append(name_group)
        self.display.show(group)



    def show_terminal(self):
        """Revert to terminalio screen.

        """
        self.display.show(None)

    @staticmethod
    def bitmap_qr(matrix):
        """The QR code bitmap."""
        border_pixels = 2
        bitmap = displayio.Bitmap(matrix.width + 2 * border_pixels,
                                  matrix.height + 2 * border_pixels, 2)
        for y in range(matrix.height):
            for x in range(matrix.width):
                if matrix[x, y]:
                    bitmap[x + border_pixels, y + border_pixels] = 1
                else:
                    bitmap[x + border_pixels, y + border_pixels] = 0
        return bitmap

    def show_qr_code(self, *, data="https://circuitpython.org"):
        """Generate a QR code and display it for ``dwell`` seconds.

        :param string data: A string of data for the QR code

        """
        qr_code = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
        qr_code.add_data(bytearray(data))
        qr_code.make()
        qr_bitmap = self.bitmap_qr(qr_code.matrix)
        palette = displayio.Palette(2)
        palette[0] = 0xFFFFFF
        palette[1] = 0x000000
        qr_code_scale = min(self.display.width // qr_bitmap.width,
                            self.display.height // qr_bitmap.height)
        qr_position_x = int(((self.display.width / qr_code_scale) - qr_bitmap.width) / 2)
        qr_position_y = int(((self.display.height / qr_code_scale) - qr_bitmap.height) / 2)
        qr_img = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=qr_position_x,
                                    y=qr_position_y)
        qr_code = displayio.Group(scale=qr_code_scale)
        qr_code.append(qr_img)
        self.display.show(qr_code)

    @staticmethod
    def _sine_sample(length):
        tone_volume = (2 ** 15) - 1
        shift = 2 ** 15
        for i in range(length):
            yield int(tone_volume * math.sin(2*math.pi*(i / length)) + shift)

    def _generate_sample(self, length=100):
        if self._sample is not None:
            return
        self._sine_wave = array.array("H", PyBadgerBase._sine_sample(length))
        self._sample = self._audio_out(board.SPEAKER)  # pylint: disable=not-callable
        self._sine_wave_sample = audiocore.RawSample(self._sine_wave)

    def _enable_speaker(self, enable):
        if not hasattr(board, "SPEAKER_ENABLE"):
            return
        self._speaker_enable.value = enable

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
        self._enable_speaker(enable=True)
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
        self._enable_speaker(enable=False)

    def play_file(self, file_name):
        """ Play a .wav file using the onboard speaker.

        :param file_name: The name of your .wav file in quotation marks including .wav

        """
        # Play a specified file.
        self.stop_tone()
        self._enable_speaker(enable=True)
        with self._audio_out(board.SPEAKER) as audio:  # pylint: disable=not-callable
            wavefile = audiocore.WaveFile(open(file_name, "rb"))
            audio.play(wavefile)
            while audio.playing:
                pass
        self._enable_speaker(enable=True)
