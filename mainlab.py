import cv2
import colour
import numpy as np
import json

# Load color databases
with open("michel_colors_lab.json", "r") as f:
    michel_colors = json.load(f)

with open("stamp_colors_name.json", "r") as f:
    stamp_colors = json.load(f)

# --- Program Logic ---

def get_allowed_color_names(michel_number):
    """Return the configured color names for a Michel number as a list."""
    color_names = stamp_colors[michel_number]
    if isinstance(color_names, str):
        return [color_names]
    return color_names


def build_known_color_array(color_names):
    """Resolve stored color names into a NumPy array of Lab values."""
    missing_names = [name for name in color_names if name not in michel_colors]
    if missing_names:
        missing_text = ", ".join(missing_names)
        raise KeyError(f"Missing Lab values for: {missing_text}")

    return np.array([michel_colors[name] for name in color_names], dtype=float)


def match_stamp_pixels_to_palette(stamp_pixels, known_colors, threshold=8):
    """Match every extracted stamp pixel against all allowed Lab colors at once."""
    dist = colour.difference.delta_E_CIE2000(
        stamp_pixels[:, None, :],
        known_colors[None, :, :]
    )

    best_match_idx = np.argmin(dist, axis=1)
    best_match_dist = np.min(dist, axis=1)
    match_mask = best_match_dist < threshold

    return best_match_idx, best_match_dist, match_mask


def summarize_matches(color_names, best_match_idx, best_match_dist, match_mask):
    """Aggregate pixel matches into per-color totals and average Delta E values."""
    summary = {
        name: {"count": 0, "total_delta_e": 0.0}
        for name in color_names
    }

    matched_indices = best_match_idx[match_mask]
    matched_distances = best_match_dist[match_mask]

    for palette_idx, delta_e in zip(matched_indices, matched_distances):
        color_name = color_names[palette_idx]
        summary[color_name]["count"] += 1
        summary[color_name]["total_delta_e"] += float(delta_e)

    return summary


def print_match_summary(michel_number, summary):
    """Print per-color match statistics and the best overall candidate."""
    best_color = None
    best_score = -1

    for name, data in summary.items():
        count = data["count"]
        avg_delta_e = data["total_delta_e"] / count if count else 0.0
        score = count / (avg_delta_e + 1e-6) if count else 0.0

        print(
            f"{name}: matches={count}, avg_delta_e={avg_delta_e:.2f}, score={score:.2f}"
        )

        if score > best_score:
            best_score = score
            best_color = name

    if best_color and summary[best_color]["count"] > 0:
        print(f"\nMost likely color for {michel_number}: {best_color} (score: {best_score:.2f})")
    else:
        print(f"\nNo good color match found for {michel_number}.")


def extract_pure_stamp_ink(image_path):
    # 1. Load the full image
    img_bgr = cv2.imread(image_path)

    # 2. Convert to Lab (Best for separating colors)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB) / 255.0
    img_lab = colour.models.XYZ_to_Lab(colour.models.sRGB_to_XYZ(img_rgb))
    pixels = img_lab.reshape(-1, 3)

    # 3. Remove "The Extremes" (Paper and Postmarks)
    # Most stamps are darker than the paper but lighter than a black cancel.
    # We use the Lightness (L) channel to find the "Meat" of the stamp.
    l_channel = pixels[:, 0]

    # We keep only pixels between the 20th and 70th percentile of brightness.
    # This effectively "deletes" the white paper and the dark black ink.
    lower_limit = np.percentile(l_channel, 20)
    upper_limit = np.percentile(l_channel, 70)

    mask = (l_channel > lower_limit) & (l_channel < upper_limit)
    ink_only_pixels = pixels[mask]

    return ink_only_pixels


# --- Main Interface ---
print("Available stamps to analyze:")
for stamp in stamp_colors:
    print(f"{stamp}")

image_path = input("Enter the path of the image you want to process: ")
michel_number = input("Enter the michel number of the stamp you want to process: ")

if michel_number in stamp_colors:
    color_names = get_allowed_color_names(michel_number)
    stamp_pixels = extract_pure_stamp_ink(image_path)
    known_colors = build_known_color_array(color_names)
    best_match_idx, best_match_dist, match_mask = match_stamp_pixels_to_palette(
        stamp_pixels,
        known_colors,
    )
    summary = summarize_matches(
        color_names,
        best_match_idx,
        best_match_dist,
        match_mask,
    )
    print_match_summary(michel_number, summary)
else:
    print("No matching stamp number found!")
