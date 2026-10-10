"""Native Manim explanation. Revised scale-freedom ablation. Actual-map clips are inserted by assemble_films.py.
All diagram perturbations are labeled illustrations; empirical images come from
saved ACFA geometry, and video snippets use recorded accepted solver states.
"""
from pathlib import Path
import json,math,os
import numpy as np
from manim import *

if not os.environ.get('FGEFUL_PROJECT'):
    raise RuntimeError('Set FGEFUL_PROJECT or use fgeful-kit manim --project')
P=Path(os.environ['FGEFUL_PROJECT']).resolve()
META=json.loads((P/'assets/story.json').read_text())
from fgeful_kit.manim_theme import text, formula
BG='#080f19';PANEL='#112333';FG='#edf6fa';MUTED='#b5c6d4';GREEN='#65dfc4';GOLD='#ffd073';BLUE='#72c8f4';ORANGE='#f4aa67';PURPLE='#ca9aff';RED='#ff8290'
config.background_color=BG
config.frame_width=16;config.frame_height=9
config.max_files_cached=250

def camera_icon(p,color=BLUE,size=.12):
    m=Polygon(np.array([-.7,-.5,0]),np.array([.7,-.5,0]),np.array([0,.65,0]),color=color,fill_color=color,fill_opacity=.9,stroke_width=1).scale(size).move_to(p)
    return m

def node(label,p,color=GREEN):
    circ=Circle(radius=.40,color=color,stroke_width=3,fill_color=PANEL,fill_opacity=1).move_to(p)
    txt=formula(label,width=.67,size=30).move_to(p)
    return VGroup(circ,txt)
def factor(p,color=GOLD):return Square(side_length=.15,color=color,fill_color=color,fill_opacity=1).move_to(p)

def make_graph(y=0):
    nodes=VGroup(*[node('T_{'+str(i)+'}',[x,y,0]) for i,x in zip([k for k in [k for k in [0,1,2]]],[-4.2,0,4.2])])
    edges=VGroup();factors=VGroup()
    for a,b in zip(nodes[:-1],nodes[1:]):
        middle=(a.get_center()+b.get_center())/2;f=factor(middle,GREEN);factors.add(f)
        edges.add(Line(a.get_right(),f.get_left(),color=GREEN,stroke_width=3),Line(f.get_right(),b.get_left(),color=GREEN,stroke_width=3))
    return nodes,edges,factors

class Explain(Scene):
    def begin(self,title,subtitle,step='FORMULATION'):
        self.eyebrow=text('ACFA  /  '+step,18,GREEN,True).to_corner(UL,buff=.55)
        self.title=text(title,48,FG,True).next_to(self.eyebrow,DOWN,buff=.18,aligned_edge=LEFT)
        if self.title.width>14.8:self.title.scale_to_fit_width(14.8)
        self.sub=text(subtitle,28,MUTED).next_to(self.title,DOWN,buff=.18,aligned_edge=LEFT)
        if self.sub.width>14.8:self.sub.scale_to_fit_width(14.8)
        self.footer=text('Rigid chunks  →  Scale correction  →  Shared map',20,MUTED).to_edge(DOWN,buff=.34)
        self.add(self.eyebrow,self.footer);self.play(FadeIn(self.title,shift=.12*UP),FadeIn(self.sub),run_time=.8)
    def note(self,s,color=GREEN):
        n=text(s,30,FG).move_to([0,-3.3,0])
        if n.width>14:n.scale_to_fit_width(14)
        line=Line(n.get_left()+[-.16,-.2,0],n.get_left()+[-.16,.2,0],color=color,stroke_width=3)
        g=VGroup(line,n);self.play(FadeIn(g),run_time=.6);return g
    def finish(self,hold=2):self.wait(hold)

