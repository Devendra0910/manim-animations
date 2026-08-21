"""
Collatz Conjecture (3n+1 problem) animation.

Rule: start with any positive integer n.
  - if n is even, next term is n / 2
  - if n is odd,  next term is 3n + 1
Repeat. Conjecture: you always eventually reach 1.

Run with:
    manim -pql collatz.py CollatzScene      # low quality, fast preview
    manim -pqh collatz.py CollatzScene      # high quality
"""
from manim import *


def collatz_sequence(n: int) -> list[int]:
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq


class CollatzScene(Scene):
    def construct(self):
        self.camera.background_color = "#0f0f17"

        # ---------- Title ----------
        title = Text("The Collatz Conjecture", font_size=48, weight=BOLD)
        subtitle = Text("Take any number. Follow one simple rule.", font_size=28, color=GRAY_B)
        subtitle.next_to(title, DOWN, buff=0.4)
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(1)
        self.play(FadeOut(title), FadeOut(subtitle))

        # ---------- Rule explanation ----------
        rule_even = Text("if n is even:  n → n / 2", font_size=34, color=BLUE_C)
        rule_odd = Text("if n is odd:   n → 3n + 1", font_size=34, color=RED_C)
        rules = VGroup(rule_even, rule_odd).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(rule_even, shift=RIGHT))
        self.wait(0.6)
        self.play(FadeIn(rule_odd, shift=RIGHT))
        self.wait(1.2)
        self.play(FadeOut(rules))

        # ---------- Worked example: n = 27 ----------
        start_n = 27
        seq = collatz_sequence(start_n)

        header = Text(f"Let's start with n = {start_n}", font_size=32)
        header.to_edge(UP)
        self.play(Write(header))

        number = Text(str(seq[0]), font_size=96)
        number.move_to(ORIGIN)
        self.play(FadeIn(number, scale=1.3))
        self.wait(0.4)

        step_count = Text("steps: 0", font_size=26, color=GRAY_B).to_corner(DR)
        self.play(FadeIn(step_count))

        # Animate through the sequence (cap the number of shown steps for pacing)
        max_steps_shown = min(len(seq) - 1, 40)
        for i in range(1, max_steps_shown + 1):
            prev, curr = seq[i - 1], seq[i]
            is_even = prev % 2 == 0
            op_text = Text("÷ 2" if is_even else "× 3 + 1", font_size=30,
                            color=BLUE_C if is_even else RED_C)
            op_text.next_to(number, RIGHT, buff=0.6)

            new_number = Text(str(curr), font_size=96).move_to(number)

            self.play(FadeIn(op_text, shift=LEFT), run_time=0.25)
            self.play(Transform(number, new_number), run_time=0.3)
            self.play(FadeOut(op_text), run_time=0.15)

            new_step_count = Text(f"steps: {i}", font_size=26, color=GRAY_B).to_corner(DR)
            self.play(Transform(step_count, new_step_count), run_time=0.1)

            if curr == 1:
                break

        self.wait(0.5)
        landed = Text("Reached 1!", font_size=40, color=GREEN_C).next_to(number, DOWN, buff=0.8)
        self.play(Write(landed))
        self.wait(1)
        self.play(*[FadeOut(m) for m in [number, header, step_count, landed]])

        # ---------- Plot the trajectory as a graph ----------
        axes_header = Text(f"The full path of n = {start_n}", font_size=32).to_edge(UP)
        self.play(Write(axes_header))

        axes = Axes(
            x_range=[0, len(seq) - 1, max(1, (len(seq) - 1) // 10)],
            y_range=[0, max(seq) + 10, max(seq) // 8 or 1],
            x_length=10,
            y_length=5.5,
            axis_config={"include_tip": True, "color": GRAY_B},
        ).shift(DOWN * 0.3)
        x_label = Text("step", font_size=24).next_to(axes.x_axis, RIGHT)
        y_label = Text("value", font_size=24).next_to(axes.y_axis, UP)

        points = [axes.c2p(i, v) for i, v in enumerate(seq)]
        graph = VMobject(color=YELLOW_C, stroke_width=3)
        graph.set_points_as_corners([points[0]])

        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        dot = Dot(points[0], color=YELLOW_C, radius=0.07)
        self.play(FadeIn(dot))

        for i in range(1, len(points)):
            new_graph = graph.copy().set_points_as_corners(points[: i + 1])
            self.play(
                Transform(graph, new_graph),
                dot.animate.move_to(points[i]),
                run_time=max(0.02, 1.5 / len(points)),
            )
        self.add(graph)

        peak = max(seq)
        peak_label = Text(f"peak: {peak}", font_size=26, color=GRAY_B).to_corner(UL).shift(DOWN * 0.8)
        length_label = Text(f"length: {len(seq)} steps", font_size=26, color=GRAY_B).next_to(peak_label, DOWN, aligned_edge=LEFT)
        self.play(FadeIn(peak_label), FadeIn(length_label))
        self.wait(2)

        self.play(*[FadeOut(m) for m in self.mobjects])

        # ---------- Outro ----------
        outro = Text("Every number tried so far reaches 1.\nWill it always? Nobody has proven it yet.",
                      font_size=32, line_spacing=1.3)
        self.play(Write(outro))
        self.wait(2.5)
        self.play(FadeOut(outro))
