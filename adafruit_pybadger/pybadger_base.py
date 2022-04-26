# SPDX-FileCopyrightText: 2019-2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

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
  https://circuitpython.org/downloads

"""

import time
import array
import math
import board
from micropython import const
import digitalio
from adafruit_bitmap_font import bitmap_font
import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
import terminalio
import adafruit_miniqr

AUDIO_ENABLED = False
try:
    import audiocore

    AUDIO_ENABLED = True
except ImportError:
    try:
        import audioio as audiocore

        AUDIO_ENABLED = True
    except ImportError:
        # Allow to work with no audio
        pass

try:
    from typing import Union, Tuple, Optional, Generator
    from adafruit_bitmap_font.bdf import BDF  # pylint: disable=ungrouped-imports
    from adafruit_bitmap_font.pcf import PCF  # pylint: disable=ungrouped-imports
    from fontio import BuiltinFont
    from keypad import Keys, ShiftRegisterKeys
    from neopixel import NeoPixel
    from adafruit_lsm6ds.lsm6ds33 import LSM6DS33
    from adafruit_lis3dh import LIS3DH_I2C
except ImportError:
    pass


__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"


def load_font(fontname: str, text: str) -> Union[BDF, PCF]:
    """Load a font and glyphs in the text string

    :param str fontname: The full path to the font file.
    :param str text: The text containing the glyphs we want to load.

    """
    font = bitmap_font.load_font(fontname)
    font.load_glyphs(text.encode("utf-8"))
    return font


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
    DEEP_PURPLE = (100, 0, 150)
    PYTHON_YELLOW = (255, 213, 69)
    PYTHON_BLUE = (55, 112, 159)
    BLINKA_PURPLE = (102, 45, 145)
    BLINKA_PINK = (231, 33, 138)

    # Button Constants
    BUTTON_LEFT = const(128)
    BUTTON_UP = const(64)
    BUTTON_DOWN = const(32)
    BUTTON_RIGHT = const(16)
    BUTTON_SELECT = const(8)
    BUTTON_START = const(4)
    BUTTON_A = const(2)
    BUTTON_B = const(1)

    def __init__(self) -> None:
        self._light_sensor = None
        self._accelerometer = None
        self._label = label
        self._y_position = 1
        self._background_group = None
        self._background_image_filename = None
        self._lines = []
        self._created_background = False

        # Display
        if "DISPLAY" in dir(board):
            self.display = board.DISPLAY
            self._display_brightness = 1.0

        self._neopixels = None

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

    def _create_badge_background(self) -> None:
        self._created_background = True

        if self._background_group is None:
            self._background_group = displayio.Group()

        self.display.show(self._background_group)

        if self._background_image_filename:
            with open(self._background_image_filename, "rb") as file_handle:
                on_disk_bitmap = displayio.OnDiskBitmap(file_handle)
                background_image = displayio.TileGrid(
                    on_disk_bitmap,
                    pixel_shader=getattr(
                        on_disk_bitmap, "pixel_shader", displayio.ColorConverter()
                    ),
                    # TODO: Once CP6 is no longer supported, replace the above line with below
                    # pixel_shader=on_disk_background.pixel_shader,
                )
                self._background_group.append(background_image)
                for image_label in self._lines:
                    self._background_group.append(image_label)

                self.display.refresh()
        else:
            for background_label in self._lines:
                self._background_group.append(background_label)

    def badge_background(
        self,
        background_color: Tuple[int, int, int] = RED,
        rectangle_color: Tuple[int, int, int] = WHITE,
        rectangle_drop: float = 0.4,
        rectangle_height: float = 0.5,
    ) -> displayio.Group:
        """Create a customisable badge background made up of a background color with a rectangle
        color block over it. Defaults are for ``show_badge``.

        :param tuple background_color: The color to fill the entire screen as a background, as
                                     RGB values.
        :param tuple rectangle_color: The color of a rectangle that displays over the background,
                                     as RGB values.
        :param float rectangle_drop: The distance from the top of the display to begin displaying
                                     the rectangle. Float represents a percentage of the display,
                                     e.g. 0.4 = 40% of the display. Defaults to ``0.4``.
        :param float rectangle_height: The height of the rectangle. Float represents a percentage
                                       of the display, e.g. 0.5 = 50% of the display. Defaults to
                                       ``0.5``.

        .. code-block:: python

            from adafruit_pybadger import pybadger

            pybadger.badge_background(background_color=pybadger.WHITE,
                                      rectangle_color=pybadger.PURPLE,
                                      rectangle_drop=0.2, rectangle_height=0.6)

            while True:
                pybadger.show_custom_badge()
        """
        self._background_group = self._badge_background(
            background_color, rectangle_color, rectangle_drop, rectangle_height
        )
        return self._background_group

    def _badge_background(
        self,
        background_color: Tuple[int, int, int] = RED,
        rectangle_color: Tuple[int, int, int] = WHITE,
        rectangle_drop: float = 0.4,
        rectangle_height: float = 0.5,
    ) -> displayio.Group:
        """Populate the background color with a rectangle color block over it as the background for
        a name badge."""
        background_group = displayio.Group()
        color_bitmap = displayio.Bitmap(self.display.width, self.display.height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = background_color

        bg_sprite = displayio.TileGrid(
            color_bitmap, pixel_shader=color_palette, x=0, y=0
        )
        background_group.append(bg_sprite)

        rectangle = Rect(
            0,
            (int(self.display.height * rectangle_drop)),
            self.display.width,
            (int(self.display.height * rectangle_height)),
            fill=rectangle_color,
        )
        background_group.append(rectangle)
        return background_group

    def image_background(self, image_name: Optional[str] = None) -> None:
        """Create a bitmap image background.

        :param str image_name: The name of the bitmap image as a string including ``.bmp``, e.g.
                               ``"Blinka.bmp"``. Image file name is required.

        .. code-block:: python

            from adafruit_pybadger import pybadger

            pybadger.image_background("Blinka.bmp")

            while True:
                pybadger.show_custom_badge()
        """
        self._background_image_filename = image_name

    # pylint: disable=too-many-arguments
    def badge_line(
        self,
        text: str = " ",
        color: Tuple[int, int, int] = BLACK,
        scale: int = 1,
        font: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        left_justify: bool = False,
        padding_above: float = 0,
    ) -> None:
        """Add a line of text to the display. Designed to work with ``badge_background`` for a
        color-block style badge, or with ``image_background`` for a badge with a background image.

        :param str text: The text to display. Defaults to displaying a blank line if no text is
                         provided.
        :param tuple color: The color of the line of text. Defaults to ``(0, 0, 0)``.
        :param int scale: The scale of the text. Must be an integer 1 or higher. Defaults to ``1``.
        :param font: The font used for displaying the text. Defaults to ``terminalio.FONT``.
        :param bool left_justify: Left-justify the line of text. Defaults to ``False`` which centers
                             the font on the display.
        :param int padding_above: Add padding above the displayed line of text. A ``padding_above``
                                  of ``1`` is equivalent to the height of one line of text, ``2``
                                  is equivalent to the height of two lines of text, etc. Defaults
                                  to ``0``.

        The following example is designed to work on CLUE. To adapt for PyBadge or PyGamer, change
        the ``scale`` and ``padding_above`` values to fit the text to the display. Examples for
        CLUE, and PyBadge and PyGamer are included in the examples folder in the library repo.

        .. code-block:: python

            from adafruit_pybadger import pybadger

            pybadger.badge_background(background_color=pybadger.WHITE,
                                      rectangle_color=pybadger.PURPLE,
                                      rectangle_drop=0.2, rectangle_height=0.6)

            pybadger.badge_line(text="@circuitpython", color=pybadger.BLINKA_PURPLE, scale=2,
                                padding_above=2)
            pybadger.badge_line(text="Blinka", color=pybadger.WHITE, scale=5,
                                padding_above=3)
            pybadger.badge_line(text="CircuitPython", color=pybadger.WHITE, scale=3,
                                padding_above=1)
            pybadger.badge_line(text="she/her", color=pybadger.BLINKA_PINK, scale=4,
                                padding_above=4)

            while True:
                pybadger.show_custom_badge()
        """
        if isinstance(font, str):
            font = load_font(font, text)

        text_label = self._label.Label(font=font, text=text, color=color, scale=scale)
        self._lines.append(text_label)

        _, _, width, height = text_label.bounding_box
        if not left_justify:
            text_label.x = (self.display.width // 2) - ((width * scale) // 2)
        else:
            text_label.x = 0

        trim_y = 0
        trim_padding = 0
        if font is terminalio.FONT:
            trim_y = 4 * scale
            trim_padding = round(4 * padding_above)

        if not padding_above:
            text_label.y = self._y_position + ((height // 2) * scale) - trim_y

            if font is terminalio.FONT:
                self._y_position += height * scale - trim_y
            else:
                self._y_position += height * scale + 4

        else:
            text_label.y = round(
                self._y_position
                + (((height // 2) * scale) - trim_y)
                + ((height * padding_above) - trim_padding)
            )

            if font is terminalio.FONT:
                self._y_position += (height * scale - trim_y) + round(
                    (height * padding_above) - trim_padding
                )
            else:
                self._y_position += height * scale + 4

    def show_custom_badge(self) -> None:
        """Call ``pybadger.show_custom_badge()`` to display the custom badge elements. If
        ``show_custom_badge()`` is not called, the custom badge elements will not be displayed.
        """
        if not self._created_background:
            self._create_badge_background()

        self.display.show(self._background_group)

    # pylint: disable=too-many-arguments
    def _create_label_group(
        self,
        text: str,
        font: Union[BuiltinFont, BDF, PCF],
        scale: int,
        height_adjustment: float,
        background_color: Optional[int] = None,
        color: int = 0xFFFFFF,
        width_adjustment: float = 2,
        line_spacing: float = 0.75,
    ) -> displayio.Group:
        """Create a label group with the given text, font, and spacing."""
        # If the given font is a string, treat it as a file path and try to load it
        if isinstance(font, str):
            font = load_font(font, text)

        create_label_group = displayio.Group(scale=scale)
        create_label = self._label.Label(
            font,
            text=text,
            line_spacing=line_spacing,
            background_color=background_color,
        )
        _, _, width, _ = create_label.bounding_box
        create_label.x = (self.display.width // (width_adjustment * scale)) - width // 2
        create_label.y = int(self.display.height * (height_adjustment / scale))
        create_label.color = color
        create_label_group.append(create_label)
        return create_label_group

    def _check_for_movement(self, movement_threshold: int = 10) -> bool:
        """Checks to see if board is moving. Used to auto-dim display when not moving."""
        current_accelerometer = self.acceleration
        if self._last_accelerometer is None:
            self._last_accelerometer = current_accelerometer
            return False
        acceleration_delta = sum(
            [
                abs(self._last_accelerometer[n] - current_accelerometer[n])
                for n in range(3)
            ]
        )
        self._last_accelerometer = current_accelerometer
        return acceleration_delta > movement_threshold

    def auto_dim_display(self, delay: float = 5.0, movement_threshold: int = 10):
        """Auto-dim the display when board is not moving.

        :param float delay: Time in seconds before display auto-dims after movement has ceased.
        :param int movement_threshold: Threshold required for movement to be considered stopped.
                                       Change to increase or decrease sensitivity.

        .. code-block:: python

            from adafruit_pybadger import pybadger

            while True:
                pybadger.auto_dim_display(delay=10)
        """
        if not self._check_for_movement(movement_threshold=movement_threshold):
            current_time = time.monotonic()
            if current_time - self._start_time > delay:
                self.display.brightness = 0.1
                self._start_time = current_time
        else:
            self.display.brightness = self._display_brightness

    @property
    def pixels(self) -> NeoPixel:
        """Sequence like object representing the NeoPixels on the board."""
        return self._neopixels

    @property
    def light(self) -> bool:
        """Light sensor data."""
        return self._light_sensor.value

    @property
    def acceleration(self) -> Union[LSM6DS33, LIS3DH_I2C]:
        """Accelerometer data, +/- 2G sensitivity."""
        return (
            self._accelerometer.acceleration
            if self._accelerometer is not None
            else None
        )

    @property
    def brightness(self) -> float:
        """Display brightness. Must be a value between ``0`` and ``1``."""
        return self.display.brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        self._display_brightness = value
        self.display.brightness = value

    # pylint: disable=too-many-locals
    def show_business_card(
        self,
        *,
        image_name: Optional[str] = None,
        name_string: Optional[str] = None,
        name_scale: int = 1,
        name_font: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        font_color: int = 0xFFFFFF,
        font_background_color: Optional[int] = None,
        email_string_one: Optional[str] = None,
        email_scale_one: int = 1,
        email_font_one: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        email_string_two: Optional[str] = None,
        email_scale_two: int = 1,
        email_font_two: Union[BuiltinFont, BDF, PCF] = terminalio.FONT
    ) -> None:
        """Display a bitmap image and a text string, such as a personal image and email address.

        :param str image_name: REQUIRED. The name of the bitmap image including .bmp, e.g.
                               ``"Blinka.bmp"``.
        :param str name_string: A name string to display along the bottom of the display, e.g.
                                 ``"Blinka"``.
        :param int name_scale: The scale of ``name_string``. Defaults to 1.
        :param name_font: The font for the name string. Defaults to ``terminalio.FONT``.
        :type name_font: ~BuiltinFont|~BDF|~PCF
        :param int font_background_color: The color of the font background, default is None
                                            (transparent)
        :param int font_color: The font color, default is white
        :param str email_string_one: A string to display along the bottom of the display, e.g.
                                 ``"blinka@adafruit.com"``.
        :param int email_scale_one: The scale of ``email_string_one``. Defaults to 1.
        :param email_font_one: The font for the first email string. Defaults to ``terminalio.FONT``.
        :type email_font_one: ~BuiltinFont|~BDF|~PCF
        :param str email_string_two: A second string to display along the bottom of the display.
                                     Use if your email address is longer than one line or to add
                                     more space between the name and email address,
                                     e.g. (blinka@) ``"adafruit.com"``.
        :param int email_scale_two: The scale of ``email_string_two``. Defaults to 1.
        :param email_font_two: The font for the second email string. Defaults to
                               ``terminalio.FONT``.
        :type email_font_two: ~BuiltinFont|~BDF|~PCF

        .. code-block:: python

            from adafruit_pybadger import pybadger

            while True:
                pybadger.show_business_card(image_name="Blinka.bmp", name_string="Blinka",
                                            name_scale=2, email_string_one="blinka@",
                                            email_string_two="adafruit.com")

        """
        business_card_label_groups = []
        if name_string:
            name_group = self._create_label_group(
                text=name_string,
                font=name_font,
                color=font_color,
                scale=name_scale,
                height_adjustment=0.73,
                background_color=font_background_color,
            )
            business_card_label_groups.append(name_group)
        if email_string_one:
            email_one_group = self._create_label_group(
                text=email_string_one,
                font=email_font_one,
                color=font_color,
                scale=email_scale_one,
                height_adjustment=0.84,
                background_color=font_background_color,
            )
            business_card_label_groups.append(email_one_group)
        if email_string_two:
            email_two_group = self._create_label_group(
                text=email_string_two,
                font=email_font_two,
                color=font_color,
                scale=email_scale_two,
                height_adjustment=0.91,
                background_color=font_background_color,
            )
            business_card_label_groups.append(email_two_group)

        business_card_splash = displayio.Group()
        self.display.show(business_card_splash)
        with open(image_name, "rb") as file_name:
            on_disk_bitmap = displayio.OnDiskBitmap(file_name)
            face_image = displayio.TileGrid(
                on_disk_bitmap,
                pixel_shader=getattr(
                    on_disk_bitmap, "pixel_shader", displayio.ColorConverter()
                ),
                # TODO: Once CP6 is no longer supported, replace the above line with below
                # pixel_shader=on_disk_bitmap.pixel_shader,
            )
            business_card_splash.append(face_image)
            for group in business_card_label_groups:
                business_card_splash.append(group)

            self.display.refresh()

    # pylint: disable=too-many-locals
    def show_badge(
        self,
        *,
        background_color: Tuple[int, int, int] = RED,
        foreground_color: Tuple[int, int, int] = WHITE,
        background_text_color: Tuple[int, int, int] = WHITE,
        foreground_text_color: Tuple[int, int, int] = BLACK,
        hello_font: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        hello_scale: int = 1,
        hello_string: str = "HELLO",
        my_name_is_font: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        my_name_is_scale: int = 1,
        my_name_is_string: str = "MY NAME IS",
        name_font: Union[BuiltinFont, BDF, PCF] = terminalio.FONT,
        name_scale: int = 1,
        name_string: str = "Blinka"
    ) -> None:
        """Create a "Hello My Name is"-style badge.

        :param tuple background_color: The color of the background. Defaults to ``(255, 0, 0)``.
        :param tuple foreground_color: The color of the foreground rectangle. Defaults to
                                 ``(255, 255, 255)``.
        :param tuple background_text_color: The color of the "HELLO MY NAME IS" text. Defaults to
                                      ``(255, 255, 255)``.
        :param tuple foreground_text_color: The color of the name text. Defaults to ``(0, 0, 0)``.
        :param hello_font: The font for the "HELLO" string. Defaults to ``terminalio.FONT``.
        :type hello_font: ~BuiltinFont|~BDF|~PCF
        :param int hello_scale: The size scale of the "HELLO" string. Defaults to 1.
        :param str hello_string: The first string of the badge. Defaults to "HELLO".
        :param my_name_is_font: The font for the "MY NAME IS" string. Defaults to
                                ``terminalio.FONT``.
        :type my_name_is_font: ~BuiltinFont|~BDF|~PCF
        :param int my_name_is_scale: The size scale of the "MY NAME IS" string. Defaults to 1.
        :param str my_name_is_string: The second string of the badge. Defaults to "MY NAME IS".
        :param name_font: The font for the name string. Defaults to ``terminalio.FONT``.
        :type name_font: ~BuiltinFont|~BDF|~PCF
        :param int name_scale: The size scale of the name string. Defaults to 1.
        :param str name_string: The third string of the badge - change to be your name. Defaults to
                            "Blinka".

        .. code-block:: python

            from adafruit_pybadger import pybadger

            while True:
                pybadger.show_badge(name_string="Blinka", hello_scale=2, my_name_is_scale=2,
                                    name_scale=3)

        """
        hello_group = self._create_label_group(
            text=hello_string,
            font=hello_font,
            scale=hello_scale,
            height_adjustment=0.117,
            color=background_text_color,
        )

        my_name_is_group = self._create_label_group(
            text=my_name_is_string,
            font=my_name_is_font,
            scale=my_name_is_scale,
            height_adjustment=0.28,
            color=background_text_color,
        )

        name_group = self._create_label_group(
            text=name_string,
            font=name_font,
            scale=name_scale,
            height_adjustment=0.65,
            color=foreground_text_color,
        )

        group = displayio.Group()
        group.append(
            self._badge_background(
                background_color=background_color, rectangle_color=foreground_color
            )
        )
        group.append(hello_group)
        group.append(my_name_is_group)
        group.append(name_group)
        self.display.show(group)

    def show_terminal(self) -> None:
        """Revert to terminalio screen."""
        self.display.show(None)

    @staticmethod
    def bitmap_qr(matrix: adafruit_miniqr.QRBitMatrix) -> displayio.Bitmap:
        """The QR code bitmap."""
        border_pixels = 2
        bitmap = displayio.Bitmap(
            matrix.width + 2 * border_pixels, matrix.height + 2 * border_pixels, 2
        )
        for y in range(matrix.height):
            for x in range(matrix.width):
                if matrix[x, y]:
                    bitmap[x + border_pixels, y + border_pixels] = 1
                else:
                    bitmap[x + border_pixels, y + border_pixels] = 0
        return bitmap

    def show_qr_code(self, data: str = "https://circuitpython.org") -> None:
        """Generate a QR code.

        :param str data: A string of data for the QR code

        .. code-block:: python

            from adafruit_pybadger import pybadger

            while True:
                pybadger.show_qr_code("https://adafruit.com")

        """
        qr_code = adafruit_miniqr.QRCode(qr_type=3, error_correct=adafruit_miniqr.L)
        qr_code.add_data(bytearray(data))
        qr_code.make()
        qr_bitmap = self.bitmap_qr(qr_code.matrix)
        palette = displayio.Palette(2)
        palette[0] = 0xFFFFFF
        palette[1] = 0x000000
        qr_code_scale = min(
            self.display.width // qr_bitmap.width,
            self.display.height // qr_bitmap.height,
        )
        qr_position_x = int(
            ((self.display.width / qr_code_scale) - qr_bitmap.width) / 2
        )
        qr_position_y = int(
            ((self.display.height / qr_code_scale) - qr_bitmap.height) / 2
        )
        qr_img = displayio.TileGrid(
            qr_bitmap, pixel_shader=palette, x=qr_position_x, y=qr_position_y
        )
        qr_code = displayio.Group(scale=qr_code_scale)
        qr_code.append(qr_img)
        self.display.show(qr_code)

    @staticmethod
    def _sine_sample(length: int) -> Generator[int, None, None]:
        tone_volume = (2**15) - 1
        shift = 2**15
        for i in range(length):
            yield int(tone_volume * math.sin(2 * math.pi * (i / length)) + shift)

    def _generate_sample(self, length: int = 100) -> None:
        if AUDIO_ENABLED:
            if self._sample is not None:
                return
            self._sine_wave = array.array("H", PyBadgerBase._sine_sample(length))
            # pylint: disable=not-callable
            self._sample = self._audio_out(
                board.SPEAKER
            )  # pylint: disable=not-callable
            self._sine_wave_sample = audiocore.RawSample(self._sine_wave)
        else:
            print("Required audio modules were missing")

    def _enable_speaker(self, enable: bool) -> None:
        if not hasattr(board, "SPEAKER_ENABLE"):
            return
        self._speaker_enable.value = enable

    def play_tone(self, frequency: int, duration: float) -> None:
        """Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone.

        :param int frequency: The frequency of the tone in Hz
        :param float duration: The duration of the tone in seconds

        """
        # Play a tone of the specified frequency (hz).
        self.start_tone(frequency)
        time.sleep(duration)
        self.stop_tone()

    def start_tone(self, frequency: int) -> None:
        """Produce a tone using the speaker. Try changing frequency to change
        the pitch of the tone. Use ``stop_tone`` to stop the tone.

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

    def stop_tone(self) -> None:
        """Use with ``start_tone`` to stop the tone produced."""
        # Stop playing any tones.
        if self._sample is not None and self._sample.playing:
            self._sample.stop()
            self._sample.deinit()
            self._sample = None
        self._enable_speaker(enable=False)

    def play_file(self, file_name: str) -> None:
        """Play a .wav file using the onboard speaker.

        :param str file_name: The name of your .wav file in quotation marks including .wav

        """
        # Play a specified file.
        self.stop_tone()
        self._enable_speaker(enable=True)
        with self._audio_out(board.SPEAKER) as audio:  # pylint: disable=not-callable
            wavefile = audiocore.WaveFile(
                open(file_name, "rb")  # pylint: disable=consider-using-with
            )
            audio.play(wavefile)
            while audio.playing:
                pass
        self._enable_speaker(enable=True)


class KeyStates:
    """Convert `keypad.Event` information from the given `keypad` scanner into key-pressed state.

    :param scanner: a `keypad` scanner, such as `keypad.Keys`
    """

    def __init__(self, scanner: Union[Keys, ShiftRegisterKeys]) -> None:
        self._scanner = scanner
        self._pressed = [False] * self._scanner.key_count
        self.update()

    def update(self) -> None:
        """Update key information based on pending scanner events."""

        # If the event queue overflowed, discard any pending events,
        # and assume all keys are now released.
        if self._scanner.events.overflowed:
            self._scanner.events.clear()
            self._scanner.reset()
            self._pressed = [False] * self._scanner.key_count

        self._was_pressed = self._pressed.copy()

        while True:
            event = self._scanner.events.get()
            if not event:
                # Event queue is now empty.
                break
            self._pressed[event.key_number] = event.pressed
            if event.pressed:
                self._was_pressed[event.key_number] = True

    def was_pressed(self, key_number: int) -> bool:
        """True if key was down at any time since the last `update()`,
        even if it was later released.
        """
        return self._was_pressed[key_number]

    def pressed(self, key_number: int) -> bool:
        """True if key is currently pressed, as of the last `update()`."""
        return self._pressed[key_number]
