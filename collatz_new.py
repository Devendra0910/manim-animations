"""
Collatz Conjecture — fresh build, scene by scene.

Run a single scene at low quality for fast preview:
    manim -pql collatz_new.py Scene1Branches
"""
import math
import os
from manim import *

PINK = "#ff2e88"
CYAN = "#00e5ff"
GOLD = "#ffd60a"
GREEN = "#00e676"
ORANGE = "#ff6b35"
PURPLE = "#9d4edd"
TEAL_C = "#20c997"
ROSE = "#e63980"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BEEP_EVEN = os.path.join(ASSETS_DIR, "beep_even.wav")   # lower pitch: ÷ 2
BEEP_ODD = os.path.join(ASSETS_DIR, "beep_odd.wav")     # higher pitch: × 3 + 1

# Cloned-voice narration clips (assets/narration/, gitignored — not committed).
NARRATION_DIR = os.path.join(ASSETS_DIR, "narration")
SCENE3_INTRO = os.path.join(NARRATION_DIR, "scene3_intro.wav")  # "Let's start with n equals twenty six."
SCENE3_PEAK = os.path.join(NARRATION_DIR, "scene3_peak.wav")    # "Watch it jump to forty..."
SCENE3_LAND = os.path.join(NARRATION_DIR, "scene3_land.wav")    # "Ten steps later, it lands on one."

SCENE4_INTRO = os.path.join(NARRATION_DIR, "scene4_intro.wav")  # "Twenty six took ten steps. Twenty seven takes..."
SCENE4_PEAK = os.path.join(NARRATION_DIR, "scene4_peak.wav")    # "It climbs past nine thousand..."
SCENE4_LAND = os.path.join(NARRATION_DIR, "scene4_land.wav")    # "Same simple rule. Wildly different journey."


def collatz_sequence(n: int) -> list[int]:
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq


def build_collatz_tree(max_depth=9, max_nodes=40):
    """Reverse-Collatz tree rooted at 1: for each value, its predecessors
    are 2*value (always valid) and (value-1)/3 (valid when that's an odd
    integer > 1). Returns {parent: [children]}, {node: depth}, {node: parent},
    and `order` (nodes in BFS discovery order, root first) so callers can
    grow the tree one node at a time in the same order it was discovered."""
    from collections import deque
    children_map = {1: []}
    depth_of = {1: 0}
    parent_of = {}
    order = [1]
    visited = {1}
    queue = deque([1])
    while queue and len(visited) < max_nodes:
        val = queue.popleft()
        d = depth_of[val]
        if d >= max_depth:
            continue
        preds = [2 * val]
        if (val - 1) % 3 == 0:
            cand = (val - 1) // 3
            if cand > 1 and cand % 2 == 1:
                preds.append(cand)
        for p in preds:
            if p not in visited and len(visited) < max_nodes:
                visited.add(p)
                children_map[val].append(p)
                children_map[p] = []
                depth_of[p] = d + 1
                parent_of[p] = val
                order.append(p)
                queue.append(p)
    return children_map, depth_of, parent_of, order


def layout_tree(children_map, depth_of, root=1, x_spacing=0.95, y_spacing=0.9):
    """Simple tree layout: leaves get sequential x-slots, each parent sits
    above the average x of its children. Root at y=0, depth grows +y."""
    xpos = {}
    leaf_counter = [0]

    def visit(node):
        kids = children_map.get(node, [])
        if not kids:
            xpos[node] = leaf_counter[0] * x_spacing
            leaf_counter[0] += 1
        else:
            for k in kids:
                visit(k)
            xpos[node] = sum(xpos[k] for k in kids) / len(kids)

    visit(root)
    mean_x = xpos[root]
    return {node: [x - mean_x, depth_of[node] * y_spacing, 0.0] for node, x in xpos.items()}


