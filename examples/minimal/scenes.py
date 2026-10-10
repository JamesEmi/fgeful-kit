"""A short equation scene to interleave with the synthetic data clip."""
from manim import *
from fgeful_kit.manim_theme import ExplainScene, formula, text, GREEN, GOLD, BLUE, MUTED


class SharedTransform(ExplainScene):
    def construct(self):
        self.begin("One transform, consistent geometry.", "Cameras and surfaces inherit the same correction.",
                   label="SCHEMATIC / EXPLANATION", footer="Local observations → shared correction → world geometry")
        equation = formula(r"\mathbf p^W=s_kR_k\mathbf p^{V_k}+\mathbf t_k", size=50).move_to([0, 1, 0])
        self.play(Write(equation), run_time=1.2)
        labels = VGroup(text("scale", 28, GOLD), text("rotation", 28, BLUE), text("translation", 28, GREEN)).arrange(RIGHT, buff=1).move_to([0, -.1, 0])
        self.play(FadeIn(labels), run_time=.6)
        cameras = formula(r"\mathbf c^W_{ki}=T_k(\mathbf c_{ki})", size=42).move_to([0, -1.35, 0])
        self.play(Write(cameras), run_time=1)
        self.note("The next clip is a synthetic teaching example, not an experimental result.")
        self.wait(1.5)
