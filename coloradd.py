import json
import os
from collections import Counter
from PIL import Image

michel_colors = {}

def add_color_to_michel(image_path, name):
  img = Image.open(image_path).convert("RGB")
  pixels = list(img.getdata())

  most_common_match = Counter(pixels).most_common(1)[0][0]
  michel_colors[name] = most_common_match

if os.path.exists("michel_colors.json"):
  with open("michel_colors.json", "r") as colors:
            michel_colors = json.load(colors)
else:
  print("Creating new database")
  with open("michel_colors.json", "w") as colors:
            json.dump(michel_colors, colors)

image_path = input("Enter the path of the image you want to save: ")
color_name = input("Enter the name of the respective Michel color: ").lower()

if color_name in michel_colors:
     print("This color name is already in use!")
     exit(0)
else:
    add_color_to_michel(image_path, color_name)

with open("michel_colors.json", "w") as colors:
  json.dump(michel_colors, colors)