class ChunkState(Explain):
    def construct(self):
        self.begin('A chunk carries cameras, surfaces and scale.','The reconstruction is local. Its metric placement is an optimization problem.')
        asset=P/'assets/local_chunk.png'
        photo=(ImageMobject(str(asset)).set_width(6.3) if asset.exists() else VGroup(RoundedRectangle(width=6.3,height=3.8,color=BLUE),text('Local cameras + surfaces',28))).move_to([-4,.05,0]);border=SurroundingRectangle(photo,buff=.025,color='#28465b',stroke_width=2)
        self.play(FadeIn(photo),Create(border),run_time=1)
        self.play(FadeIn(text('Actual ACFA local reconstruction' if asset.exists() else 'Schematic: optional preview not supplied',24,MUTED).next_to(photo,DOWN,buff=.17)),run_time=.5)
        eq=formula(r'\mathbf p^W=s_kR_k\mathbf p^{V_k}+\mathbf t_k',width=7.5,size=46).move_to([3.65,1.1,0]);self.play(Write(eq),run_time=1.8)
        dims=VGroup(text('scale',27,GOLD),text('rotation',27,BLUE),text('translation',27,GREEN)).arrange(RIGHT,buff=.6).next_to(eq,DOWN,buff=.5)
        nums=VGroup(*[text(v,24,MUTED) for v in ['1 variable','3 variables','3 variables']])
        for d,l in zip(nums,dims):d.next_to(l,DOWN,buff=.15)
        self.play(FadeIn(dims),FadeIn(nums),run_time=1)
        cam=formula(r'\mathbf c^W_{ki}=T_k(\mathbf c_{ki})',width=7,size=40).move_to([3.65,-1.2,0]);self.play(Write(cam),run_time=1.2)
        self.note('One chunk transform must govern both its cameras and its dense geometry.');self.finish(4)

class RigidGPS(Explain):
    def construct(self):
        self.begin('Standard GPSFactor uses a Pose3 state.','Six variables: rotation and translation. The initialized chunk scale stays fixed.')
        n=node('P_k',[-5,.35,0],GOLD);f=factor([-5,1.7,0],GOLD);line=Line(f.get_bottom(),n.get_top(),color=GOLD,stroke_width=3)
        self.play(FadeIn(n),FadeIn(f),Create(line),FadeIn(text('GPS position',24,GOLD).next_to(f,UP,buff=.2)),run_time=1)
        eq=formula(r'\mathbf r_k^{\mathrm{GPS}}=\mathbf t_k-\mathbf g_k',width=8,size=47).move_to([2.0,1.2,0]);self.play(Write(eq),run_time=1.8)
        state=formula(r'P_k\in SE(3),\qquad s_k=s_k^{(0)}',width=9,size=43).move_to([2,-.05,0]);self.play(Write(state),run_time=1.8)
        geom=formula(r'\mathbf p^W=s_k^{(0)}R_k\mathbf p^{V_k}+\mathbf t_k',width=10,size=42).move_to([1,-1.4,0]);self.play(Write(geom),run_time=1.8)
        self.play(FadeIn(text('Native GTSAM factor attached at the chunk’s anchor camera.',25,MUTED).move_to([0,-2.35,0])),run_time=.6)
        self.note('The graph can reposition the chunk. It has no variable for resizing it.',GOLD);self.finish(4.5)

