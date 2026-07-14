from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

# Same colors from viewer
subject_colors = {
    "P1": "#d6eaf8", "P2": "#d1f2eb", "P3": "#f9e79f", "P4": "#f5cba7", "P5": "#f7dc6f",
    "L1": "#fadbd8", "L2": "#e8daef", "L3": "#d5f5e3", "L4": "#fcf3cf", "L5": "#f0b27a",
    "CDC": "#d7bde2"
}

DEFAULT_SUBJECT_COLOR = "#eef"

def get_cell_color(content: str) -> str:
    content = content.strip()
    if "Lunch" in content:
        return "#dcdcdc"
    elif "Library" in content:
        return "#f2f2f2"
    elif content:
        code = content.split()[0]
        return subject_colors.get(code, DEFAULT_SUBJECT_COLOR)
    return "#ffffff"

def generate_table_image(data: pd.DataFrame, title: str) -> io.BytesIO:
    cell_width = 200
    cell_height = 60
    font_size = 18
    padding = 10

    rows, cols = data.shape
    title_lines = [line.strip() for line in title.split("\n") if line.strip()]

    image = Image.new("RGB", (cell_width * cols, cell_height * (rows + 1) + padding * 3 + font_size * len(title_lines)), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Title
    title_height = padding
    line_height = font_size + 6
    for idx, line in enumerate(title_lines):
        try:
            text_width = draw.textlength(line, font=font)
        except AttributeError:
            text_width = draw.textsize(line, font=font)[0]
        x = max((image.width - text_width) / 2, padding)
        y = title_height + idx * line_height
        draw.text((x, y), line, fill="black", font=font)
    title_height += len(title_lines) * line_height
    title_height += padding

    # Header
    for j, col in enumerate(data.columns):
        x = j * cell_width
        y = title_height
        draw.rectangle([x, y, x + cell_width, y + cell_height], outline="black", fill="#cccccc")
        draw.text((x + padding, y + padding), str(col), fill="black", font=font)

    # Table cells
    for i, row in data.iterrows():
        for j, cell in enumerate(row):
            x = j * cell_width
            y = title_height + cell_height + i * cell_height
            bg_color = get_cell_color(str(cell))
            draw.rectangle([x, y, x + cell_width, y + cell_height], outline="black", fill=bg_color)
            draw.text((x + padding, y + padding), str(cell), fill="black", font=font)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf
