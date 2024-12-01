from pathlib import Path
from typing import List, Tuple
import vpype as vp
import geojson

import vsketch

try:
    ADDRESSES = (Path(__file__).parent / "addresses.txt").read_text().split("\n\n")
except FileNotFoundError:
    ADDRESSES = ["John Doe\n123 Main St\nAnytown, USA"]

try:
    HEADER = (Path(__file__).parent / "header.txt").read_text()
except FileNotFoundError:
    HEADER = "Myself\nMy Place\nMy town, USA"


try:
    MESSAGE = (Path(__file__).parent / "message.txt").read_text()
except FileNotFoundError:
    MESSAGE = """
Dear $FirstName$,

Please enjoy this postcard!

Best,
Me
"""


class PostcardSketch(vsketch.SketchClass):
    addr_id = vsketch.Param(0, 0, len(ADDRESSES) - 1)
    address_only = vsketch.Param(False)
    page_size = vsketch.Param(
        "8.5inx10in",
        choices=vp.PAGE_SIZES.keys(),
    )
    address_font_size = vsketch.Param(
        0.15,
    )
    address_line_spacing = vsketch.Param(1.2, decimals=1)
    address_y_offset = vsketch.Param(3, decimals=1)

    header_font_size = vsketch.Param(
        0.15,
    )
    header_line_spacing = vsketch.Param(1.1, decimals=1)

    message_font_size = vsketch.Param(
        0.2,
    )
    message_line_spacing = vsketch.Param(1.2, decimals=1)
    message_y_offset = vsketch.Param(1.5, decimals=1)

    postcard_margin = vsketch.Param(0.25)

    map_padding = vsketch.Param(0.1)

    @staticmethod
    def first_name(address: str) -> str:
        lines = address.splitlines()
        name_line = lines[0].split(" ")
        # deal with abbreviated first name
        if len(name_line) > 2 and len(name_line[1]) > len(name_line[0]):
            return name_line[1]
        else:
            return name_line[0]

    def draw_house(self, vsk: vsketch.Vsketch, x, y, size=0.1):
        half = size / 2
        roof_height = size * 0.6  # Proportional roof height

        # Draw the house base (square)
        vsk.polygon(
            [
                (x - half, y),  # Bottom-left
                (x + half, y),  # Bottom-right
                (x + half, y - size),  # Top-right
                (x - half, y - size),  # Top-left
                (x - half, y),
            ]
        )

        # Draw the roof (triangle)
        vsk.polygon(
            [
                (x - half, y - size),  # Left corner of the roof
                (x + half, y - size),  # Right corner of the roof
                (x, y - size - roof_height),  # Top of the roof
                (x - half, y - size),
            ]
        )

    def drawPostcard(self, vsk, x, y) -> None:
        address = ADDRESSES[self.addr_id]

        if not self.address_only:
            # vsk.line(4, 4, 4, 10)
            vsk.rect(x, y, 6, 4)
            vsk.rect(
                x + 6 - 0.87 - self.postcard_margin,
                y + self.postcard_margin,
                0.87,
                0.98,
            )
            vsk.line(
                x + 3.5, y + self.postcard_margin, x + 3.5, y + 4 - self.postcard_margin
            )
            vsk.text(
                HEADER,
                x + self.postcard_margin,
                y + self.postcard_margin + 0.1,
                width=7.0,
                size=self.header_font_size,
                line_spacing=self.header_line_spacing,
            )

            vsk.text(
                MESSAGE.replace("$FirstName$", self.first_name(address)),
                x + self.postcard_margin,
                y + self.message_y_offset,
                width=7.0,
                size=self.message_font_size,
                line_spacing=self.message_line_spacing,
                font="cursive",
            )

        vsk.text(
            address,
            x + 4,
            y + self.address_y_offset,
            width=5.8,
            size=self.address_font_size,
            line_spacing=self.address_line_spacing,
        )

    def normalize_coordinates(
        self, coords, box_width=6, box_height=4, padding=0.1, alignment="center"
    ):
        """
        Normalize GeoJSON coordinates to fit within a specified bounding box (width x height)
        with padding and alignment options.

        Parameters:
            coords (list): List of (lon, lat) tuples from GeoJSON.
            box_width (float): Width of the bounding box in inches.
            box_height (float): Height of the bounding box in inches.
            padding (float): Padding around the drawing inside the rectangle.
            alignment (str): Alignment of the drawing inside the rectangle.
                            Options: "center", "top-left", "top-right", "bottom-left", "bottom-right".

        Returns:
            list: List of normalized (x, y) tuples in inches.
        """
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]

        # Find min/max for scaling
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        # Calculate ranges and scaling factors
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat

        # Apply padding by reducing the effective width and height
        effective_width = box_width - 2 * padding
        effective_height = box_height - 2 * self.map_padding

        # Use the smaller scaling factor to maintain aspect ratio
        if lon_range > 0 and lat_range > 0:
            scale_lon = effective_width / lon_range
            scale_lat = effective_height / lat_range
            scale = min(scale_lon, scale_lat)
        else:
            scale = 1  # Prevent divide-by-zero if range is zero

        # Calculate drawing dimensions
        drawing_width = lon_range * scale
        drawing_height = lat_range * scale

        # Calculate offsets to apply alignment
        if alignment == "center":
            x_offset = self.map_padding + (effective_width - drawing_width) / 2
            y_offset = self.map_padding + (effective_height - drawing_height) / 2
        elif alignment == "top-left":
            x_offset = self.map_padding
            y_offset = self.map_padding
        elif alignment == "top-right":
            x_offset = self.map_padding + (effective_width - drawing_width)
            y_offset = self.map_padding
        elif alignment == "bottom-left":
            x_offset = self.map_padding
            y_offset = self.map_padding + (effective_height - drawing_height)
        elif alignment == "bottom-right":
            x_offset = self.map_padding + (effective_width - drawing_width)
            y_offset = padding + (effective_height - drawing_height)
        else:
            raise ValueError(f"Invalid alignment: {alignment}")

        # Normalize the coordinates
        normalized_coords = [
            (
                (lon - min_lon) * scale + x_offset,  # X (longitude)
                box_height
                - (
                    (lat - min_lat) * scale + y_offset
                ),  # Y (latitude, flipped for canvas orientation)
            )
            for lon, lat in coords
        ]

        return normalized_coords

    def drawGeoJson(
        self, vsk: vsketch.Vsketch, rect_size=(6, 4), xy_start=(0, 0)
    ) -> None:
        """
        Draw GeoJSON scaled to fit within a rectangle of specified size and offset to a start position.

        Parameters:
            vsk (vsketch.Vsketch): vsketch instance for drawing.
            rect_size (tuple): The size of the rectangle in inches (width, height).
            xy_start (tuple): The (x, y) position in inches where the top-left of the rectangle starts.
        """
        with open("testgeojson.geojson", "r") as f:
            data = geojson.load(f)

        coords = data["routes"][0]["geometry"]["coordinates"]

        # Unpack rectangle size and start position
        rect_width, rect_height = rect_size
        x_start, y_start = xy_start

        # Normalize coordinates to fit within the specified rectangle
        normalized_coords = self.normalize_coordinates(
            coords, box_width=rect_width, box_height=rect_height
        )

        # Apply the starting offset to the normalized coordinates
        offset_coords = [(x + x_start, y + y_start) for x, y in normalized_coords]

        # Debugging: Draw a bounding rectangle for the area
        # vsk.rect(x_start, y_start, rect_width, rect_height)

        # Draw the lines
        for i in range(len(offset_coords) - 1):
            x1, y1 = offset_coords[i]
            x2, y2 = offset_coords[i + 1]
            vsk.line(x1, y1, x2, y2)

        # Draw house at the start
        vsk.fill(1)
        x_house, y_house = offset_coords[0]
        self.draw_house(vsk, x_house, y_house, size=0.15)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(
            self.page_size,
        )
        vsk.scale("in")
        # self.drawPostcard(vsk, 0, 0)
        # self.drawPostcard(vsk, 0, 4.5)
        # Draw the GeoJSON in the top-left corner

        self.drawGeoJson(vsk, rect_size=(6, 4), xy_start=(0, 0))

        # Draw the GeoJSON in the bottom-right corner
        # self.drawGeoJson(vsk, rect_size=(6, 4), xy_start=(0, 4.5))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    PostcardSketch.display()
