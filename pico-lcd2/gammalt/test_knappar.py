# Felsökning för Pico 2 + Waveshare Pico-LCD-2.
# Kör med F5 i Thonny och titta i Skal-rutan.
#
# - Den lilla gröna lampan på Picon blinkar: då kör programmet.
# - Bakgrundsljuset på skärmen blinkar av/på varje halv sekund.
# - Varje knapptryckning skrivs ut i Skal-rutan.
#
# Knapparna sitter på skärmkortet. Syns knapptrycken i Thonny har
# Picon kontakt med skärmkortet.

from machine import Pin
import time

led = Pin("LED", Pin.OUT)
bl = Pin(13, Pin.OUT)

keys = {
    "KEY0 (GP15)": Pin(15, Pin.IN, Pin.PULL_UP),
    "KEY1 (GP17)": Pin(17, Pin.IN, Pin.PULL_UP),
    "KEY2 (GP2)": Pin(2, Pin.IN, Pin.PULL_UP),
    "KEY3 (GP3)": Pin(3, Pin.IN, Pin.PULL_UP),
}
last = {name: 1 for name in keys}

print("Testet kör. Tryck på knapparna på skärmkortet.")
print("Läge just nu (1 = släppt, 0 = nedtryckt):",
      {n: p.value() for n, p in keys.items()})

t = time.ticks_ms()
on = True
while True:
    for name, pin in keys.items():
        v = pin.value()
        if v != last[name]:
            print(name, "NEDTRYCKT" if v == 0 else "släppt")
            last[name] = v
    if time.ticks_diff(time.ticks_ms(), t) > 500:
        t = time.ticks_ms()
        on = not on
        led.value(on)
        bl.value(on)
    time.sleep_ms(10)
