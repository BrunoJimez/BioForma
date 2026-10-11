"""A lightweight software 3D viewport using native Tk Canvas."""
from __future__ import annotations
from .i18n import tr
from .paths import UI_FONT, MONO_FONT

import math
import tkinter as tk
from dataclasses import dataclass
from xml.sax.saxutils import escape
from .core import BASE_COLORS, COMPLEMENT, ELEMENT_COLORS, atomic_write

BG = '#101824'


@dataclass
class Point:
    xyz: tuple[float,float,float]
    color: str
    radius: float = 4
    label: str = ''
    detail: str = ''


def dna_geometry(seq, start, count, baseline=''):
    """Idealized double helix. Dots denote bases, not atoms."""
    stop = min(len(seq), start+count)
    n = stop-start
    pts, links = [], []
    for j,i in enumerate(range(start, stop)):
        angle = j*2*math.pi/10.5
        base = seq[i]
        for strand in (0,1):
            a = angle+strand*math.pi
            b = base if strand == 0 else base.translate(COMPLEMENT)
            changed = i >= len(baseline) or base != baseline[i]
            pts.append(Point((math.cos(a)*10, (j-(n-1)/2)*3.4, math.sin(a)*10),
                             BASE_COLORS.get(b,'#abb6c3'), 5,
                             b if count <= 80 else '',
                             tr('Posição {0} • base {1} • ').format(i + 1, b)+(tr('fita 5′→3′') if strand==0 else tr('complementar antiparalela'))+
                             (tr(' • alterada nesta posição') if changed else '')))
        links.append((2*j,2*j+1,'#f077b5' if changed else '#3b536b',2))
        if j:
            for strand in (0,1):
                links.append((2*(j-1)+strand,2*j+strand,'#6489a4',3))
    return pts,links


def pdb_geometry(atoms, mode='trace', cap=1800):
    if mode == 'trace':
        selected = [a for a in atoms if a.name == 'CA' and a.element == 'C']
    else:
        selected = atoms
    total = len(selected)
    selected = selected[:cap]
    if not selected:
        return [], [], total
    centers = tuple(sum(getattr(a,dim) for a in selected)/len(selected) for dim in ('x','y','z'))
    pts = [Point((a.x-centers[0],a.y-centers[1],a.z-centers[2]),
                 ELEMENT_COLORS.get(a.element,'#b89feb'),4 if mode=='trace' else 3,'',
                 tr('{0} {1} • cadeia {2} • {3} ({4})').format(a.resname, a.residue, a.chain.strip() or '—', a.name, a.element))
           for a in selected]
    links = []
    if mode == 'trace':
        for i in range(1,len(selected)):
            a,b = selected[i-1],selected[i]
            distance = math.dist((a.x,a.y,a.z),(b.x,b.y,b.z))
            if a.chain==b.chain and a.segment==b.segment and a.residue != b.residue and distance <= 4.5:
                links.append((i-1,i,'#53c6ca',3))
    return pts,links,total