class RigidDistance(Explain):
    def construct(self):
        self.begin('A rigid transform preserves the wrong size.','Schematic: the predicted camera span is 12 m, but the measured span is 10 m.','GEOMETRIC EXPLANATION')
        # All lengths below are explicitly schematic; the next clip is the ACFA run.
        x1=-4.5;x2=3.5;y=-.1
        gps=VGroup(Dot([x1,y,0],radius=.08,color=GREEN),Dot([x2,y,0],radius=.08,color=GREEN))
        true=Line([x1,y,0],[x2,y,0],color=GREEN,stroke_width=4)
        measured=text('GPS separation: 10 m',29,GREEN).move_to([-.5,1,0])
        pred=VGroup(Line([x1,.35,0],[x1+9.6,.35,0],color=GOLD,stroke_width=5),camera_icon([x1,.35,0],GOLD,.2),camera_icon([x1+9.6,.35,0],GOLD,.2))
        self.play(Create(true),FadeIn(gps),FadeIn(measured),run_time=1)
        self.play(FadeIn(pred),run_time=.8)
        length=text('Rigid chunk span: 12 m',29,GOLD).move_to([.3,1.8,0]);self.play(FadeIn(length),run_time=.5)
        self.play(pred.animate.shift(LEFT*1.6),run_time=1.8);self.wait(.6);self.play(pred.animate.shift(RIGHT*.8),run_time=1.5)
        e=VGroup(DashedLine([-5.3,.35,0],[x1,y,0],color=RED),DashedLine([4.3,.35,0],[x2,y,0],color=RED));self.play(Create(e),run_time=.7)
        eq=formula(r'\|T_{\mathrm{rigid}}(\mathbf a)-T_{\mathrm{rigid}}(\mathbf b)\|=\|\mathbf a-\mathbf b\|',width=14,size=40).move_to([0,-1.5,0]);self.play(Write(eq),run_time=1.8)
        self.play(FadeIn(text('Translation and rotation cannot change this distance.',30,MUTED).move_to([0,-2.35,0])),run_time=.5)
        self.note('Wrong chunk scale can leave GPS and surface constraints in conflict.',GOLD);self.finish(3)

class ScaleAwareGPS(Explain):
    def construct(self):
        self.begin('Your GPS factor acts on a Sim3 chunk.','The observed camera position depends on scale, rotation and translation.')
        n=node('T_k',[0,.35,0],GREEN);gps=VGroup(*[factor([x,1.8,0],GOLD) for x in [-4,-2,0,2,4]]);cams=VGroup(*[camera_icon([x,-.75,0],BLUE,.15) for x in [-4,-2,0,2,4]])
        self.play(FadeIn(n),FadeIn(cams),run_time=.6);self.play(LaggedStart(*[FadeIn(f) for f in gps],lag_ratio=.12),run_time=.8)
        edges=VGroup(*[Line(f.get_bottom(),n.get_top(),color=GOLD,stroke_width=1.7) for f in gps]);self.play(Create(edges),run_time=.8)
        eq=formula(r'\mathbf r_{ki}^{\mathrm{GPS}}=s_kR_k\mathbf c_{ki}+\mathbf t_k-\mathbf g_i',size=45).move_to([0,-1.6,0]);self.play(Write(eq),run_time=2)
        d=formula(r'\frac{\partial\mathbf r_{ki}}{\partial\log s_k}=s_kR_k\mathbf c_{ki}',size=41,color=GREEN).move_to([0,-2.55,0]);self.play(Write(d),run_time=1.7)
        self.note('Camera offsets make the GPS residual sensitive to the chunk’s scale.');self.finish(4)

class SharedCorrection(Explain):
    def construct(self):
        self.begin('Correct the geometry, not just the trajectory.','The optimized similarity transforms all outputs owned by the chunk.')
        left=VGroup(formula(r'\{\mathbf c_{ki}\}',size=49,color=GOLD),text('local cameras',26,MUTED)).arrange(DOWN,buff=.25).move_to([-5,1,0])
        points=VGroup(formula(r'\{\mathbf p_{ku}\}',size=49,color=BLUE),text('local dense points',26,MUTED)).arrange(DOWN,buff=.25).move_to([-5,-1,0])
        n=node('T_k',[0,0,0]);right=VGroup(formula(r'\mathbf c^W_{ki}=T_k(\mathbf c_{ki})',width=6,size=37,color=GOLD),formula(r'\mathbf p^W_{ku}=T_k(\mathbf p_{ku})',width=6,size=37,color=BLUE)).arrange(DOWN,buff=.8).move_to([4.1,0,0])
        self.play(FadeIn(left),FadeIn(points),FadeIn(n),run_time=.8)
        self.play(Create(Arrow(left.get_right(),n.get_left(),buff=.15,color=GOLD)),Create(Arrow(points.get_right(),n.get_left(),buff=.15,color=BLUE)),run_time=1)
        self.play(Create(Arrow(n.get_right(),right.get_left(),buff=.15,color=GREEN)),FadeIn(right),run_time=1)
        eq=formula(r'\|T_k(\mathbf a)-T_k(\mathbf b)\|=s_k\|\mathbf a-\mathbf b\|',size=42).move_to([0,-2.45,0]);self.play(Write(eq),run_time=1.8)
        self.note('Scale correction changes internal world distances while preserving local shape.');self.finish(4)

