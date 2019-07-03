from adafruit_pybadger import PyBadger

pybadger = PyBadger()

while True:
    pybadger.show_badge(name_string="Blinka", hello_scale=2, my_name_is_scale=2, name_scale=3)
    pybadger.auto_dim_display()

    if pybadger.button.a:
        pybadger.show_business_card(image_name="Blinka.bmp", email_string="blinka@adafruit.com")
    elif pybadger.button.b:
        pybadger.show_qr_code(data="https://circuitpython.org")
    elif pybadger.button.start:
        print("Start button pressed!")
    elif pybadger.button.select:
        print("Select button pressed!")
