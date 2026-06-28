#!/usr/bin/env python3
"""
Create a composite ligature: S + A (elevated)
S comes first at baseline, A is raised into the empty space above S.

Usage:
    python3 create_sa_ligature.py input_font.ttf output_font.ttf
    
Example:
    python3 create_sa_ligature.py Undinian-Regular-complete.ttf Undinian-SA-Ligature.ttf
"""

import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.feaLib.builder import Builder
from io import StringIO

def get_glyph_bounds(glyph):
    """Get the bounding box of a glyph"""
    if hasattr(glyph, 'xMax') and hasattr(glyph, 'yMax'):
        return {
            'xMin': glyph.xMin,
            'yMin': glyph.yMin,
            'xMax': glyph.xMax,
            'yMax': glyph.yMax,
        }
    return None

def create_sa_ligature(input_path, output_path, elevation=None):
    """
    Create S + A composite glyph with A elevated
    
    Args:
        input_path: Path to input TTF font
        output_path: Path to output TTF font
        elevation: How much to raise A (in font units). 
                   If None, auto-calculate based on S height
    """
    
    print(f"Loading font: {input_path}")
    font = TTFont(input_path)
    
    # Get the glyph table
    glyf_table = font['glyf']
    hmtx = font['hmtx']
    
    # Get glyphs for S and A
    print("Analyzing S and A glyphs...")
    
    if 's' not in glyf_table:
        print("ERROR: Font doesn't have lowercase 's'")
        return False
    
    if 'a' not in glyf_table:
        print("ERROR: Font doesn't have lowercase 'a'")
        return False
    
    s_glyph = glyf_table['s']
    a_glyph = glyf_table['a']
    
    s_bounds = get_glyph_bounds(s_glyph)
    a_bounds = get_glyph_bounds(a_glyph)
    
    print(f"\nGlyph bounds:")
    print(f"  S: xMin={s_bounds['xMin']}, yMin={s_bounds['yMin']}, "
          f"xMax={s_bounds['xMax']}, yMax={s_bounds['yMax']}")
    print(f"  A: xMin={a_bounds['xMin']}, yMin={a_bounds['yMin']}, "
          f"xMax={a_bounds['xMax']}, yMax={a_bounds['yMax']}")
    
    # Auto-calculate elevation if not specified
    if elevation is None:
        # Raise A so its bottom is at the top of S (or higher)
        # This puts A in the empty space above S
        s_height = s_bounds['yMax'] - s_bounds['yMin']
        a_height = a_bounds['yMax'] - a_bounds['yMin']
        
        # Elevation: move A up by S's full height minus some overlap
        # Using 70% of S height to raise A nicely into the space
        elevation = int(s_height * 0.7)
    
    print(f"\nComposite glyph settings:")
    print(f"  A will be raised by: {elevation} units")
    
    # Create new composite glyph
    # A composite glyph is made up of component references with transformations
    
    from fontTools.ttLib.tables._g_l_y_f import GlyphComponent
    
    composite_glyph = Glyph()
    composite_glyph.numberOfContours = -1  # -1 means composite glyph
    
    # Create components using proper GlyphComponent objects
    comp_s = GlyphComponent()
    comp_s.glyphName = 's'
    comp_s.x = 0
    comp_s.y = 0
    comp_s.flags = 0x0004  # ARG_1_AND_2_ARE_WORDS
    
    comp_a = GlyphComponent()
    comp_a.glyphName = 'a'
    comp_a.x = 0  # No horizontal offset (overlaps with S)
    comp_a.y = elevation  # Vertical offset (raised)
    comp_a.flags = 0x0004  # ARG_1_AND_2_ARE_WORDS
    
    composite_glyph.components = [comp_s, comp_a]
    
    # Calculate bounds of the composite
    # Width: S's width + A's width (or less if overlapping)
    s_width = s_bounds['xMax'] - s_bounds['xMin']
    a_width = a_bounds['xMax'] - a_bounds['xMin']
    
    # Total width (mostly S's width since A overlaps)
    total_width = int(s_width * 1.3)  # Add some spacing
    
    # Add the composite glyph to font
    print(f"\nCreating composite glyph 'sa_compound'...")
    glyf_table['sa_compound'] = composite_glyph
    
    # Add metrics (width) for the composite glyph
    hmtx.metrics['sa_compound'] = (total_width, s_bounds['xMin'])
    
    print(f"  Composite width: {total_width}")
    
    # Now add the substitution rule using feature code
    # This makes "s a" (when typed) become "sa_compound"
    
    print(f"\nAdding substitution rule: s + a -> sa_compound")
    
    feature_code = """
languagesystem DFLT dflt;
languagesystem latn dflt;

feature liga {
    sub s a by sa_compound;
} liga;
"""
    
    print(f"Feature code:\n{feature_code}")
    
    # Write feature file
    feature_file = StringIO(feature_code)
    
    try:
        # Add the feature to the font
        builder = Builder(font, feature_file)
        builder.build()
        print("✓ Feature code compiled and added to font")
    except Exception as e:
        print(f"WARNING: Could not add feature code: {e}")
        print("  (Font can still be used, but substitution won't work)")
    
    # Save the modified font
    print(f"\nSaving font: {output_path}")
    font.save(output_path)
    print(f"✓ Font saved successfully!")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Create S + A Composite Ligature")
        print("\nUsage:")
        print("  python3 create_sa_ligature.py <input.ttf> [output.ttf] [elevation]")
        print("\nExamples:")
        print("  python3 create_sa_ligature.py Undinian-Regular-complete.ttf")
        print("    -> creates: Undinian-Regular-complete-sa.ttf with auto elevation")
        print()
        print("  python3 create_sa_ligature.py input.ttf output.ttf 100")
        print("    -> raises A by 100 font units")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = input_path.replace('.ttf', '-sa.ttf')
    
    elevation = None
    if len(sys.argv) > 3:
        try:
            elevation = int(sys.argv[3])
            print(f"Using specified elevation: {elevation}")
        except ValueError:
            print(f"ERROR: Elevation must be a number, got: {sys.argv[3]}")
            sys.exit(1)
    
    success = create_sa_ligature(input_path, output_path, elevation)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()