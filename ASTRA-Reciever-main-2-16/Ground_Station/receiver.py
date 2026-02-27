import serial
import time

# --- Configuration ---
#SERIAL_PORT = "/dev/tty.usbserial-A5069RR4" for rlyr999
#SERIAL_PORT = "/dev/tty.usbserial-ABA29K0Q" for rlyr998
SERIAL_PORT = "/dev/tty.usbserial-A5069RR4"

BAUDRATE = 115200
RECEIVER_ADDRESS = 2
NETWORK_ID = 18 
BAND = 920000000
PARAMETER = "10,8,1,12"
SENDER_ID = "ST26"
# --- End Configuration ---


class LoraReceiver:

    def send_cmd(self, ser, cmd):
        ser.write((cmd + '\r\n').encode('utf-8'))
        # time.sleep(1)
        print(ser.readline())
        raw = ser.readline().decode('utf-8', 'ignore').strip()
        print(f"Response: {raw}")

    def __init__(self, dataQueue):
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        self.ser = ser
        self.dataQueue = dataQueue
        self.received_data = []
        if ser and ser.is_open:
            print(f"Connected to LoRa module on {SERIAL_PORT}")

        # --- Setup LoRa ---
        print("\n--- Initializing Receiver Module (Address 2) ---")
        self.send_cmd(ser, "AT")
        self.send_cmd(ser, "AT+RESET")
        # time.sleep(1)
        self.send_cmd(ser, f"AT+ADDRESS={RECEIVER_ADDRESS}")
        self.send_cmd(ser, f"AT+NETWORKID={NETWORK_ID}")
        self.send_cmd(ser, f"AT+BAND={BAND}")
        self.send_cmd(ser, f"AT+PARAMETER={PARAMETER}")   

        print("\nModule initialized. Waiting for packets...\n")

    

    def receive_data(self):
        while True:
            if self.ser.in_waiting:
                raw = self.ser.readline().decode('utf-8', 'ignore').strip()
                if raw:
                    print("read data")
                    print(raw)
                    print("read data done")
                    if raw.startswith("+RCV="):
                        #self.parse_and_print_received_data(raw)
                        print("Data received: " + raw)
                        self.parse_and_queue_received_data(raw)
                    else:
                        print(f"LoRa Response: {raw}")
            time.sleep(0.5)

    def parse_and_queue_received_data(self, data):
        try:
            parts = data.split(',')
            if len(parts) > 2:
                msg = parts[2]
                print(f"\nMessage received: {msg}")
                
                if msg.startswith(SENDER_ID):
                    self.dataQueue.put(msg)

        except Exception as e:
            print(f"Error parsing data: {e} | Raw: {data}")


    