def make_tree_mobject(max_depth=9, max_nodes=40):
    """Builds the Collatz tree as Manim mobjects, one node per actual
    reverse-Collatz value with its number labeled, grown out to max_depth
    (root 1 at depth 0). Returns:
      full       - VGroup of everything (for the closing FadeOut)
      root_group - VGroup(root_dot, root_label)
      reveal     - list of (edge, VGroup(dot, label)) in BFS discovery
                   order, one entry per non-root node, for a one-by-one
                   growth animation.
    """
    children_map, depth_of, parent_of, order = build_collatz_tree(max_depth, max_nodes)
    positions = layout_tree(children_map, depth_of)
    max_depth_val = max(depth_of.values()) or 1

    dot_of, label_of, edge_of = {}, {}, {}
    everything = VGroup()

    for node in order:
        pos = positions[node]
        d = depth_of[node]
        size = 0.15 if node == 1 else 0.085
        color = interpolate_color(ManimColor(GOLD), ManimColor(CYAN), d / max_depth_val)
        dot = Dot(pos, radius=size, color=color)
        label = Text(str(node), font_size=20, color=WHITE)
        label.next_to(dot, RIGHT, buff=0.1)
        dot_of[node] = dot
        label_of[node] = label
        everything.add(dot, label)
        if node in parent_of:
            edge = Line(positions[parent_of[node]], pos, stroke_width=2.5,
                        color=interpolate_color(ManimColor(GOLD), ManimColor(PURPLE), d / max_depth_val))
            edge_of[node] = edge
            everything.add(edge)

    everything.scale_to_fit_height(6.2)
    if everything.width > 12.5:
        everything.scale_to_fit_width(12.5)
    everything.move_to(ORIGIN)

    full = everything
    root_group = VGroup(dot_of[1], label_of[1])
    reveal = [(edge_of[node], VGroup(dot_of[node], label_of[node])) for node in order[1:]]

    return full, root_group, reveal


# ============================================================
# Scene 1 — different starting numbers, different branches,
# all of them ending up at 1.
# ============================================================
class Scene1Branches(Scene):
    def construct(self):
        self.camera.background_color = "#120a1f"

        # Real tree structure: every value's predecessors are 2*value and
        # (value-1)/3 (when valid), so this is an actual branching tree
        # rooted at 1 rather than independently-drawn lines — separate
        # branches share edges and nodes exactly where their numbers'
        # journeys actually coincide, then merge down into the root.
        full, root_group, reveal = make_tree_mobject(max_depth=13, max_nodes=70)

        self.wait(0.4)
        self.play(FadeIn(root_group, scale=0.3), run_time=0.4)
        for edge, node_group in reveal:
            self.play(Create(edge), FadeIn(node_group), run_time=0.15)
        self.wait(2.0)
        self.play(FadeOut(full), run_time=1.0)
        self.wait(0.3)


# ============================================================
# Scene 2 — introduction: what the Collatz conjecture is,
# where it came from, and why it's notorious.
# ============================================================
class Scene2Intro(Scene):
    """Timings below are tuned to a recorded voiceover (9 clips, cloned
    from voice_sample.wav via XTTS v2, then sped up 1.3x with ffmpeg's
    atempo since the raw cadence read as slow) rather than picked for
    pacing — each self.wait() covers the matching narration clip's
    actual duration plus a small buffer, so text and voice land
    together. See narration_script.json / durations.json for the clip
    timings this was built against."""

    def construct(self):
        self.camera.background_color = "#120a1f"

        # ---------- Title ---------- (seg 0, 1.95s, starts as title finishes growing)
        title = Text("The Collatz Conjecture", font_size=54, weight=BOLD)
        title.set_color_by_gradient(PINK, CYAN, GOLD)
        self.play(GrowFromCenter(title), run_time=1.0)
        self.wait(2.45)
        self.play(FadeOut(title), run_time=1.0)

        # ---------- History: 1937 ---------- (seg 1, 4.88s, starts as "1937" appears)
        year = Text("1937", font_size=120, color=GOLD)
        self.play(FadeIn(year, scale=1.5), run_time=1.0)
        self.wait(1.5)
        sub = Text("Lothar Collatz", font_size=34, color=CYAN).next_to(year, DOWN, buff=0.6)
        self.play(FadeIn(sub, shift=UP), run_time=1.0)
        self.wait(1.88)
        self.play(FadeOut(year), FadeOut(sub), run_time=1.0)

        # ---------- The rule ---------- (seg 2: 2.27s, seg 3: 2.73s, seg 4: 4.37s)
        rule_even = Text("if n is even:  n → n / 2", font_size=34, color=CYAN)
        rule_odd = Text("if n is odd:   n → 3n + 1", font_size=34, color=PINK)
        VGroup(rule_even, rule_odd).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(rule_even, shift=RIGHT), run_time=0.8)
        self.wait(1.77)
        self.play(FadeIn(rule_odd, shift=RIGHT), run_time=0.8)
        self.wait(2.23)

        conjecture = Text("Repeat, and you always reach 1.",
                           font_size=30, color=GREEN)
        conjecture.next_to(VGroup(rule_even, rule_odd), DOWN, buff=0.9)
        self.play(FadeIn(conjecture, shift=UP), run_time=0.8)
        self.wait(4.07)
        self.play(FadeOut(rule_even), FadeOut(rule_odd), FadeOut(conjecture), run_time=1.0)

        # ---------- Many names, one problem ---------- (seg 5, 8.98s across 4 names)
        names = ["The 3n + 1 Problem", "Ulam's Conjecture",
                 "The Syracuse Problem", "Kakutani's Problem"]
        name_colors = [CYAN, PINK, GOLD, PURPLE]
        per_name_hold = 1.64  # (8.98s / 4 names) - 0.6s transition each
        current = Text(names[0], font_size=38, color=name_colors[0])
        self.play(FadeIn(current), run_time=0.6)
        self.wait(per_name_hold)
        for name, col in zip(names[1:], name_colors[1:]):
            nxt = Text(name, font_size=38, color=col)
            self.play(Transform(current, nxt), run_time=0.6)
            self.wait(per_name_hold)
        self.wait(0.4)
        self.play(FadeOut(current), run_time=0.8)

        # ---------- Erdős quote ---------- (seg 6: 2.34s, seg 7: 4.45s)
        quote = Text('"Mathematics is not yet\nready for such problems."',
                      font_size=36, slant=ITALIC, line_spacing=1.3, color=GOLD)
        attribution = Text("— Paul Erdős", font_size=26, color=PURPLE).next_to(quote, DOWN, buff=0.5)
        self.play(Write(quote), run_time=2.0)
        self.wait(0.64)
        self.play(FadeIn(attribution), run_time=0.8)
        self.wait(4.15)
        self.play(FadeOut(quote), FadeOut(attribution), run_time=1.0)

        # ---------- Bridge into the next scene ---------- (seg 8, 1.98s)
        bridge = Text("Let's see why, with an example.", font_size=34, color=CYAN)
        self.play(FadeIn(bridge, scale=0.8), run_time=0.6)
        self.wait(1.88)
        self.play(FadeOut(bridge), run_time=0.8)


