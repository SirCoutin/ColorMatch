import json
import os
from collections import Counter
from PIL import Image

michel_colors = {}
stamp_colors = {}

if os.path.exists("michel_colors.json"):
  with open("michel_colors.json", "r") as colors:
            michel_colors = json.load(colors)
else:
  print("Creating new database")
  with open("michel_colors.json", "w") as colors:
            json.dump(michel_colors, colors)

if os.path.exists("stamp_colors.json"):
  with open("stamp_colors.json", "r") as colors:
            stamp_colors = json.load(colors)
else:
  print("Creating new database")
  with open("stamp_colors.json", "w") as colors:
            json.dump(stamp_colors, colors)

def add_color_to_michel(image_path, name, stamp_name):
  img = Image.open(image_path).convert("HSV")
  pixels = list(img.getdata())

  hsv_pixel_array = []

  for pixel in pixels:
    hsv_pixel_array.append((
      round(pixel[0] * (360 / 255), 2),
      round(pixel[1] * (100 / 255), 2),
      round(pixel[2] * (100 / 255), 2)
    ))

  most_common_match = Counter(hsv_pixel_array).most_common(1)[0][0]
  michel_colors[name] = most_common_match
  
  if stamp_name not in stamp_colors:
    stamp_colors[stamp_name] = []

  if name not in stamp_colors[stamp_name]:
    stamp_colors[stamp_name].append(name)

  print(f"Added {color_name} with the RGB value of {most_common_match} successfully!")

while True:
    image_path = input("Enter the path of the image you want to save (Or type 'exit' to quit):  ")
    if image_path.lower() == "exit":
        break

    color_name = input("Enter the name of the respective Michel color: ").lower()
    stamp_name = input("What stamp should this color be associated with? Use Michel numbers: ").lower()
     
    if color_name in michel_colors:
      question = input("This color name is already in use! Do you want to override the color? (Y/N) ").lower()
      if question == "y":
          add_color_to_michel(image_path, color_name, stamp_name)
      elif question == "n":
          print("Please try again")
    else:
      add_color_to_michel(image_path, color_name, stamp_name)

with open("michel_colors.json", "w") as colors:
  json.dump(michel_colors, colors)

with open("stamp_colors.json", "w") as colors:
  json.dump(stamp_colors, colors)
