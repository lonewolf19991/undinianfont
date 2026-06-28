#!/usr/bin/env python3
"""
Robust CV abugida generator with CONSONANT positioning control.

Edit CONSONANT_POSITIONING to control consonant size/position.
Edit POSITIONING_RULES to control vowel size/position.

Usage:
    python3 abugida_generator.py input.ttf output.ttf
"""
import sys, traceback
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

CONSONANTS=['b','d','f','l','m','n','p','s','t','g','r','h','j','y','z','k']
VOWELS=['a','e','i','o','u','v','c','w','x','q']

# CONSONANT POSITIONING: control size and position of base consonants
# x: horizontal offset (positive=right, negative=left)
# y: vertical offset (positive=up, negative=down)
# scale: 1.0=full size, 0.5=half size, etc.
CONSONANT_POSITIONING = {
    'b': {'x': 0, 'y': 0, 'scale': 0.50},
    'd': {'x': 0, 'y': 0, 'scale': 1.0},
    'f': {'x': 0, 'y': 0, 'scale': 1.0},
    'l': {'x': 0, 'y': 0, 'scale': 1.0},
    'm': {'x': 0, 'y': 0, 'scale': 1.0},
    'n': {'x': 0, 'y': 0, 'scale': 1.0},
    'p': {'x': 0, 'y': 0, 'scale': 1.0},
    's': {'x': 0, 'y': 0, 'scale': 1.0},
    't': {'x': 0, 'y': 0, 'scale': 1.0},
    'g': {'x': 0, 'y': 0, 'scale': 1.0},
    'r': {'x': 0, 'y': 0, 'scale': 1.0},
    'h': {'x': 0, 'y': 0, 'scale': 1.0},
    'j': {'x': 0, 'y': 0, 'scale': 1.0},
    'y': {'x': 0, 'y': 0, 'scale': 1.0},
    'z': {'x': 0, 'y': 0, 'scale': 1.0},
    'k': {'x': 0, 'y': 0, 'scale': 1.0},
}

# VOWEL POSITIONING: control size and position of vowels
# x: horizontal offset
# y: vertical offset
# scale: vowel size (typically 0.4-0.65)
POSITIONING_RULES = {
    'b': {'default': {'x': 200, 'y': 400, 'scale': 0.45}},
    'd': {'default': {'x': 0, 'y': -60, 'scale': 0.55}},
    'f': {'default': {'x': 540, 'y': 600, 'scale': 0.45}},
    'l': {'default': {'x': 50, 'y': 250, 'scale': 0.55}},
    'm': {'default': {'x': 480, 'y': 350, 'scale': 0.55}},
    'n': {'a': {'x': 0, 'y': 750, 'scale': 0.65}, 'default': {'x': 500, 'y': 20, 'scale': 0.55}},
    'p': {'default': {'x': 550, 'y': 450, 'scale': 0.55}},
    's': {'default': {'x': 500, 'y': 300, 'scale': 0.55}},
    't': {'default': {'x': 500, 'y': 700, 'scale': 0.40}},
    'g': {'default': {'x': 550, 'y': 350, 'scale': 0.45}},
    'r': {'default': {'x': 450, 'y': 250, 'scale': 0.45}},
    'h': {'default': {'x': 300, 'y': 500, 'scale': 0.40}},
    'j': {'default': {'x': 450, 'y': 50, 'scale': 0.45}},
    'y': {'default': {'x': 150, 'y': 0, 'scale': 0.65}},
    'z': {'default': {'x': 0, 'y': -120, 'scale': 0.65}},
}

def cmap_lookup(font):
    """Extract character to glyph name mapping from font."""
    cmap = {}
    for t in font["cmap"].tables:
        if t.isUnicode():
            cmap.update(t.cmap)
    out = {}
    for cp, name in cmap.items():
        out[chr(cp)] = name
    return out

def component(name, x, y, scale):
    """Create a GlyphComponent with positioning and scaling."""
    c = GlyphComponent()
    c.glyphName = name
    c.flags = 0x0004
    c.x = x
    c.y = y
    if scale != 1.0:
        c.transform = ((scale, 0), (0, scale))
    return c

def main(inp, out):
    """Create CV ligatures with consonant and vowel positioning."""
    font = TTFont(inp)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    mapping = cmap_lookup(font)
    rules = []
    made = 0
    
    for cons in CONSONANTS:
        cg = mapping.get(cons)
        if not cg:
            print("Warning missing consonant", cons)
            continue
        
        # Get consonant positioning rules
        cons_pos = CONSONANT_POSITIONING.get(cons, {'x': 0, 'y': 0, 'scale': 1.0})
        cons_x = cons_pos['x']
        cons_y = cons_pos['y']
        cons_scale = cons_pos['scale']
        
        for vow in VOWELS:
            vg = mapping.get(vow)
            if not vg:
                print("Warning missing vowel", vow)
                continue
            
            # Get vowel positioning rules
            r = POSITIONING_RULES.get(cons, {})
            p = r.get(vow, r.get("default", {"x": 0, "y": 0, "scale": 0.65}))
            
            # Create composite glyph
            gname = f"{cg}_{vg}.cv"
            g = Glyph()
            g.numberOfContours = -1
            
            # Add consonant (with positioning) and vowel (with positioning)
            g.components = [
                component(cg, cons_x, cons_y, cons_scale),
                component(vg, p["x"], p["y"], p["scale"])
            ]
            
            glyf[gname] = g
            aw, lsb = hmtx[cg]
            hmtx[gname] = (aw, lsb)
            rules.append(f"sub {cg} {vg} by {gname};")
            made += 1
    
    # Compile OpenType features
    feat = "languagesystem DFLT dflt;\nfeature liga {\n" + "\n".join(rules) + "\n} liga;"
    try:
        addOpenTypeFeaturesFromString(font, feat)
    except Exception as e:
        print("Feature compile warning:", e)
    
    font.save(out)
    print(f"Created {made} composites.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    try:
        main(sys.argv[1], sys.argv[2])
    except Exception:
        traceback.print_exc()
        sys.exit(2)