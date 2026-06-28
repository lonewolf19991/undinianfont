
#!/usr/bin/env python3
"""
Robust CV abugida generator.

Edit POSITIONING_RULES to tweak x/y/scale.
Usage:
    python3 abugida_generator.py input.ttf output.ttf
"""
import sys, traceback
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

CONSONANTS=['b','d','f','l','m','n','p','s','t','ʁ','ɾ','ʃ','ʒ','ʎ','z']
VOWELS=['a','e','i','o','u','v','c','w','x','q']

POSITIONING_RULES={
 'b':{'default':{'x':200,'y':400,'scale':0.45}},
 'd':{'default':{'x':0,'y':-60,'scale':0.55}},
 'f':{'default':{'x':540,'y':600,'scale':0.45}},
 'l':{'default':{'x':50,'y':250,'scale':0.55}},
 'm':{'default':{'x':480,'y':350,'scale':0.55}},
 'n':{'a':{'x':0,'y':750,'scale':0.65}, 'default':{'x':500,'y':20,'scale':0.55}},
 'p':{'default':{'x':180,'y':150,'scale':0.65}},
 's':{'default':{'x':500,'y':300,'scale':0.55}},
 't':{'default':{'x':180,'y':150,'scale':0.65}},
 'ʁ':{'default':{'x':180,'y':150,'scale':0.65}},
 'ɾ':{'default':{'x':180,'y':150,'scale':0.65}},
 'ʃ':{'default':{'x':180,'y':150,'scale':0.65}},
 'ʒ':{'default':{'x':180,'y':150,'scale':0.65}},
 'ʎ':{'default':{'x':150,'y':0,'scale':0.65}},
 'z':{'default':{'x':0,'y':-120,'scale':0.65}},
}

def cmap_lookup(font):
    cmap={}
    for t in font["cmap"].tables:
        if t.isUnicode():
            cmap.update(t.cmap)
    out={}
    for cp,name in cmap.items():
        out[chr(cp)]=name
    return out

def component(name,x,y,scale):
    c=GlyphComponent()
    c.glyphName=name
    c.flags=0x0004
    c.x=x;c.y=y
    if scale!=1.0:
        c.transform=((scale,0),(0,scale))
    return c

def main(inp,out):
    font=TTFont(inp)
    glyf=font["glyf"];hmtx=font["hmtx"]
    mapping=cmap_lookup(font)
    rules=[]
    made=0
    for cons in CONSONANTS:
        cg=mapping.get(cons)
        if not cg:
            print("Warning missing consonant",cons);continue
        for vow in VOWELS:
            vg=mapping.get(vow)
            if not vg:
                print("Warning missing vowel",vow);continue
            r=POSITIONING_RULES.get(cons,{})
            p=r.get(vow,r.get("default",{"x":0,"y":0,"scale":0.65}))
            gname=f"{cg}_{vg}.cv"
            g=Glyph();g.numberOfContours=-1
            g.components=[component(cg,0,0,1.0),component(vg,p["x"],p["y"],p["scale"])]
            glyf[gname]=g
            aw,lsb=hmtx[cg]
            hmtx[gname]=(aw,lsb)
            rules.append(f"sub {cg} {vg} by {gname};")
            made+=1
    feat="languagesystem DFLT dflt;\nfeature liga {\n"+"\n".join(rules)+"\n} liga;"
    try:
        addOpenTypeFeaturesFromString(font,feat)
    except Exception as e:
        print("Feature compile warning:",e)
    font.save(out)
    print(f"Created {made} composites.")
if __name__=="__main__":
    if len(sys.argv)<3:
        print(__doc__);sys.exit(1)
    try:
        main(sys.argv[1],sys.argv[2])
    except Exception:
        traceback.print_exc();sys.exit(2)
