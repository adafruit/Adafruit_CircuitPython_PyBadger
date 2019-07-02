from adafruit_pybadger import PyBadger

pybadger = PyBadger()

while True:
    pybadger.show_badge(hello_scale=2, my_name_is_scale=2, name_scale=3)
    pybadger.auto_dim_display()

    if pybadger.button.a:
        pybadger.business_card(image_name="Blinka.bmp")
    elif pybadger.button.b:
        print("b B")
    elif pybadger.button.start:
        print("b start")
    elif pybadger.button.select:
        pybadger.qr_code()
