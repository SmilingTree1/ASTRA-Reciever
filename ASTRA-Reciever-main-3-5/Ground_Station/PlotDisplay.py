#HELLO
import matplotlib
import time
matplotlib.use('Qt5Agg')  # use the Qt5Agg backend
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime, date, timedelta
import matplotlib.dates as mdates
import pytz
from MapDisplay import LiveKmlRoute

pressure_data = []
altitude_data = []
time_data = []
dataFile = open("receiverLog.txt", "a", encoding="utf-8")
dataFile.write("\n")

TIMEZONE = "US/Pacific"

startTime = time.time()

class TwoSubplotCanvas(FigureCanvas):


    def __init__(self, dataQueue, mapQueue):
        self.dataQueue = dataQueue
        self.mapQueue = mapQueue

        fig = Figure(figsize=(5, 4))
        super().__init__(fig)

        self.ax1 = fig.add_subplot(211)
        self.ax2 = fig.add_subplot(212)
    
        self.x1, self.y1 = [], []
        self.x2, self.y2 = [], []

        self.line1, = self.ax1.plot([], [])
        self.line2, = self.ax2.plot([], [])

        self.ax1.set_title("Altitude", color = "green")
        self.ax1.set_xlabel("Time (s)", color = "green")
        self.ax1.set_ylabel("Altitude (m)", color = "green")
        self.ax1.grid(True, alpha=0.3)


        self.ax2.set_title("Atmospheric Pressure", color = "red")
        self.ax2.set_xlabel("Time (s)", color = "red")
        self.ax2.set_ylabel("Pressure (hPa)", color = "red")
        self.ax2.grid(True, alpha=0.3)

        self.ax1.xaxis_date()
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        self.ax2.xaxis_date()
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        self.line1.set_color('green') 
        self.line2.set_color('red')


        dataFile.write("-----------------------Receiver Start-----------------------\n")
        dataFile.flush()

        # KML route for Google Earth visualization to b added later
        self.LiveKmlRoute = LiveKmlRoute("route.kml")

        self.last_datetime = None
        self.lastPackageID = None


    def update_plot(self):
               # ensure axis uses a time formatter
        # self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        # self.ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        while not self.dataQueue.empty():
            data = self.dataQueue.get()
            line = data.rstrip("\r\n") + "\n"
            dataFile.write(line)
            #dataFile.write(f"{packageID},{pressure},{alt},{lat},{lon}, {timeUTCString}\n")
            #dataFile.write(f"{packageID},{pressure},{alt},{lat},{lon}, {timeUTCString}\n")
            dataFile.flush()

            payloadData = data.split("#")
            
            # Validation need to be improved, istead of ignoring sample fully when GPS unlocks in between
            # try to estimate time from last good GPS data sample, if packet id is continuous 
            # Example packet 10 has good GPS, 11 lost GPS, time for 11 can be estimated from 10
            gpsLocked = True
            if len(payloadData) < 5:
                print(f"Invalid data format: {data}")
                continue
            elif len(payloadData) < 8:
                print(f"GPS data missing: {data}")
                gpsLocked = False
            
            try:
                packageID = int(payloadData[1])
                pressure = float(payloadData[2])
                alt = float(payloadData[3])

                if gpsLocked:
                    lat = float(payloadData[4])
                    lon = float(payloadData[5])
                    timeUTCString = (payloadData[6]).strip()
                    dateString = (payloadData[7]).strip("/")

                    #timeUTCString = time.time() - startTime
                    print("ID: ", packageID, " Pressure: ", pressure, " Altitude: ", alt, " Latitude: ", lat, " Longitude: ", lon, " Time: ", timeUTCString)

            except Exception:
                print("data format mismatch")
                continue

            try:


                if gpsLocked:
                # parse time and date from payload
                    parsedTime = datetime.strptime(timeUTCString, "%H:%M:%S.%f").time()
                    # payload date is provided as day/month/year (e.g. "31/12/2025")
                    parsedDate = datetime.strptime(dateString, "%d/%m/%Y").date()

                    # combine into an aware UTC datetime (assume payload time is UTC)
                    combined_utc = datetime.combine(parsedDate, parsedTime).replace(tzinfo=pytz.UTC)

                    if self.last_datetime is not None and (combined_utc < self.last_datetime):
                        print("Time went backwards, skipping sample")
                        continue 

                    self.last_datetime = combined_utc
                    self.lastPackageID = packageID

                else:
                    if self.last_datetime is not None:
                        # estimate time based on last good GPS sample and package ID difference
                        if packageID < self.lastPackageID:
                            continue
                        
                        print("Estimating time for GPS unlocked sample")

                        
                        id_diff = packageID - self.lastPackageID

                        time_estimate = self.last_datetime + timedelta(seconds=id_diff * 2)  # assuming 3 second between samples
                        combined_utc = time_estimate
                        self.last_datetime = combined_utc
                        self.lastPackageID = packageID
                        #print("ESTIMATED TIME:  ID: ", packageID, " Pressure: ", pressure, " Altitude: ", alt, " Time: ", timeUTCString)
                        dataFile.write(f"ID: {packageID}, Pressure: {pressure}, Altitude: {alt}, Time: {combined_utc}\n")
                        dataFile.flush()
                    else:
                        print("No previous GPS data to estimate time, skipping sample")
                        continue

                    
                # convert to user-configurable local timezone
                tz = pytz.timezone(TIMEZONE)
                combined_datetime = combined_utc.astimezone(tz)

                # matplotlib.dates expects naive datetimes in the displayed timezone
                xnum = mdates.date2num(combined_datetime.replace(tzinfo=None))

                # `combined_datetime` is a timezone-aware datetime you can use elsewhere
                # `combined_utc` is the UTC version if you need it

            except ValueError:
                # if parsing fails, skip this sample
                print("Time format mismatch")
                continue
            
                        
            global pressure_data, altitude_data, time_data

            time_data.append(xnum)
            time_data= time_data[-1200:]        

            altitude_data.append(alt)
            altitude_data = altitude_data[-1200:]

            min_time = min(time_data)
            max_time= max(time_data)
            time_range = max_time - min_time if max_time != min_time else 1.0 / 86400.0
            pad = time_range * 0.1
            self.ax1.set_xlim(min_time - pad, max_time + pad)
            self.ax2.set_xlim(min_time - pad, max_time + pad)
            #self.ax1.set_xlim(min_time - timea_range * 0.1, max_time + min_time * 0.1)
            #self.ax2.set_xlim(min_time - timea_range * 0.1, max_time + min_time * 0.1)

            min_alt = min(altitude_data)
            max_alt = max(altitude_data)
            alt_range = max_alt - min_alt if max_alt != min_alt else 1.0
            self.ax1.set_ylim(min_alt - alt_range * 0.1, max_alt + alt_range * 0.1)
            # self.ax1.set_ylim(200, 400)
            self.line1.set_data(time_data, altitude_data)
                    

            pressure_data.append(pressure)
            pressure_data = pressure_data[-1200:]

            min_pressure = min(pressure_data)
            max_pressure = max(pressure_data)
            pressure_range = max_pressure - min_pressure if max_pressure != min_pressure else 1.0
            self.ax2.set_ylim(min_pressure - pressure_range * 0.1, max_pressure + pressure_range * 0.1)
           
            # self.ax2.set_ylim(100, 1200)
            self.line2.set_data(time_data, pressure_data)

            if gpsLocked:

                self.mapQueue.put((lat, lon))
                # KML route for Google Earth visualization to b added later
                self.LiveKmlRoute.add_point(lat, lon, alt)

        self.LiveKmlRoute.save()

        self.figure.autofmt_xdate()
        self.draw_idle()  
