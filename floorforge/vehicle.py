"""Authored Kylaq representation for architectural scale studies (not OEM CAD).
Proportions: Škoda India Kylaq brochure, 3995 × 1783 × 1619 mm; WB 2566 mm.
Design reference: https://www.skoda-auto.co.in/models/kylaq/kylaq/kylaq-design
Geometry is original and shared by the offline viewer and geometry exports.
"""
import math
import numpy as np
import trimesh
from scipy.interpolate import PchipInterpolator


def parked_car(k, materials, x, y, z):
    materials.update({
        'car-pearl': {'color':'#8b916b','roughness':.24,'metallic':.65,'clearcoat':1,'clearcoat_roughness':.075},
        'car-tint': {'color':'#40535a','roughness':.12,'metallic':.15,'alpha':.48},
        'car-black': {'color':'#111618','roughness':.26,'metallic':.2},
        'car-rubber': {'color':'#212426','roughness':.88},
        'car-alloy': {'color':'#b9c0c4','roughness':.22,'metallic':.9},
        'car-brake': {'color':'#60666a','roughness':.5,'metallic':.75},
        'car-tail': {'color':'#981a20','roughness':.18,'clearcoat':1},
        'car-headlight': {'color':'#dde6eb','roughness':.1,'metallic':.55},
        'car-seat': {'color':'#383e3c','roughness':.87},
        'car-plate': {'color':'#e1e6df','roughness':.35},
    })
    start=len(k.nodes); owner='parked-car'
    def mesh(vertices, faces, mat, name=None, smooth=False):
        m=trimesh.Trimesh(vertices=vertices,faces=faces,process=True);m.fix_normals()
        return k.node(k.asset(m,smooth=smooth),mat,(x,y,z),floor=-1,role='vehicle',name=name,owner=owner)
    def rb(cx,cy,cz,size,mat,r=.015):
        return k.rb((x+cx,y+cy,z+cz),size,mat,-1,'vehicle',r,owner=owner)
    def beam(a,b,r,mat):
        k.beam(np.array(a)+(x,y,z),np.array(b)+(x,y,z),r,mat,-1,'vehicle')
    def prism(points,yy,depth,mat):
        # Convex X/Z silhouette, extruded along the vehicle's length.
        n=len(points);v=[(a,yy+d,b) for d in (-depth/2,depth/2) for a,b in points];f=[]
        for i in range(1,n-1):f.extend([(0,i+1,i),(n,n+i,n+i+1)])
        for i in range(n):j=(i+1)%n;f.extend([(i,j,n+j),(i,n+j,n+i)])
        mesh(v,f,mat)
    def loft(rings,mat,name,body=False):
        # Dense longitudinal sections and curved shoulder profiles avoid faceted toy surfaces.
        rr=np.array(rings); ys=np.linspace(rr[0,0],rr[-1,0],100 if body else 35)
        p=PchipInterpolator(rr[:,0],rr[:,1:],axis=0);v=[];f=[]
        for yy in ys:
            w,lo,hi=p(yy)
            if body:
                for wy in (-1.283,1.283):
                    d=abs(yy-wy)
                    if d<.385:lo=max(lo,.329+math.sqrt(.385**2-d*d))
            dz=hi-lo
            section=[(-.91,0),(.91,0),(.982,.04),(1,.14),(1,.68),(.98,.84),(.90,.965),(.7,1),(-.7,1),(-.90,.965),(-.98,.84),(-1,.68),(-1,.14),(-.982,.04)]
            v.extend([(a*w,yy,lo+b*dz) for a,b in section])
        n=len(section)
        for j in range(len(ys)-1):
            for i in range(n):a=j*n+i;b=j*n+(i+1)%n;f.extend([(a,b,b+n),(a,b+n,a+n)])
        for i in range(1,n-1):f.extend([(0,i+1,i),((len(ys)-1)*n,(len(ys)-1)*n+i,(len(ys)-1)*n+i+1)])
        mesh(v,f,mat,'parked-car-'+name,True)
    # Front is toward the street (negative local Y). Body length is exactly 3.995 m.
    loft([(-1.9975,.78,.28,.96),(-1.89,.84,.23,1.00),(-1.50,.882,.22,1.06),
          (-.87,.8915,.22,1.10),(.55,.885,.22,1.09),(1.52,.875,.24,1.12),(1.91,.83,.29,1.09),(1.9975,.75,.34,1.03)],'car-pearl','body',True)
    loft([(-.88,.795,1.065,1.085),(-.40,.69,1.08,1.51),(.96,.692,1.085,1.535),
          (1.48,.78,1.075,1.26),(1.63,.80,1.07,1.10)],'car-tint','glazing')
    loft([(-.40,.685,1.50,1.525),(-.25,.70,1.515,1.555),(.87,.70,1.54,1.564),(1.06,.685,1.50,1.54)],'car-pearl','roof')
    # Dark interior gives the glazing real depth: dashboard, console, seats and headrests.
    rb(0,-.64,1.065,(1.46,.35,.14),'car-black',.035)
    rb(0,.39,.79,(.23,1.43,.22),'car-black',.04)
    for xx in (-.40,.40):
        for yy in (-.01,.89):
            rb(xx,yy,.81,(.49,.49,.16),'car-seat',.052)
            rb(xx,yy+.19,1.055,(.49,.14,.50),'car-seat',.052)
            rb(xx,yy+.20,1.36,(.25,.12,.16),'car-seat',.04)
    rb(0,-.47,1.17,(.27,.028,.145),'car-black',.013)
    # Right-hand-drive steering wheel, visible through the windscreen.
    for i in range(40):
        a=2*math.pi*i/40;b=2*math.pi*(i+1)/40
        beam((.40+.14*math.cos(a),-.36,1.15+.14*math.sin(a)),(.40+.14*math.cos(b),-.36,1.15+.14*math.sin(b)),.012,'car-black')
    beam((.4,-.36,1.15),(.4,-.36,1.02),.012,'car-black')
    for xx in (-.36,.36):beam((xx-.22,-.827,1.124),(xx+.18,-.788,1.154),.006,'car-black')
    # Broad painted A/C pillars and gloss B pillars, side glazing and door shut lines.
    for side in (-1,1):
        beam((side*.792,-.86,1.09),(side*.687,-.39,1.518),.038,'car-pearl')
        beam((side*.80,1.60,1.095),(side*.694,.98,1.529),.065,'car-pearl')
        beam((side*.837,.22,1.08),(side*.700,.22,1.55),.043,'car-black')
        beam((side*.835,.99,1.09),(side*.711,.79,1.54),.016,'car-black')
        beam((side*.818,-.83,1.073),(side*.842,1.48,1.083),.012,'car-alloy')
        # Sill cladding and a crisp shoulder crease in body colour.
        rb(side*.861,0,.27,(.045,1.70,.16),'car-rubber',.018)
        beam((side*.871,-.86,.94),(side*.876,1.06,.96),.010,'car-pearl')
        for yy in (-.79,.22,1.0):
            beam((side*.889,yy,.39),(side*.889,yy,1.05),.0035,'car-black')
        for yy in (-.02,.89):
            rb(side*.89,yy,.98,(.027,.18,.039),'car-pearl',.012)
            rb(side*.907,yy,.973,(.011,.13,.009),'car-black',.003)
        beam((side*.795,-.68,1.09),(side*.929,-.64,1.12),.024,'car-black')
        rb(side*.927,-.66,1.16,(.155,.205,.104),'car-black',.033)
        rb(side*.934,-.67,1.189,(.15,.198,.042),'car-pearl',.013)
        rb(side*.94,-.760,1.157,(.11,.008,.012),'car-headlight',.003)
        # Raised satin roof rails with black mounting feet.
        for yy in (-.19,.85):rb(side*.57,yy,1.576,(.055,.11,.04),'car-black',.012)
        beam((side*.57,-.27,1.597),(side*.57,.92,1.609),.010,'car-alloy')
        # Sculpted arch trim: open wheel wells, not wheels pasted onto a solid side slab.
        for wy in (-1.283,1.283):
            verts=[];faces=[]
            for a in np.linspace(-.18,math.pi+.18,49):
                for xx,r in [(side*.887,.387),(side*.908,.391),(side*.906,.438),(side*.883,.447)]:
                    verts.append((xx,wy+r*math.cos(a),.329+r*math.sin(a)))
            for j in range(48):
                for i in range(3):a=j*4+i;faces.extend([(a,a+1,a+5),(a,a+5,a+4)])
            mesh(verts,faces,'car-rubber',smooth=True)
            # Revolved rounded tyre sidewall and tread; axle along X.
            profile=[(-.104,.231),(-.107,.275),(-.098,.316),(-.076,.329),(.076,.329),(.098,.316),(.107,.275),(.104,.231)]
            vv=[];ff=[];xc=side*.790
            for angle in np.linspace(0,2*math.pi,81)[:-1]:
                vv.extend([(xc+ax,wy+r*math.cos(angle),.329+r*math.sin(angle)) for ax,r in profile])
            for j in range(80):
                for i in range(8):a=j*8+i;b=j*8+(i+1)%8;c=((j+1)%80)*8+(i+1)%8;d=((j+1)%80)*8+i;ff.extend([(a,b,c),(a,c,d)])
            mesh(vv,ff,'car-rubber',smooth=True)
            # Detailed 17-inch machined split-spoke wheels with brake disc and five lugs.
            for xx,r,dep,mat in [(side*.891,.218,.012,'car-black'),(side*.895,.194,.013,'car-brake'),(side*.907,.07,.02,'car-alloy')]:
                k.cylinder((x+xx,y+wy,z+.329),r,dep,mat,-1,'vehicle',rot=(0,math.pi/2,0))
            for rad in (.212,.221):
                for a in range(80):
                    aa=2*math.pi*a/80;bb=2*math.pi*(a+1)/80
                    beam((side*.914,wy+rad*math.cos(aa),.329+rad*math.sin(aa)),(side*.914,wy+rad*math.cos(bb),.329+rad*math.sin(bb)),.004,'car-alloy')
            for a in range(5):
                aa=2*math.pi*a/5
                for delta in (-.16,.16):
                    beam((side*.918,wy+.068*math.cos(aa),.329+.068*math.sin(aa)),(side*.918,wy+.206*math.cos(aa+delta),.329+.206*math.sin(aa+delta)),.013,'car-alloy')
                k.cylinder((x+side*.925,y+wy+.038*math.cos(aa),z+.329+.038*math.sin(aa)),.007,.012,'car-black',-1,'vehicle',rot=(0,math.pi/2,0))
            # Fine tread ribs visible on the tyre crown.
            for a in range(64):
                aa=2*math.pi*a/64
                beam((xc-.055,wy+.330*math.cos(aa),.329+.330*math.sin(aa)),(xc+.055,wy+.330*math.cos(aa+.03),.329+.330*math.sin(aa+.03)),.002,'car-black')
    # Kylaq grille outline, vertical ribs, split DRLs and lower projector clusters.
    prism([(-.52,.89),(-.45,.705),(.45,.705),(.52,.89),(.40,.936),(-.40,.936)],-2.008,.025,'car-black')
    for xx in np.linspace(-.43,.43,17):rb(xx,-2.026,.81,(.016,.013,.17),'car-black',.006)
    rb(0,-2.020,.40,(1.40,.08,.15),'car-rubber',.025)
    rb(0,-2.065,.32,(1.06,.023,.065),'car-alloy',.015)
    rb(0,-2.021,.535,(.86,.035,.15),'car-black',.017)
    for xx in np.linspace(-.39,.39,15):rb(xx,-2.044,.533,(.012,.012,.12),'car-rubber',.003)
    for side in (-1,1):
        rb(side*.655,-2.025,.945,(.32,.065,.053),'car-black',.012)
        rb(side*.655,-2.066,.958,(.285,.012,.014),'car-headlight',.004)
        rb(side*.656,-2.026,.72,(.24,.055,.105),'car-black',.012)
        for xx in (.615,.711):rb(side*xx,-2.058,.737,(.071,.012,.045),'car-headlight',.010)
        # Hood creases converge towards the emblem.
        beam((side*.37,-1.85,1.018),(side*.51,-.91,1.091),.006,'car-pearl')
    k.cylinder((x,y-2.022,z+.991),.023,.008,'car-alloy',-1,'vehicle',rot=(math.pi/2,0,0))
    # Rear spoiler, rear wiper, black wordmark band, T-signature lamps and diffuser.
    rb(0,1.21,1.489,(1.39,.29,.062),'car-pearl',.02)
    rb(0,1.357,1.476,(.59,.02,.014),'car-tail',.004)
    beam((-.12,1.591,1.126),(.29,1.545,1.174),.008,'car-black')
    rb(0,1.993,.967,(1.27,.029,.086),'car-black',.01)
    rb(0,1.982,.40,(1.51,.055,.19),'car-rubber',.025)
    rb(0,2.001,.333,(1.07,.018,.10),'car-alloy',.018)
    for side in (-1,1):
        rb(side*.633,1.965,1.005,(.31,.072,.096),'car-tail',.018)
        rb(side*.64,2.007,1.025,(.265,.009,.017),'car-tail',.004)
        rb(side*.65,2.009,.982,(.018,.008,.08),'car-tail',.003)
        rb(side*.63,1.991,.465,(.20,.015,.033),'car-tail',.006)
    # Small model plates and spaced rear wordmark made of original vector strokes.
    glyphs={'S':[(1,1,0,1),(0,1,0,.5),(0,.5,1,.5),(1,.5,1,0),(1,0,0,0)],'K':[(0,0,0,1),(0,.5,1,1),(0,.5,1,0)],'O':[(0,0,0,1),(0,1,1,1),(1,1,1,0),(1,0,0,0)],'D':[(0,0,0,1),(0,1,.7,1),(.7,1,1,.8),(1,.8,1,.2),(1,.2,.7,0),(.7,0,0,0)],'A':[(0,0,.5,1),(.5,1,1,0),(.25,.45,.75,.45)],'Y':[(0,1,.5,.5),(1,1,.5,.5),(.5,.5,.5,0)],'L':[(0,1,0,0),(0,0,1,0)],'Q':[(0,0,0,1),(0,1,1,1),(1,1,1,0),(1,0,0,0),(.6,.3,1.2,-.1)]}
    def lettering(word,yy,zz,height,mat):
        step=height*.85;origin=-len(word)*step/2
        for i,ch in enumerate(word):
            for a,b,c,d in glyphs[ch]:beam((origin+i*step+a*height*.6,yy,zz+b*height),(origin+i*step+c*height*.6,yy,zz+d*height),.0016,mat)
    lettering('SKODA',2.012,.948,.039,'car-alloy')
    for yy in (-2.07,2.027):
        rb(0,yy,.635,(.36,.012,.085),'car-plate',.006)
        lettering('KYLAQ',yy+(-.009 if yy<0 else .009),.610,.046,'car-black')
    for n in k.nodes[start:]:n['owner']=owner