class ACFAProtocol(Explain):
    def construct(self):
        self.begin('Test scale freedom on the same ACFA map.','91 chunks. Identical initial geometry, surface factors, GPS weights and priors.','EXPERIMENT')
        rows=[('Rigid baseline','Pose3 + GPSFactor','scale fixed',GOLD),('Stronger rigid control','Pose3 + per-camera GPS','scale fixed',GOLD),('Scale-aware graph','Similarity3 + custom GPS','scale free',GREEN)]
        for i,(a,b,c,color) in enumerate(rows):
            y=1.2-i*1.0;r=VGroup(text(a,27,color,True).move_to([-4.5,y,0]),text(b,28).move_to([.6,y,0]),text(c,27,color).move_to([5.2,y,0]));self.play(FadeIn(r,shift=UP*.1),run_time=.6)
        self.play(FadeIn(text('Position-only GPS isolates scale; the custom heading term is disabled.',27,MUTED).move_to([0,-2.25,0])),run_time=.7)
        self.note('The strengthened control gets exactly the same camera GPS observations.');self.finish(5)

class ACFAFinding(Explain):
    def construct(self):
        self.begin('The corrected ablation shows the scale effect.','P90 disagreement on revisit correspondences absent from these objectives.','MEASURED RESULT')
        cases={c:META['metrics'][stage] for c,stage in [('fixed_anchor','rigid_anchor'),('fixed_frame','rigid_frame'),('free_anchor','sim3_anchor'),('free_frame','sim3_frame')]}
        head=VGroup(text('GPS observations',28,MUTED).move_to([-4.5,1.35,0]),text('Scale fixed',30,GOLD,True).move_to([1.15,1.35,0]),text('Scale optimized',30,GREEN,True).move_to([4.75,1.35,0]));self.play(FadeIn(head),run_time=.6)
        for i,(label,mode) in enumerate([('One anchor per chunk','anchor'),('Same per-camera GPS','frame')]):
            y=.35-i*1.05;values=[cases['fixed_'+mode]['revisit_disagreement']['p90_m'],cases['free_'+mode]['revisit_disagreement']['p90_m']];row=VGroup(text(label,29).move_to([-4.5,y,0]),text(f'{values[0]:.2f} m',39,GOLD).move_to([1.15,y,0]),text(f'{values[1]:.2f} m',39,GREEN).move_to([4.75,y,0]));self.play(FadeIn(row),run_time=.7)
        note=text('Same camera GPS: 28.52 m → 10.60 m, a 62.8% reduction.',30,GREEN).move_to([0,-1.75,0]);self.play(FadeIn(note),run_time=.7)
        self.play(FadeIn(text('All four native GTSAM solves converge. GPS alone still leaves drift.',27,MUTED).move_to([0,-2.5,0])),run_time=.7)
        self.note('The improvement persists when the GPS observations are identical.');self.finish(5)

