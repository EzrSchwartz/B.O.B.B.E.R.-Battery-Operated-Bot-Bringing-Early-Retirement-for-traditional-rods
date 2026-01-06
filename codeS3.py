import board
import busio
import time
import digitalio

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

class SBUSTransmitter:
    def __init__(self):
        self.uart = busio.UART(
            tx=board.IO17,
            rx=None,
            baudrate=100000,
            bits=8,
            parity=busio.UART.Parity.EVEN,
            stop=2,
            timeout=0
        )
        self.channels = [992] * 16
        print("SBUS initialized on GPIO17")
        
    def set_channel(self, channel, value):
        if 0 <= channel < 16:
            self.channels[channel] = max(172, min(1811, value))
    
    def _pack_channels(self):
        bit_string = 0
        for i, channel in enumerate(self.channels):
            bit_string |= (channel & 0x7FF) << (i * 11)
        
        packed = []
        for i in range(22):
            packed.append((bit_string >> (i * 8)) & 0xFF)
        
        return bytes(packed)
    
    def build_packet(self):
        packet = bytearray(25)
        packet[0] = 0x0F
        packet[1:23] = self._pack_channels()
        packet[23] = 0x00
        packet[24] = 0x00
        return bytes(packet)
    
    def send_packet(self):
        self.uart.write(self.build_packet())

print("=== ARM AND SPIN TEST ===")
print("Close INAV Configurator now!")
time.sleep(3)

sbus = SBUSTransmitter()

# Set all channels to safe positions
sbus.set_channel(0, 992)   # Roll center
sbus.set_channel(1, 992)   # Pitch center
sbus.set_channel(2, 172)   # Throttle MINIMUM (not 10!)
sbus.set_channel(3, 992)   # Yaw center
sbus.set_channel(4, 172)   # AUX1 low
sbus.set_channel(5, 172)   # AUX2 low

# Send neutral position for 2 seconds
print("Sending neutral position with LOW throttle...")
for _ in range(140):
    sbus.send_packet()
    led.value = not led.value if _ % 10 == 0 else led.value
    time.sleep(0.014)

# ARM: Throttle LOW + Yaw RIGHT
print("ARMING: Throttle LOW + Yaw RIGHT")
sbus.set_channel(2, 172)   # Throttle stays at MINIMUM
sbus.set_channel(3, 1811)  # Yaw RIGHT (not 2000!)
for _ in range(150):  # Hold for ~2 seconds
    sbus.send_packet()
    time.sleep(0.014)

# Return yaw to center
sbus.set_channel(3, 992)
print("ARMED - Should be beeping")
for _ in range(70):
    sbus.send_packet()
    time.sleep(0.014)

# Raise throttle slowly
print("Raising throttle to spin motors...")
for throttle in range(172, 1400, 5):
    sbus.set_channel(2, throttle)
    for _ in range(5):
        sbus.send_packet()
        time.sleep(0.014)

# Hold at 1400
print("MOTORS SPINNING at throttle 1400")
sbus.set_channel(2, 1400)
for _ in range(140):  # 2 seconds
    sbus.send_packet()
    led.value = not led.value if _ % 20 == 0 else led.value
    time.sleep(0.014)

# Lower throttle
print("Lowering throttle...")
for throttle in range(1400, 172, -5):
    sbus.set_channel(2, throttle)
    for _ in range(5):
        sbus.send_packet()
        time.sleep(0.014)

# Back to minimum
sbus.set_channel(2, 172)
print("Back to minimum throttle - beeping")
for _ in range(70):
    sbus.send_packet()
    time.sleep(0.014)

# DISARM: Throttle LOW + Yaw LEFT
print("DISARMING: Throttle LOW + Yaw LEFT")
sbus.set_channel(2, 172)
sbus.set_channel(3, 172)  # Yaw LEFT
for _ in range(150):
    sbus.send_packet()
    time.sleep(0.014)

# Neutral
sbus.set_channel(3, 992)
print("DISARMED - Test complete!")
for _ in range(70):
    sbus.send_packet()
    time.sleep(0.014)

led.value = False
print("Done!")
