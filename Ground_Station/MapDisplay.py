#from offline_folium import offline
import folium





class LiveKmlRoute:
    def _init_(self, filename):
        import simplekml
        self.kml = simplekml.Kml()
        self.filename = filename
        self._coords = []
        self._linestring = self.kml.newlinestring(name="route")
        # optional: show altitude
        self._linestring.altitudemode = simplekml.AltitudeMode.absolute
        
        self._linestring.style.linestyle.color = simplekml.Color.red
        self._linestring.style.linestyle.width = 4

    def add_point(self, lat, lon, alt=None):
        # simplekml expects (lon, lat[, alt])
        if alt is None:
            self._coords.append((lon, lat))
        else:
            self._coords.append((lon, lat, alt))
        self._linestring.coords = self._coords

    def save(self):
        self.kml.save(self.filename)

class LiveMapDisplay:
    def update(self, lat, lon):
        map = folium.Map(location=[lat, lon], zoom_start=18)
        tooltop_text = f"Lat: {lat:.5f}, Lon: {lon:.5f}"

        custom_tooltip = folium.Tooltip(
        tooltop_text,
        style="background-color: white; color: black; font-family: Arial; font-size: 16px; padding: 5px;")

        positionPopup=folium.Popup(tooltop_text, max_width=300,min_width=300)

        folium.Marker([lat, lon], tooltip=custom_tooltip).add_to(map)
        map.save("FF.html")