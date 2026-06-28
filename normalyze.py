from fontTools.ttLib import TTFont

def convert_to_monospace(input_path, output_path, target_width=None):
    font = TTFont(input_path)
    hmtx = font['hmtx']
    glyf = font['glyf']
    
    glyph_names = [name for name in font.getGlyphOrder() if name != '.notdef']
    
    # Calculate average width if not explicitly defined
    if target_width is None:
        total_width = sum(hmtx[name][0] for name in glyph_names)
        target_width = int(total_width / len(glyph_names))
        print(f"Calculated average target width: {target_width}")

    for name in font.getGlyphOrder():
        current_width, current_lsb = hmtx[name]
        
        # Keep formatting markers or zero-width glyphs unchanged
        if current_width == 0:
            continue
            
        if name in glyf and hasattr(glyf[name], 'xMin'):
            glyph = glyf[name]
            visual_width = glyph.xMax - glyph.xMin
            
            # Calculate spacing requirements to perfectly center the vectors
            new_lsb = int((target_width - visual_width) / 2)
            shift_x = new_lsb - current_lsb
            
            # Shift composite layouts (characters built using parts of other characters)
            if glyph.isComposite():
                for component in glyph.components:
                    component.x += shift_x
            # Shift simple vector paths
            elif hasattr(glyph, 'numberOfContours') and glyph.numberOfContours > 0:
                for i in range(len(glyph.coordinates)):
                    x, y = glyph.coordinates[i]
                    glyph.coordinates[i] = (x + shift_x, y)
            
            # Recompute structural bounding boxes
            glyph.recalcBounds(glyf)
            
            # Commit the structural update back to the metric index
            hmtx[name] = (target_width, new_lsb)
        else:
            # Standardizes empty slots like spaces
            hmtx[name] = (target_width, current_lsb)

    # Set structural properties telling OS layout engines that it is fixed-width
    if 'post' in font:
        font['post'].isFixedPitch = 1
        
    if 'OS/2' in font:
        font['OS/2'].panose.bProportion = 9 
        
    font.save(output_path)
    print(f"Monospace font successfully saved to {output_path}")

# Run the final script safely
convert_to_monospace("undinian.ttf", "normalizedtest.ttf")
