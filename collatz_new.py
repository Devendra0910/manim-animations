"""
Collatz Conjecture — fresh build, scene by scene.

Run a single scene at low quality for fast preview:
    manim -pql collatz_new.py Scene1Branches
"""
import math
from manim import *

PINK = "#ff2e88"
CYAN = "#00e5ff"
GOLD = "#ffd60a"
GREEN = "#00e676"
ORANGE = "#ff6b35"
PURPLE = "#9d4edd"
TEAL_C = "#20c997"
ROSE = "#e63980"


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
    from voice_sample.wav via XTTS v2) rather than picked for pacing —
    each self.wait() covers the matching narration clip's actual
    duration plus a small buffer, so text and voice land together.
    See narration_script.json / durations.json for the clip timings
    this was built against."""

    def construct(self):
        self.camera.background_color = "#120a1f"

        # ---------- Title ---------- (seg 0, 2.55s, starts as title finishes growing)
        title = Text("The Collatz Conjecture", font_size=54, weight=BOLD)
        title.set_color_by_gradient(PINK, CYAN, GOLD)
        self.play(GrowFromCenter(title), run_time=1.0)
        self.wait(3.05)
        self.play(FadeOut(title), run_time=1.0)

        # ---------- History: 1937 ---------- (seg 1, 6.36s, starts as "1937" appears)
        year = Text("1937", font_size=120, color=GOLD)
        self.play(FadeIn(year, scale=1.5), run_time=1.0)
        self.wait(1.5)
        sub = Text("Lothar Collatz", font_size=34, color=CYAN).next_to(year, DOWN, buff=0.6)
        self.play(FadeIn(sub, shift=UP), run_time=1.0)
        self.wait(3.36)
        self.play(FadeOut(year), FadeOut(sub), run_time=1.0)

        # ---------- The rule ---------- (seg 2: 2.97s, seg 3: 3.57s, seg 4: 5.71s)
        rule_even = Text("if n is even:  n → n / 2", font_size=34, color=CYAN)
        rule_odd = Text("if n is odd:   n → 3n + 1", font_size=34, color=PINK)
        VGroup(rule_even, rule_odd).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(rule_even, shift=RIGHT), run_time=0.8)
        self.wait(2.47)
        self.play(FadeIn(rule_odd, shift=RIGHT), run_time=0.8)
        self.wait(3.07)

        conjecture = Text("Repeat, and you always reach 1.",
                           font_size=30, color=GREEN)
        conjecture.next_to(VGroup(rule_even, rule_odd), DOWN, buff=0.9)
        self.play(FadeIn(conjecture, shift=UP), run_time=0.8)
        self.wait(5.41)
        self.play(FadeOut(rule_even), FadeOut(rule_odd), FadeOut(conjecture), run_time=1.0)

        # ---------- Many names, one problem ---------- (seg 5, 11.69s across 4 names)
        names = ["The 3n + 1 Problem", "Ulam's Conjecture",
                 "The Syracuse Problem", "Kakutani's Problem"]
        name_colors = [CYAN, PINK, GOLD, PURPLE]
        per_name_hold = 2.32  # (11.69s / 4 names) - 0.6s transition each
        current = Text(names[0], font_size=38, color=name_colors[0])
        self.play(FadeIn(current), run_time=0.6)
        self.wait(per_name_hold)
        for name, col in zip(names[1:], name_colors[1:]):
            nxt = Text(name, font_size=38, color=col)
            self.play(Transform(current, nxt), run_time=0.6)
            self.wait(per_name_hold)
        self.wait(0.4)
        self.play(FadeOut(current), run_time=0.8)

        # ---------- Erdős quote ---------- (seg 6: 3.06s, seg 7: 5.80s)
        quote = Text('"Mathematics is not yet\nready for such problems."',
                      font_size=36, slant=ITALIC, line_spacing=1.3, color=GOLD)
        attribution = Text("— Paul Erdős", font_size=26, color=PURPLE).next_to(quote, DOWN, buff=0.5)
        self.play(Write(quote), run_time=2.0)
        self.wait(1.36)
        self.play(FadeIn(attribution), run_time=0.8)
        self.wait(5.5)
        self.play(FadeOut(quote), FadeOut(attribution), run_time=1.0)

        # ---------- Bridge into the next scene ---------- (seg 8, 1.48s)
        bridge = Text("Let's see why, with an example.", font_size=34, color=CYAN)
        self.play(FadeIn(bridge, scale=0.8), run_time=0.6)
        self.wait(2.49)
        self.play(FadeOut(bridge), run_time=0.8)
