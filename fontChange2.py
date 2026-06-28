#!/usr/bin/env python3
"""
Create comprehensive consonant-vowel composite ligatures with custom positioning AND SCALING.

This script creates composites for all consonants where vowels are:
- Positioned according to consonant shape
- Scaled down (0.6x default) to fit in empty spaces
- Combined into single glyphs

Positioning rules per consonant:
- b: vowel above (centered, full height)
- d: vowel below (centered)
- f: vowel upper right corner (shrunk)
- l: vowel upper left corner (shrunk)
- m: vowel upper right region (shrunk)
- n: 'a' on top (full size), other vowels bottom right (shrunk)
- p: vowel upper right corner (shrunk)
- s,t,ʁ,ɾ,ʃ,ʒ: vowel upper right part (shrunk)
- ʎ: vowel middle right space (shrunk, between the character's curve)
- z: vowel lower space (shrunk, in the half-circle space)

Usage:
    python3 fontChange2.py input_font.ttf output_font.ttf
"""

import sys
import array
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.feaLib.builder import Builder
from io import StringIO

# Define your consonants and vowels
CONSONANTS = ['b', 'd', 'f', 'l', 'm', 'n', 'p', 's', 't', 'ʁ', 'ɾ', 'ʃ', 'ʒ', 'ʎ', 'z']
VOWELS = ['a', 'e', 'i', 'o', 'u', 'ø', 'œ', 'ɑ̃', 'œ̃', 'ɔ̃']

# Positioning rules: (x_offset, y_offset, scale)
# x: positive = right, negative = left
# y: positive = up, negative = down
# scale: 1.0 = full size, 0.6 = 60% size

POSITIONING_RULES = {
    'b': {
        'default': {'x': 0, 'y': 120, 'scale': 0.65}  # vowel above, centered
    },
    'd': {
        'default': {'x': 0, 'y': -120, 'scale': 0.65}  # vowel below, centered
    },
    'f': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right corner
    },
    'l': {
        'default': {'x': -180, 'y': 150, 'scale': 0.65}  # upper left corner
    },
    'm': {
        'default': {'x': 150, 'y': 150, 'scale': 0.65}  # upper right region
    },
    'n': {
        'a': {'x': 0, 'y': 120, 'scale': 1.0},         # 'a' on top, full size
        'default': {'x': 150, 'y': -100, 'scale': 0.65}  # other vowels bottom right
    },
    'p': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right corner
    },
    's': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    't': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    'ʁ': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    'ɾ': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    'ʃ': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    'ʒ': {
        'default': {'x': 180, 'y': 150, 'scale': 0.65}  # upper right part
    },
    'ʎ': {
        'default': {'x': 150, 'y': 0, 'scale': 0.65}  # middle right space (between curve)
    },
    'z': {
        'default': {'x': 0, 'y': -120, 'scale': 0.65}  # lower space (in half-circle)
    },
}

def apply_transform(component, x_offset, y_offset, scale):
    """
    Apply positioning AND SCALING to component using transformation matrix.
    
    TrueType composite glyphs support 2D affine transformations:
    transform = [scaleX, scaleXY, scaleYX, scaleY, translateX, translateY]
    
    For uniform scaling: [scale, 0, 0, scale, x, y]
    """
    component.flags = 0x0004  # ARG_1_AND_2_ARE_WORDS
    
    if scale == 1.0:
        # No scaling, just position
        component.x = x_offset
        component.y = y_offset
    else:
        # Apply scaling transformation
        # Convert scale to F2Dot14 format (1.14 fixed point used in TrueType)
        # This is scale * 2^14 = scale * 16384
        scale_fixed = int(scale * 16384)
        
        # Set the transformation matrix
        # Format: [xx, xy, yx, yy, dx, dy]
        # For uniform scale: [scale_fixed, 0, 0, scale_fixed, x, y]
        component.transform = (scale_fixed, 0, 0, scale_fixed, x_offset, y_offset)

