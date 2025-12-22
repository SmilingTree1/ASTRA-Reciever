import serial
import time

# --- Configuration ---
SERIAL_PORT = "/dev/tty.usbserial-A5069RR4"
#/dev/tty.usbserial-A5069RR4 for lora rylr999
BAUDRATE = 115200
RECEIVER_ADDRESS = 2
NETWORK_ID = 18 
BAND = 915000000
PARAMETER = "10,8,1,12"
# --- End Configuration ---


def send_cmd(ser, cmd):
    """Sends an AT command to the LoRa module and prints its response."""
    ser.write((cmd + '\r\n').encode('utf-8'))
    # time.sleep(1)
    print(ser.readline())
    raw = ser.readline().decode('utf-8', 'ignore').strip()
    print(f"Response: {raw}")


def parse_and_print_received_data(data):
    """Parses and prints +RCV messages."""
    try:
        parts = data.split(',')
        if len(parts) > 2:
            msg = parts[2]
            print(f"\nMessage received: {msg}")

            # Attempt to parse coordinates
            payloadData = msg.split('#')
            if len(payloadData) >= 6:
                packet_id = payloadData[0]
                pressure = payloadData[1]
                alt = payloadData[2]
                lat = payloadData[3]
                lon = payloadData[4]
                time_UTC =  payloadData[5]

                
                print(f"Parsed: ID={packet_id}, Pressure={pressure}, Alt={alt}, Lat={lat}, Lon={lon}, time={time_UTC}")
            else:
                print("Could not parse coordinates — data format mismatch.")
    except Exception as e:
        print(f"Error parsing data: {e} | Raw: {data}")
 

# --- Initialize Serial Connection ---
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
if ser and ser.is_open:
    print(f"Connected to LoRa module on {SERIAL_PORT}")

# --- Setup LoRa ---
print("\n--- Initializing Receiver Module (Address 2) ---")
send_cmd(ser, "AT")
send_cmd(ser, "AT+RESET")
# time.sleep(1)
send_cmd(ser, f"AT+ADDRESS={RECEIVER_ADDRESS}")
send_cmd(ser, f"AT+NETWORKID={NETWORK_ID}")
send_cmd(ser, f"AT+BAND={BAND}")
send_cmd(ser, f"AT+PARAMETER={PARAMETER}")   

print("\nModule initialized. Waiting for packets...\n")

# --- Main Loop ---
while True:
    if ser.in_waiting:
        raw = ser.readline().decode('utf-8', 'ignore').strip()
        if raw:
            print("read data")
            print(raw)
            print("read data done")
            if raw.startswith("+RCV="):
                parse_and_print_received_data(raw)
                # print("Data received: " + raw)
            else:
                print(f"LoRa Response: {raw}")

