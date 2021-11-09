# SPDX-FileCopyrightText: 2021 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT
class EventQueue:
    def __init__(self):
        self.overflowed = False

    def get(self):
        return None


class Keys:
    def __init__(self, pins, value_when_pressed, pull):
        self.key_count = len(pins)
        self.events = EventQueue()


class ShiftRegisterKeys:
    def __init__(
        self,
        *,
        clock,
        data,
        latch,
        value_to_latch=True,
        key_count,
        value_when_pressed,
        interval=0.020,
        max_events=64
    ):
        self.key_count = 123
        self.events = EventQueue()
