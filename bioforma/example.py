"""Artificial geometry for viewer testing, not a measured protein structure."""
import math


def demo_pdb():
    rows=['HEADER    BIOFORMA GEOMETRIC DEMO',
          'REMARK    ARTIFICIAL COORDINATES. NOT A REAL OR PREDICTED PROTEIN.']
    for i in range(32):
        angle=i*math.radians(100)
        x,y,z=2.3*math.cos(angle),2.3*math.sin(angle),1.5*i
        rows.append(f'ATOM  {i+1:5d}  CA  ALA A{i+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{1:6.2f}{0:6.2f}          {"C":>2s}')
    return '\n'.join(rows+['END',''])
