"""Finish-only detailing for the authored upper-floor terrace composition."""
import numpy as np
from shapely.geometry import Polygon


def upper_floor_finishes(k, building, height):
    rooms={r['id']:r for r in building['spaces']}
    if not {'u-studio-terrace','u-bedroom-balcony','u-office','u-lobby'} <= rooms.keys():
        return
    z=height;f=1;owner='upper-front-composition'
    x0,y0,x1,y1=Polygon(np.array(rooms['u-office']['clear'])/1000).bounds
    lx0,ly0,lx1,ly1=Polygon(np.array(rooms['u-lobby']['clear'])/1000).bounds
    # A single shallow head unifies the two setback rooms; most of the deck stays open sky.
    k.rect((x0-.15,y0-.47,z+2.81,lx1+.15,y0-.10,z+2.94),'roof',f,'canopy',owner+'/head',owner)
    k.rect((x0-.10,y0-.42,z+2.785,lx1+.10,y0-.12,z+2.81),'oak',f,'soffit',owner+'/timber-reveal',owner)
    k.rect((x0-.15,y0-.475,z+2.81,lx1+.15,y0-.45,z+2.86),'frame',f,'fascia',owner+'/shadow-line',owner)
    # Stone at the end and a narrow timber reveal between aligned glazing bays.
    k.rect((x0-.15,y0-.18,z+.03,x0+.20,y0-.15,z+2.81),'facade-limestone',f,'wall-panel',owner+'/stone-return',owner)
    for i,xx in enumerate(np.arange(x1-.26,lx0-.03,.085)):
        k.rect((xx,y0-.195,z+.04,xx+.04,y0-.15,z+2.76),'oak',f,'wall-panel',owner+f'/timber-fin-{i}',owner)
    for i,xx in enumerate(((x0+x1)/2,(lx0+lx1)/2)):
        k.cylinder((xx,y0-.29,z+2.775),.045,.012,'lamp',f,'fixture')
        k.light((xx,y0-.30,z+2.73),10,kind='soffit')
    # A modest outdoor bench hugs the broad north return, leaving the lobby approach clear.
    owner='u-terrace-front/lounge-bench'
    k.rect((14.25,2.1,z+.03,14.8,3.9,z+.35),'oak',f,'outdoor-furniture',owner+'/base',owner)
    k.rb((14.48,3,z+.405),(.66,1.88,.13),'fabric',f,'outdoor-furniture',.035,owner=owner)
    k.rb((14.76,3,z+.67),(.13,1.88,.48),'fabric',f,'outdoor-furniture',.035,owner=owner)
    footprint=[[14.15,2.06],[14.825,2.06],[14.825,3.94],[14.15,3.94]]
    k.colliders.append({'id':owner,'floor':f,'kind':'furniture','polygon':footprint})
    k.furniture.append({'id':owner,'room_id':'u-terrace-front','floor':f,'kind':'outdoor-bench','footprint':footprint})
    # Append upper planting last so existing ground-level plant instances retain their seeds.
    for x,y,h in [(14.42,.68,1.15),(14.42,4.8,1.45),(1.0,13.5,1.2)]:
        k.plant(x,y,z+.022,'strelitzia',height=h,f=f,pot=(.23,.43,'planter'))
        k.colliders.append({'id':f'upper-pot-{x}-{y}','floor':f,'kind':'landscape','polygon':[[x-.24,y-.24],[x+.24,y-.24],[x+.24,y+.24],[x-.24,y+.24]]})
