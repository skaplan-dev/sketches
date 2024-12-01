import math
import random
import vsketch


def rotation(angle: float) -> complex:
    """A rotation of the unit vector by the given angle in radians."""
    return complex(math.cos(angle), math.sin(angle))


def comp_eq(a: complex, b: complex, tolerance: float = 0.1) -> bool:
    return abs(a.real - b.real) < tolerance and abs(a.imag - b.imag) < tolerance


class HexSketch(vsketch.SketchClass):
    # Sketch parameters:
    width = vsketch.Param(4)
    width_scale = vsketch.Param(0.7)
    length = vsketch.Param(12)
    length_scale = vsketch.Param(0.5)  # 1/math.sqrt(2)
    iters = vsketch.Param(8)
    level_prob = vsketch.Param(0.1)
    circle_size = vsketch.Param(0.25)
    circle_prob = vsketch.Param(0.1)
    circle_fill_prob = vsketch.Param(0.7)

    fuel_cost = [0, 1, 2]

    def draw_branch(
        self, vsk: vsketch.Vsketch, x: complex, v: complex, width: float, fuel: int
    ) -> None:
        if fuel <= 0 or abs(v) < 0.5:
            return

        # Line
        vsk.stroke(1)
        vsk.strokeWeight(max(1, int(width)))
        end = x + v
        self.nodes.append(end)
        vsk.line(x.real, x.imag, end.real, end.imag)

        directions = [
            v * rotation(math.pi / 3),
            v * rotation(-math.pi / 3),
        ]  # +/-60 deg
        for new_v in directions:
            new_end = end + new_v
            if random.random() < (
                self.level_prob if abs(end.real) < abs(end.imag) else 0.6
            ) or any(comp_eq(node, new_end) for node in self.nodes):
                self.draw_branch(
                    vsk,
                    end,
                    new_v * self.length_scale,
                    width * self.width_scale,
                    fuel - random.choice(self.fuel_cost),
                )
            else:
                self.draw_branch(
                    vsk, end, new_v, width, fuel - random.choice(self.fuel_cost)
                )

        # Circle
        if random.random() < self.circle_prob and abs(v) >= 2:
            vsk.stroke(2)
            if random.random() < self.circle_fill_prob:
                vsk.fill(2)
            else:
                vsk.noFill()
            vsk.strokeWeight(max(1, int(width)))
            vsk.circle(end.real, end.imag, radius=abs(v) * self.circle_size)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        size = "8.5inx11in"
        vsk.scale("mm")
        vsk.penWidth("0.15mm")

        self.nodes = [0 + 0j]
        for start_dir in [
            1 + 0j,
            rotation(math.pi * 2 / 3),
            rotation(-math.pi * 2 / 3),
        ]:
            self.draw_branch(
                vsk, 0 + 0j, complex(0, self.length) * start_dir, self.width, self.iters
            )

        layout = f"layout -h center -v center {size} translate -- 0 -1.5cm"
        pens = "color -l1 black penwidth -l1 0.3mm color -l2 black penwidth -l2 0.3mm"
        vsk.vpype(f"{layout} {pens}")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    HexSketch.display()
