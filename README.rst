Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-pybadger/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/pybadger/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_PyBadger/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_PyBadger/actions/
    :alt: Build Status

Badge-focused CircuitPython helper library for PyBadge, PyBadge LC, PyGamer and CLUE.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
=====================
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-pybadger/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-pybadger

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-pybadger

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-pybadger

Usage Example
=============

.. code-block:: python

    from adafruit_pybadger import pybadger

    pybadger.show_badge(name_string="Blinka", hello_scale=2, my_name_is_scale=2, name_scale=3)

    while True:
        pybadger.auto_dim_display(delay=10)
        if pybadger.button.a:
            pybadger.show_business_card(image_name="Blinka.bmp", name_string="Blinka", name_scale=2,
                                        email_string_one="blinka@", email_string_two="adafruit.com")
        elif pybadger.button.b:
            pybadger.show_qr_code(data="https://circuitpython.org")
        elif pybadger.button.start:
            pybadger.show_badge(name_string="Blinka", hello_scale=2, my_name_is_scale=2, name_scale=3)


Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_PyBadger/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