def create_cv_ligatures(input_path, output_path):
    """
    Create all consonant-vowel composite ligatures with scaling.
    """
    print(f"Loading font: {input_path}")
    font = TTFont(input_path)
    
    glyf_table = font['glyf']
    hmtx = font['hmtx']
    
    # Track created ligatures and feature code
    created_ligatures = []
    feature_rules = []
    
    print(f"\nCreating composite ligatures...")
    print(f"Consonants: {len(CONSONANTS)}")
    print(f"Vowels: {len(VOWELS)}")
    print(f"Expected ligatures: {len(CONSONANTS) * len(VOWELS)}")
    print()
    
    # Create composite for each consonant-vowel pair
    for consonant in CONSONANTS:
        # Check if consonant exists in font
        if consonant not in glyf_table:
            print(f"⚠ Warning: Consonant '{consonant}' not in font, skipping")
            continue
        
        consonant_bounds = get_glyph_bounds(glyf_table[consonant])
        consonant_width = consonant_bounds['xMax'] - consonant_bounds['xMin']
        consonant_height = consonant_bounds['yMax'] - consonant_bounds['yMin']
        
        for vowel in VOWELS:
            # Check if vowel exists in font
            if vowel not in glyf_table:
                print(f"⚠ Warning: Vowel '{vowel}' not in font, skipping")
                continue
            
            # Get positioning rule for this vowel/consonant pair
            if consonant in POSITIONING_RULES:
                rules = POSITIONING_RULES[consonant]
                # Check if there's a specific rule for this vowel
                if vowel in rules:
                    rule = rules[vowel]
                else:
                    rule = rules.get('default', {'x': 0, 'y': 0, 'scale': 0.65})
            else:
                rule = {'x': 0, 'y': 0, 'scale': 0.65}
            
            x_offset = rule['x']
            y_offset = rule['y']
            scale = rule['scale']
            
            # Create composite glyph name
            glyph_name = f"{consonant}{vowel}_compound"
            
            # Create composite glyph
            composite = Glyph()
            composite.numberOfContours = -1  # -1 = composite
            
            # Add consonant as first component (baseline)
            comp_c = GlyphComponent()
            comp_c.glyphName = consonant
            comp_c.x = 0
            comp_c.y = 0
            comp_c.flags = 0x0004
            
            # Add vowel as second component (positioned AND SCALED)
            comp_v = GlyphComponent()
            comp_v.glyphName = vowel
            apply_transform(comp_v, x_offset, y_offset, scale)
            
            composite.components = [comp_c, comp_v]
            
            # Add to glyf table
            glyf_table[glyph_name] = composite
            
            # Calculate metrics for composite
            # Width is roughly consonant width + some padding
            total_width = int(consonant_width * 1.3)
            hmtx.metrics[glyph_name] = (total_width, consonant_bounds['xMin'])
            
            # Track for feature code
            created_ligatures.append((consonant, vowel, glyph_name))
            feature_rules.append(f"    sub {consonant} {vowel} by {glyph_name};")
    
    print(f"✓ Created {len(created_ligatures)} composite ligatures")
    
    # Generate feature code
    print(f"\nGenerating substitution rules...")
    feature_code = """languagesystem DFLT dflt;
languagesystem latn dflt;

feature liga {
"""
    feature_code += "\n".join(feature_rules)
    feature_code += "\n} liga;\n"
    
    # Add feature code to font
    print(f"Adding {len(feature_rules)} substitution rules to font...")
    try:
        feature_file = StringIO(feature_code)
        builder = Builder(font, feature_file)
        builder.build()
        print(f"✓ Feature code compiled successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not add feature code: {e}")
        print(f"  Font can still be used but substitutions won't work")
    
    # Save font
    print(f"\nSaving font: {output_path}")
    try:
        font.save(output_path)
        print(f"✓ Font saved successfully!")
        print(f"\nFont now contains:")
        print(f"  - {len(created_ligatures)} consonant-vowel composites")
        print(f"  - All vowels SCALED according to rules (0.65x by default)")
        print(f"  - Full substitution rules (GSUB table)")
        print(f"  - All original glyphs preserved")
        return True
    except Exception as e:
        print(f"✗ Error saving font: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_glyph_bounds(glyph):
    """Get bounding box of a glyph."""
    if hasattr(glyph, 'xMax') and hasattr(glyph, 'yMax'):
        return {
            'xMin': glyph.xMin if hasattr(glyph, 'xMin') else 0,
            'yMin': glyph.yMin if hasattr(glyph, 'yMin') else 0,
            'xMax': glyph.xMax if hasattr(glyph, 'xMax') else 0,
            'yMax': glyph.yMax if hasattr(glyph, 'yMax') else 0,
        }
    return {'xMin': 0, 'yMin': 0, 'xMax': 100, 'yMax': 100}

def main():
    if len(sys.argv) < 2:
        print("Undinian Consonant-Vowel Ligature Generator (WITH SCALING)")
        print("\nUsage:")
        print("  python3 fontChange2.py <input.ttf> [output.ttf]")
        print("\nExamples:")
        print("  python3 fontChange2.py Undinian-Regular-complete.ttf")
        print("    -> creates: Undinian-Regular-complete-allcv.ttf (with scaled vowels)")
        print()
        print("SCALE VALUES IN POSITIONING_RULES:")
        print("  1.0 = full size (100%)")
        print("  0.65 = 65% size")
        print("  0.5 = 50% size (half)")
        print("  0.3 = 30% size (very small)")
        print()
        print("Change the 'scale' values in POSITIONING_RULES to control vowel size!")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = input_path.replace('.ttf', '-allcv.ttf')
    
    success = create_cv_ligatures(input_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()