class DirectReferenceFactor(Explain):
    def construct(self):
        self.begin('A cross-robot match becomes a 3D factor.','Direct UFM route: lift each matched pixel through its own existing map.')
        E={'display_matches':META['imageMatches']};old=P/'assets'
        left=ImageMobject(str(old/'reference_216.png')).set_width(5.5).move_to([-4.4,.85,0]);right=ImageMobject(str(old/'exploring_1710.png')).set_width(4.4).move_to([4.5,.75,0]);self.play(FadeIn(left),FadeIn(right),run_time=.8)
        self.play(FadeIn(text('Spirit · fixed world frame W',23,BLUE).next_to(left,DOWN,buff=.12)),FadeIn(text('Starling · local chunk frame',23,ORANGE).next_to(right,DOWN,buff=.12)),run_time=.5)
        matches=VGroup()
        for row in E['display_matches']:
            u,v=row['uv_reference'];a,b=row['uv_exploring'];pa=left.get_center()+np.array([(u/584-.5)*left.width,(.5-v/328)*left.height,0]);pb=right.get_center()+np.array([(a/512-.5)*right.width,(.5-b/384)*right.height,0]);matches.add(Line(pa,pb,color=PURPLE,stroke_width=1.3),Dot(pa,radius=.025,color=PURPLE),Dot(pb,radius=.025,color=PURPLE))
        self.play(LaggedStart(*[Create(m) for m in matches],lag_ratio=.035),run_time=1.5)
        low=formula(r'\mathbf p^{V_k}\ \xleftarrow{\ \mathrm{depth,pose}\ }\ \mathbf u\ \leftrightarrow\ \mathbf v\ \xrightarrow{\ \mathrm{depth,pose}\ }\ \mathbf q^W',width=13,size=37).move_to([0,-1.6,0]);self.play(Write(low),run_time=2)
        eq=formula(r'\mathbf r^{\mathrm{ref}}_{kj}=T_k(\mathbf p_j^{V_k})-\mathbf q_j^W',size=45,color=BLUE).move_to([0,-2.55,0]);self.play(Write(eq),run_time=1.7)
        self.note('The reference stays fixed. The same Sim3 state corrects the exploring map.',BLUE);self.finish(4)

class FullGraph(Explain):
    def construct(self):
        self.begin('Add reference evidence to the same graph.','Continue directly from the new GPS solution; retain its existing factors.')
        ns,es,fs=make_graph(.8);self.play(FadeIn(ns),Create(es),FadeIn(fs),run_time=.8)
        gps=VGroup();refs=VGroup();lines=VGroup()
        for n in ns:
            for dx in [-.5,0,.5]:
                f=factor(n.get_center()+[dx,1.2,0],GOLD);gps.add(f);lines.add(Line(f.get_bottom(),n.get_top(),color=GOLD,stroke_width=1.6))
        f=factor([2.1,-.4,0],BLUE);refs.add(f);lines.add(Line(f.get_top(),ns[1].get_right(),color=BLUE,stroke_width=2.5))
        self.play(FadeIn(gps),FadeIn(refs),Create(lines),run_time=1)
        self.play(FadeIn(text('GPS',24,GOLD).move_to([-6.3,2,0])),FadeIn(text('reference surfaces',24,BLUE).move_to([4.6,-.4,0])),run_time=.6)
        eq=formula(r'\min_{\{s_k,R_k,\mathbf t_k\}}\quad E_{\mathrm{GPS}}+E_{\mathrm{overlap}}+E_{\mathrm{reference}}+E_{\mathrm{prior}}',width=14,size=40).move_to([0,-1.65,0]);self.play(Write(eq),run_time=2)
        self.play(FadeIn(text('29 reference groups added. No revisit factors are fitted in this film.',27,MUTED).move_to([0,-2.5,0])),run_time=.6)
        self.note('Measured cross-reference P90 improves from 6.17 m to 0.32 m.',BLUE);self.finish(4)

class Contribution(Explain):
    def construct(self):
        self.begin('The contribution: externally corrected chunks','A scale-aware interface between local reconstruction and a shared metric map.','TAKEAWAY')
        claims=['Expose each chunk’s scale, rotation and translation.','Constrain its cameras with GPS through that state.','Add verified cross-robot surfaces to the same graph.','Apply the corrected state to cameras and dense geometry.']
        for i,c in enumerate(claims):
            d=Dot([-6.65,1.45-i*.83,0],radius=.045,color=[GOLD,GREEN,BLUE,PURPLE][i]);s=text(c,30).next_to(d,RIGHT,buff=.23);self.play(FadeIn(d),FadeIn(s,shift=RIGHT*.1),run_time=.55)
        self.play(FadeIn(text('The ACFA ablation isolates the value of optimizing chunk scale.',28,MUTED).move_to([0,-2.45,0])),run_time=.6)
        self.note('Local reconstruction becomes geometry that external evidence can correct.');self.finish(4)
