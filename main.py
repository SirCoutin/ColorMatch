from PIL import Image
from collections import Counter

# Function to compare colors with tolerance
def is_color_in_range(rgb, target_rgb, tolerance=40):
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(rgb, target_rgb))

# Function to process image and filter for target color
def filter_image_by_color(image_path, target_color_name, tolerance=40):
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())
    width, height = img.size
    target_rgb = color_db[target_color_name]

    matching_pixels = []

    for pixel in pixels:
        if is_color_in_range(pixel, target_rgb, tolerance):
            matching_pixels.append(pixel)
        else:
            pass

    if matching_pixels:
        most_common_match = Counter(matching_pixels).most_common(1)[0][0]
        print(f"Most common matching shade for {target}: {most_common_match}")
    else:
        print(f"No pixels close to {target_color_name} found.")
