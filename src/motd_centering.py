def load_font_widths():
    font_widths = {}
    try:
        with open('data/fontWidths.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    char_part, width_part = line.split('=', 1)
                    if width_part.isdigit():
                        if not char_part:
                            font_widths[' '] = int(width_part)
                        else:
                            font_widths[char_part] = int(width_part)
    except FileNotFoundError:
        print("[WARN] fontWidths.txt not found, using default widths")
        return {}
    except Exception as e:
        print(f"[WARN] Error loading fontWidths.txt: {e}")
        return {}

    return font_widths

def calculate_text_width(text, font_widths):
    total_width = 0
    is_bold = False
    i = 0
    visible_chars_count = 0

    while i < len(text):
        char = text[i]

        if char == '§':
            i += 1
            if i < len(text):
                format_code = text[i].lower()
                if format_code == 'l':
                    is_bold = True
                elif format_code in '0123456789abcdefkr':
                    is_bold = False
            i += 1
            continue

        visible_chars_count += 1

        char_width = font_widths.get(char, 6)
        if is_bold:
            char_width += 1

        total_width += char_width

        i += 1

    if visible_chars_count > 0:
        total_width += (visible_chars_count - 1)

    return total_width

def center_text_by_width(text, font_widths, max_width=260):
    if not text.strip():
        return text

    text_width = calculate_text_width(text, font_widths)

    if text_width >= max_width:
        return text

    space_width = font_widths.get(' ', 4)
    padding_needed = (max_width - text_width) // 2
    spaces_needed = max(0, padding_needed // space_width)

    return ' ' * spaces_needed + text