class Viewport(tk.Canvas):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,bg=BG,highlightthickness=0,**kwargs)
        self.points,self.links = [],[]
        self.yaw,self.pitch = .45,.15
        self.zoom,self.pan_x,self.pan_y = 1.,0.,0.
        self.caption,self.detail = '',''
        self.projected = []
        self.bind('<Configure>',lambda e:self.draw())
        self.bind('<ButtonPress-1>',self.begin)
        self.bind('<B1-Motion>',self.orbit)
        self.bind('<ButtonRelease-1>',self.pick)
        self.bind('<ButtonPress-3>',self.begin)
        self.bind('<B3-Motion>',self.pan)
        self.bind('<MouseWheel>',lambda e:self.wheel(1.12 if e.delta>0 else 1/1.12))
        self.bind('<Button-4>',lambda e:self.wheel(1.12))
        self.bind('<Button-5>',lambda e:self.wheel(1/1.12))
        self.bind('<Double-Button-1>',lambda e:self.reset())

    def set_model(self,points,links,caption='',reset=False):
        self.points,self.links,self.caption = points,links,caption
        self.detail = ''
        if reset:
            self.reset()
        else:
            self.draw()

    def reset(self):
        self.yaw,self.pitch,self.zoom,self.pan_x,self.pan_y=.45,.15,1.,0.,0.
        self.draw()

    def begin(self,e):
        self.last=(e.x,e.y)
        self.moved=False

    def orbit(self,e):
        dx,dy=e.x-self.last[0],e.y-self.last[1]
        self.yaw+=dx*.012
        self.pitch+=dy*.012
        self.last=(e.x,e.y)
        self.moved=True
        self.draw()

    def pan(self,e):
        self.pan_x+=e.x-self.last[0]
        self.pan_y+=e.y-self.last[1]
        self.last=(e.x,e.y)
        self.draw()

    def wheel(self,factor):
        self.zoom=max(.12,min(8,self.zoom*factor))
        self.draw()

    def pick(self,e):
        if getattr(self,'moved',True) or not self.projected:
            return
        i=min(range(len(self.projected)),key=lambda i:(self.projected[i][0]-e.x)**2+(self.projected[i][1]-e.y)**2)
        if math.dist(self.projected[i][:2],(e.x,e.y))<18:
            self.detail=self.points[i].detail
            self.draw()

    def draw(self):
        self.delete('all')
        w,h=max(200,self.winfo_width()),max(180,self.winfo_height())
        for x in range(0,w,40):
            self.create_line(x,0,x,h,fill='#152131')
        for y in range(0,h,40):
            self.create_line(0,y,w,y,fill='#152131')
        self.create_text(18,20,anchor='nw',text=self.caption,fill='#96aabf',font=(UI_FONT,10),width=w-36)
        self.create_text(18,h-23,anchor='sw',text=self.detail or tr('Arraste: girar  ·  Roda: zoom  ·  Botão direito: mover  ·  Duplo clique: enquadrar'),
                         fill='#87a0b7',font=(UI_FONT,9),width=w-36)
        if not self.points:
            self.create_text(w/2,h/2,text=tr('Abra uma estrutura PDB\nou escolha um exemplo.'),
                             fill='#69849e',font=(UI_FONT,16),justify='center')
            self.projected=[]
            return
        radius=max(1,max(math.sqrt(sum(v*v for v in p.xyz)) for p in self.points))
        scale=max(1,min(w-70,h-130))/(2*radius)*self.zoom
        ca,sa,cb,sb=math.cos(self.yaw),math.sin(self.yaw),math.cos(self.pitch),math.sin(self.pitch)
        projected=[]
        for p in self.points:
            x,y,z=p.xyz
            rx,rz=x*ca+z*sa,-x*sa+z*ca
            ry,rz=y*cb-rz*sb,y*sb+rz*cb
            projected.append((w/2+self.pan_x+rx*scale,h/2+self.pan_y-ry*scale,rz))
        self.projected=projected
        primitives=[((projected[a][2]+projected[b][2])/2,'line',(a,b,col,width))
                    for a,b,col,width in self.links]
        primitives += [(projected[i][2],'point',i) for i in range(len(self.points))]
        for _,kind,data in sorted(primitives,key=lambda p:p[0]):
            if kind=='line':
                a,b,col,width=data
                self.create_line(*projected[a][:2],*projected[b][:2],fill=col,width=width)
            else:
                i=data
                p=self.points[i]
                x,y,z=projected[i]
                r=max(2,min(10,p.radius*self.zoom))
                self.create_oval(x-r,y-r,x+r,y+r,fill=p.color,outline=BG,width=1)
                if p.label and self.zoom>.7:
                    self.create_text(x+9,y,text=p.label,fill=p.color,font=(MONO_FONT,9),anchor='w')

    def export_svg(self,path):
        w,h=self.winfo_width(),self.winfo_height()
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
               f'<rect width="100%" height="100%" fill="{BG}"/>']
        for item in self.find_all():
            kind=self.type(item)
            coords=self.coords(item)
            color=self.itemcget(item,'fill')
            if kind=='line':
                x1,y1,x2,y2=coords
                parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{self.itemcget(item,"width")}"/>')
            elif kind=='oval':
                x1,y1,x2,y2=coords
                parts.append(f'<ellipse cx="{(x1+x2)/2}" cy="{(y1+y2)/2}" rx="{(x2-x1)/2}" ry="{(y2-y1)/2}" fill="{color}"/>')
            elif kind=='text':
                x,y=coords
                anchor=self.itemcget(item,'anchor')
                content=escape(self.itemcget(item,'text'))
                alignment='start' if 'w' in anchor else 'end' if 'e' in anchor else 'middle'
                for j,line in enumerate(content.splitlines()):
                    parts.append(f'<text x="{x}" y="{y+13+j*16}" fill="{color}" text-anchor="{alignment}" font-family="sans-serif" font-size="12">{line}</text>')
        parts.append('</svg>')
        atomic_write(path,'\n'.join(parts))