# ============================================================
# Scene 3 — worked example: n = 26, every step shown, a beep on
# every conversion, and a trajectory graph that fills in live.
# ============================================================
class Scene3Example26(Scene):
    def construct(self):
        self.camera.background_color = "#120a1f"
        seq = collatz_sequence(26)
        peak_val = max(seq)

        # "Let's start with n equals twenty-six." — plays under the setup below.
        self.add_sound(SCENE3_INTRO, gain=-3)

        header = Text("n = 26", font_size=34, color=CYAN).to_edge(UP)
        self.play(Write(header), run_time=0.7)

        number = Text(str(seq[0]), font_size=88, color=WHITE).move_to(UP * 1.1)
        self.play(FadeIn(number, scale=1.3), run_time=0.5)

        step_count = Text("steps: 0", font_size=24, color=GRAY_B).to_corner(DR)
        self.play(FadeIn(step_count), run_time=0.35)

        # Trajectory graph, built up one point at a time as the walk proceeds.
        axes = Axes(
            x_range=[0, len(seq) - 1, 4],
            y_range=[0, max(seq) + 5, 10],
            x_length=9.5, y_length=2.6,
            axis_config={"color": GRAY_C, "stroke_width": 1.5, "include_tip": False,
                         "font_size": 18},
        ).to_edge(DOWN, buff=0.55)
        self.play(Create(axes), run_time=0.6)

        first_dot = Dot(axes.c2p(0, seq[0]), radius=0.06, color=GOLD)
        graph_group = VGroup(first_dot)
        self.play(FadeIn(first_dot, scale=0.5), run_time=0.25)
        self.wait(0.5)  # room for the intro line (2.62s, sped up 1.3x) to finish

        for i in range(1, len(seq)):
            prev, curr = seq[i - 1], seq[i]
            is_even = prev % 2 == 0
            op_color = CYAN if is_even else PINK

            if curr == peak_val:
                # "Watch it jump to forty before it turns around." — the peak
                # of this trajectory; plays as background commentary over the
                # next several (fast) steps.
                self.add_sound(SCENE3_PEAK, gain=-3)

            op_text = Text("÷ 2" if is_even else "× 3 + 1", font_size=28, color=op_color)
            op_text.next_to(number, RIGHT, buff=0.6)
            new_number = Text(str(curr), font_size=88, color=WHITE).move_to(number)

            # A beep lands right as the number flips — pitch tells even from odd.
            self.add_sound(BEEP_EVEN if is_even else BEEP_ODD, gain=-6)
            self.play(FadeIn(op_text, shift=LEFT), run_time=0.18)
            self.play(Transform(number, new_number), Flash(number, color=op_color,
                                                             flash_radius=0.9, line_length=0.2),
                      run_time=0.26)
            self.play(FadeOut(op_text), run_time=0.12)

            new_dot = Dot(axes.c2p(i, curr), radius=0.06,
                          color=GREEN if curr == 1 else GOLD)
            new_line = Line(axes.c2p(i - 1, prev), axes.c2p(i, curr),
                            color=PURPLE, stroke_width=2.5)
            graph_group.add(new_line, new_dot)
            self.play(Create(new_line), FadeIn(new_dot, scale=0.5), run_time=0.14)

            new_step = Text(f"steps: {i}", font_size=24, color=GRAY_B).to_corner(DR)
            self.play(Transform(step_count, new_step), run_time=0.08)

        self.wait(0.4)
        self.add_sound(SCENE3_LAND, gain=-3)  # "Ten steps later, it lands on one."
        landed = Text("Reached 1!", font_size=38, color=GREEN).next_to(number, DOWN, buff=0.6)
        self.play(Write(landed), run_time=0.8)
        self.wait(3.8)  # room for the landing line (4.27s, sped up 1.3x) to finish
        self.play(*[FadeOut(m) for m in [number, header, step_count, landed, axes, graph_group]],
                  run_time=1.0)


# ============================================================
# Scene 4 — n = 27: same rule, wildly different journey. Contrasts
# against Scene 3's tame 10-step n = 26 with a fast, graph-driven
# reveal instead of a step-by-step walk (111 steps at n = 26's
# pace would take over a minute).
# ============================================================
class Scene4Example27(Scene):
    def construct(self):
        self.camera.background_color = "#120a1f"
        seq26_steps = 10  # from Scene3Example26, for the comparison beat
        seq = collatz_sequence(27)
        total_steps = len(seq) - 1
        peak_val = max(seq)

        # ---------- Comparison recap ---------- (5.19s narration, sped up 1.3x)
        self.add_sound(SCENE4_INTRO, gain=-3)
        left = VGroup(
            Text("n = 26", font_size=32, color=CYAN),
            Text(f"{seq26_steps} steps", font_size=44, color=GOLD, weight=BOLD),
        ).arrange(DOWN, buff=0.3).shift(LEFT * 3.2)
        self.play(FadeIn(left, shift=UP), run_time=0.7)
        self.wait(1.05)

        right_label = Text("n = 27", font_size=32, color=PINK).shift(RIGHT * 3.2 + UP * 0.55)
        right_q = Text("?", font_size=44, color=GRAY_B).next_to(right_label, DOWN, buff=0.3)
        self.play(FadeIn(right_label, shift=UP), FadeIn(right_q, scale=0.5), run_time=0.6)
        self.wait(0.9)

        right_steps = Text(f"{total_steps} steps", font_size=44, color=ORANGE,
                            weight=BOLD).move_to(right_q)
        self.play(Transform(right_q, right_steps),
                  Flash(right_q, color=ORANGE, flash_radius=0.8), run_time=0.6)
        self.wait(1.65)
        self.play(FadeOut(left), FadeOut(right_label), FadeOut(right_q), run_time=0.8)

        # ---------- Setup: header, big number, trajectory graph ----------
        header = Text("n = 27", font_size=34, color=PINK).to_edge(UP)
        self.play(Write(header), run_time=0.6)

        number = Text(str(seq[0]), font_size=88, color=WHITE).move_to(UP * 1.1)
        self.play(FadeIn(number, scale=1.3), run_time=0.4)

        step_count = Text("steps: 0", font_size=24, color=GRAY_B).to_corner(DR)
        self.play(FadeIn(step_count), run_time=0.3)

        axes = Axes(
            x_range=[0, total_steps, 20],
            y_range=[0, peak_val + 500, 2000],
            x_length=9.5, y_length=3.0,
            axis_config={"color": GRAY_C, "stroke_width": 1.5, "include_tip": False,
                         "font_size": 18},
        ).to_edge(DOWN, buff=0.45)
        self.play(Create(axes), run_time=0.5)

        first_dot = Dot(axes.c2p(0, seq[0]), radius=0.05, color=GOLD)
        graph_group = VGroup(first_dot)
        self.play(FadeIn(first_dot, scale=0.5), run_time=0.2)

        # ---------- The rapid walk: all 111 steps, fast, one (quiet) beep each ----------
        for i in range(1, len(seq)):
            prev, curr = seq[i - 1], seq[i]
            is_even = prev % 2 == 0

            if curr == peak_val:
                # "It climbs past nine thousand, before it turns back down."
                self.add_sound(SCENE4_PEAK, gain=-4)

            self.add_sound(BEEP_EVEN if is_even else BEEP_ODD, gain=-14)

            new_dot = Dot(axes.c2p(i, curr), radius=0.05,
                          color=GREEN if curr == 1 else GOLD)
            new_line = Line(axes.c2p(i - 1, prev), axes.c2p(i, curr),
                            color=PURPLE, stroke_width=2)
            new_step = Text(f"steps: {i}", font_size=24, color=GRAY_B).to_corner(DR)
            graph_group.add(new_line, new_dot)

            self.play(Create(new_line), FadeIn(new_dot, scale=0.5),
                      Transform(step_count, new_step), run_time=0.045)

        new_number = Text("1", font_size=88, color=WHITE).move_to(number)
        self.play(Transform(number, new_number), run_time=0.3)
        self.wait(1.5)  # let the peak line ("...turns back down") finish before landing

        self.add_sound(SCENE4_LAND, gain=-3)  # "Same simple rule. Wildly different journey."
        landed = Text(f"Reached 1 — after {total_steps} steps", font_size=32,
                      color=GREEN).next_to(number, DOWN, buff=0.6)
        self.play(Write(landed), run_time=0.9)
        self.wait(3.9)
        self.play(*[FadeOut(m) for m in [number, header, step_count, landed, axes, graph_group]],
                  run_time=1.0)
