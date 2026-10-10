"""Reusable typography and layout from the original captioned explainers."""
from importlib.resources import files

from manim import (Scene, Text, MathTex, VGroup, Line, FadeIn, UP, DOWN, UL, LEFT,
                   BOLD, NORMAL, config)
import manimpango

BG, FG, MUTED = "#080f19", "#edf6fa", "#b5c6d4"
GREEN, GOLD, BLUE, PURPLE = "#65dfc4", "#ffd073", "#72c8f4", "#ca9aff"
config.background_color = BG
config.frame_width, config.frame_height = 16, 9
for font in ("Lato-Regular.ttf", "Lato-Bold.ttf"):
    manimpango.register_font(str(files("fgeful_kit").joinpath("fonts", font)))


def text(value, size=34, color=FG, bold=False):
    return Text(value, font="Lato", font_size=size, color=color, weight=BOLD if bold else NORMAL)


def formula(value, width=13, color=FG, size=43):
    equation = MathTex(value, font_size=size, color=color)
    if equation.width > width:
        equation.scale_to_fit_width(width)
    return equation


class ExplainScene(Scene):
    def begin(self, title, subtitle, label="EXPLAINER", footer=""):
        eyebrow = text(label, 18, GREEN, True).to_corner(UL, buff=.55)
        heading = text(title, 46, FG, True)
        if heading.width > 14.8:
            heading.scale_to_fit_width(14.8)
        heading.next_to(eyebrow, DOWN, buff=.18, aligned_edge=LEFT)
        sub = text(subtitle, 27, MUTED)
        if sub.width > 14.8:
            sub.scale_to_fit_width(14.8)
        sub.next_to(heading, DOWN, buff=.18, aligned_edge=LEFT)
        self.add(eyebrow, text(footer, 19, MUTED).to_edge(DOWN, buff=.34))
        self.play(FadeIn(heading, shift=.12 * UP), FadeIn(sub), run_time=.7)

    def note(self, message, color=GREEN):
        caption = text(message, 28).move_to([0, -3.3, 0])
        if caption.width > 14:
            caption.scale_to_fit_width(14)
        marker = Line(caption.get_left() + [-.16, -.2, 0], caption.get_left() + [-.16, .2, 0], color=color, stroke_width=3)
        group = VGroup(marker, caption)
        self.play(FadeIn(group), run_time=.5)
        return group
