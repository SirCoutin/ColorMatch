import cv2
import colour 
import numpy as np
import json
import os

michel_colors = {}
stamp_colors = {}

if os.path.exists("michel_colors_lab.json"):
  with open("michel_colors_lab.json", "r") as colors:
            michel_colors = json.load(colors)
else:
  print("Creating new database")
  with open("michel_colors_lab.json", "w") as colors:
            json.dump(michel_colors, colors)

if os.path.exists("stamp_colors_name.json"):
  with open("stamp_colors_name.json", "r") as colors:
            stamp_colors = json.load(colors)
else:
  print("Creating new database")
  with open("stamp_colors_name.json", "w") as colors:
            json.dump(stamp_colors, colors)

def add_color_to_michel(image_path, color_name, stamp_name):

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not load image.")
        return
    median_lab = get_median_lab(img)

    print ([round(float(x), 2) for x in median_lab.tolist()])

    michel_colors[color_name] = [round(float(x), 2) for x in median_lab.tolist()]
    
    if stamp_name not in stamp_colors:
      stamp_colors[stamp_name] = []
    
    if color_name not in stamp_colors[stamp_name]:
      stamp_colors[stamp_name].append(color_name)

    print(f"Added color '{color_name}' with Michel stamp '{stamp_name}' to the database.")

def get_median_lab(img):
    
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0
    lab = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb))
    
    # reshape(-1, 3) lines up pixels so we can find the middle value
    
    return np.median(lab.reshape(-1, 3), axis=0)

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

with open("michel_colors_lab.json", "w") as colors:
  json.dump(michel_colors, colors)

with open("stamp_colors_name.json", "w") as colors:
  json.dump(stamp_colors, colors)
