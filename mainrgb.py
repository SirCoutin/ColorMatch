from PIL import Image
from collections import Counter
import json

michel_colors = {}
with open("michel_colors_rgb.json", "r") as f:
    michel_colors = json.load(f)

stamp_colors = {}
with open("stamp_colors_rgb.json", "r") as f:
    stamp_colors = json.load(f)

#Check color matches
def is_color_in_range(rgb, stamp_colors, michel_colors, tolerance):
    for color_name in stamp_colors:
        color_rgb = michel_colors[color_name]
        dist = rgb_distance(rgb, color_rgb)
        if dist <= tolerance:
            print(f" --> Matched with '{color_name}' (RGB {rgb} stamp color {color_rgb})")
            return True
    return False

def find_closest_color(rgb_value, michel_colors):
    closest_color = None
    min_distance = float('inf')
    
    for name, rgb in michel_colors.items():
        dist = rgb_distance(rgb_value, rgb)
        if dist < min_distance:
            min_distance = dist
            closest_color = name
    return closest_color

def rgb_distance(rgb1, rgb2):
    return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5

# Function to process image and filter for target color
def filter_image_by_color(image_path, stamp_colors, michel_colors, michel_number, tolerance=15):
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())

    matching_pixels = []

    for pixel in pixels:
        if is_color_in_range(pixel, stamp_colors, michel_colors, tolerance):
            matching_pixels.append(pixel)
        else:
            pass

    if matching_pixels:
        most_common_match = Counter(matching_pixels).most_common(1)[0][0]
        closest_color_name = find_closest_color(most_common_match, michel_colors)
        print(f"The most common color was {most_common_match}")
        print(f"The closest matching shade for {michel_number} was {closest_color_name}")
    else:
        print(f"No pixels close to {stamp_colors} found.")

print("Available stamps to analyze:")
for stamp in stamp_colors:
    print(f"{stamp}")

image_path = input("Enter the path of the image you want to process: ")
michel_number = input("Enter the michel number of the stamp you want to process: ")
if michel_number in stamp_colors:
    color_names = stamp_colors[michel_number]
    filter_image_by_color(image_path, color_names, michel_colors, michel_number)
else:
    print("No matching stamp number found!")