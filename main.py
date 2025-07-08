from PIL import Image
from collections import defaultdict
import json
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
import numpy as np

if not hasattr(np, "asscalar"):
    def asscalar(a):
        return a if np.isscalar(a) else a.item()
    np.asscalar = asscalar

# Load color databases
with open("michel_colors.json", "r") as f:
    michel_colors = json.load(f)

with open("stamp_colors.json", "r") as f:
    stamp_colors = json.load(f)

# Convert all stored Michel colors to LabColor
lab_michel_colors = {
    name: LabColor(*lab) for name, lab in michel_colors.items()
}

def filter_image_by_color(image_path, stamp_colors_list, lab_michel_colors, michel_number, tolerance=2):
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())

    score_tracker = {
        name: {"count": 0, "total_delta_e": 0.0}
        for name in stamp_colors_list
    }

    for pixel in pixels:
        rgb = sRGBColor(pixel[0]/255, pixel[1]/255, pixel[2]/255)
        lab_pixel = convert_color(rgb, LabColor)

        best_match = None
        lowest_diff = float("inf")

        for name in stamp_colors_list:
            stored_lab = lab_michel_colors[name]
            diff = delta_e_cie2000(lab_pixel, stored_lab)
            if diff < lowest_diff:
                lowest_diff = diff
                best_match = name

        if lowest_diff <= tolerance:
            score_tracker[best_match]["count"] += 1
            score_tracker[best_match]["total_delta_e"] += lowest_diff

    def confidence_score(count, total_diff):
        if count == 0:
            return 0
        avg_diff = total_diff / count
        return count / (avg_diff + 1e-6)

    best_color = None
    best_score = -1

    for name, data in score_tracker.items():
        score = confidence_score(data["count"], data["total_delta_e"])
        print(f"{name}: matches={data['count']}, avg_delta_e={data['total_delta_e'] / data['count'] if data['count'] else 0:.2f}, score={score:.2f}")
        if score > best_score:
            best_score = score
            best_color = name

    if best_color:
        print(f"\nMost likely color for {michel_number}: {best_color} (score: {best_score:.2f})")
    else:
        print(f"\nNo good color match found for {michel_number}.")

# --- Main Interface ---
print("Available stamps to analyze:")
for stamp in stamp_colors:
    print(f"{stamp}")

image_path = input("Enter the path of the image you want to process: ")
michel_number = input("Enter the michel number of the stamp you want to process: ")

if michel_number in stamp_colors:
    color_names = stamp_colors[michel_number]
    filter_image_by_color(image_path, color_names, lab_michel_colors, michel_number)
else:
    print("No matching stamp number found!")