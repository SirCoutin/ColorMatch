import os

import cv2
import colour
import numpy as np


WINDOW_NAME = "Stamp Sample Picker"


def load_image(image_path):
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB) / 255.0
    img_lab = colour.models.XYZ_to_Lab(colour.models.sRGB_to_XYZ(img_rgb))
    return img_bgr, img_lab


def fit_display_image(img_bgr, max_width=1400, max_height=900):
    height, width = img_bgr.shape[:2]
    scale_x = max_width / width
    scale_y = max_height / height
    scale = min(scale_x, scale_y, 1.0)

    if scale == 1.0:
        return img_bgr.copy(), 1.0

    display_width = int(width * scale)
    display_height = int(height * scale)
    display_bgr = cv2.resize(img_bgr, (display_width, display_height), interpolation=cv2.INTER_AREA)
    return display_bgr, scale


def build_display_overlay(display_bgr, points):
    overlay = display_bgr.copy()
    for idx in range(len(points)):
        point = points[idx]
        x = point[0]
        y = point[1]
        cv2.circle(overlay, (x, y), 8, (0, 255, 0), 2)
        cv2.putText(
            overlay,
            str(idx + 1),
            (x + 10, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    cv2.putText(
        overlay,
        "Left click: add point | Backspace/U: undo | C: clear | Enter/Space: run | Esc: cancel",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
    )
    return overlay


def select_sample_points(img_bgr):
    display_bgr, scale = fit_display_image(img_bgr)
    selected_points = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            selected_points.append((x, y))

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    confirmed = False
    while True:
        overlay = build_display_overlay(display_bgr, selected_points)
        cv2.imshow(WINDOW_NAME, overlay)
        key = cv2.waitKey(20) & 0xFF

        if key == 13 or key == 32:
            if selected_points:
                confirmed = True
                break
        elif key == 27:
            break
        elif key == 8 or key == ord("u"):
            if selected_points:
                selected_points.pop()
        elif key == ord("c"):
            selected_points.clear()

    cv2.destroyWindow(WINDOW_NAME)

    if not confirmed:
        return []

    image_points = []
    for idx in range(len(selected_points)):
        display_x, display_y = selected_points[idx]
        image_x = int(round(display_x / scale))
        image_y = int(round(display_y / scale))
        image_points.append((image_x, image_y))

    return image_points


def extract_patch_medians(img_lab, points, patch_radius):
    height, width = img_lab.shape[:2]
    sample_rows = []
    sample_info = []

    for idx in range(len(points)):
        x, y = points[idx]
        x0 = max(0, x - patch_radius)
        x1 = min(width, x + patch_radius + 1)
        y0 = max(0, y - patch_radius)
        y1 = min(height, y + patch_radius + 1)

        patch = img_lab[y0:y1, x0:x1]
        patch_pixels = patch.reshape(-1, 3)
        patch_median = np.median(patch_pixels, axis=0)
        sample_rows.append(patch_median)

        sample_info.append(
            {
                "point": (x, y),
                "bounds": (x0, y0, x1, y1),
                "lab": patch_median,
            }
        )

    samples = np.array(sample_rows, dtype=float)
    return samples, sample_info


def build_reference_mask(img_lab, sample_lab, delta_threshold, min_l=0.0, max_l=100.0):
    pixels = img_lab.reshape(-1, 3)
    l_channel = pixels[:, 0]
    lightness_mask = (l_channel >= min_l) & (l_channel <= max_l)

    candidate_pixels = pixels[lightness_mask]
    if candidate_pixels.size == 0:
        raise ValueError("No pixels remained after the lightness guard.")

    dist = colour.difference.delta_E_CIE2000(
        candidate_pixels[:, None, :],
        sample_lab[None, :, :],
    )

    best_match_idx = np.argmin(dist, axis=1)
    best_match_dist = np.min(dist, axis=1)
    matched_candidates = best_match_dist <= delta_threshold

    final_flat_mask = np.zeros(lightness_mask.shape, dtype=bool)
    candidate_indices = np.flatnonzero(lightness_mask)
    kept_indices = candidate_indices[matched_candidates]
    final_flat_mask[kept_indices] = True
    final_mask = final_flat_mask.reshape(img_lab.shape[:2])

    details = {
        "delta_threshold": float(delta_threshold),
        "min_delta_e": float(np.min(best_match_dist)),
        "max_delta_e": float(np.max(best_match_dist)),
        "mean_delta_e": float(np.mean(best_match_dist)),
        "lightness_min": float(min_l),
        "lightness_max": float(max_l),
    }

    return final_mask, best_match_idx, best_match_dist, matched_candidates, details


def write_debug_images(image_path, img_bgr, mask, label):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(os.path.dirname(image_path), "debug_output")
    os.makedirs(output_dir, exist_ok=True)

    mask_image = mask.astype(np.uint8) * 255

    filtered_bgr = np.zeros_like(img_bgr)
    filtered_bgr[mask] = img_bgr[mask]

    overlay_bgr = img_bgr.copy()
    overlay_bgr[mask] = (0, 255, 0)

    mask_path = os.path.join(output_dir, f"{base_name}_{label}_mask.png")
    filtered_path = os.path.join(output_dir, f"{base_name}_{label}_filtered.png")
    overlay_path = os.path.join(output_dir, f"{base_name}_{label}_overlay.png")

    cv2.imwrite(mask_path, mask_image)
    cv2.imwrite(filtered_path, filtered_bgr)
    cv2.imwrite(overlay_path, overlay_bgr)

    return mask_path, filtered_path, overlay_path


def write_sample_overlay(image_path, img_bgr, sample_info):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(os.path.dirname(image_path), "debug_output")
    os.makedirs(output_dir, exist_ok=True)

    overlay = img_bgr.copy()
    for idx in range(len(sample_info)):
        info = sample_info[idx]
        x, y = info["point"]
        x0, y0, x1, y1 = info["bounds"]
        cv2.rectangle(overlay, (x0, y0), (x1 - 1, y1 - 1), (0, 255, 255), 2)
        cv2.circle(overlay, (x, y), 5, (0, 255, 0), -1)
        cv2.putText(
            overlay,
            str(idx + 1),
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    overlay_path = os.path.join(output_dir, f"{base_name}_samples_overlay.png")
    cv2.imwrite(overlay_path, overlay)
    return overlay_path


def print_sample_info(sample_info):
    for idx in range(len(sample_info)):
        info = sample_info[idx]
        lab = info["lab"]
        x, y = info["point"]
        print(
            f"Sample {idx + 1} at ({x}, {y}): "
            f"L={lab[0]:.2f}, a={lab[1]:.2f}, b={lab[2]:.2f}"
        )


def main():
    image_path = input("Enter the path of the image you want to process: ").strip()
    patch_radius_text = input("Patch radius around each click (default 5): ").strip()
    delta_threshold_text = input("Delta E threshold from clicked samples (default 10): ").strip()
    min_l_text = input("Minimum L to keep (default 0): ").strip()
    max_l_text = input("Maximum L to keep (default 100): ").strip()

    if patch_radius_text:
        patch_radius = int(patch_radius_text)
    else:
        patch_radius = 5

    if delta_threshold_text:
        delta_threshold = float(delta_threshold_text)
    else:
        delta_threshold = 10.0

    if min_l_text:
        min_l = float(min_l_text)
    else:
        min_l = 0.0

    if max_l_text:
        max_l = float(max_l_text)
    else:
        max_l = 100.0

    img_bgr, img_lab = load_image(image_path)
    points = select_sample_points(img_bgr)
    if not points:
        print("No sample points selected. Exiting.")
        return

    sample_lab, sample_info = extract_patch_medians(img_lab, points, patch_radius)
    matched_mask, best_match_idx, best_match_dist, matched_candidates, details = build_reference_mask(
        img_lab,
        sample_lab,
        delta_threshold,
        min_l=min_l,
        max_l=max_l,
    )

    sample_overlay_path = write_sample_overlay(image_path, img_bgr, sample_info)
    matched_mask_path, matched_filtered_path, matched_overlay_path = write_debug_images(
        image_path,
        img_bgr,
        matched_mask,
        "clicked_match",
    )

    kept_pixels = int(np.count_nonzero(matched_mask))
    total_pixels = int(matched_mask.size)
    kept_ratio = kept_pixels / total_pixels if total_pixels else 0.0
    matched_count = int(np.count_nonzero(matched_candidates))
    total_candidates = len(best_match_dist)
    matched_ratio = matched_count / total_candidates if total_candidates else 0.0

    print_sample_info(sample_info)
    print(f"Delta E range: {details['min_delta_e']:.2f} to {details['max_delta_e']:.2f}")
    print(f"Mean Delta E: {details['mean_delta_e']:.2f}")
    print(f"Delta E threshold: {details['delta_threshold']:.2f}")
    print(f"Lightness guard: L from {details['lightness_min']:.2f} to {details['lightness_max']:.2f}")
    print(f"Matched candidates: {matched_count}/{total_candidates} ({matched_ratio:.2%})")
    print(f"Matched image pixels: {kept_pixels}/{total_pixels} ({kept_ratio:.2%})")
    print(f"Sample overlay image: {sample_overlay_path}")
    print(f"Matched mask image: {matched_mask_path}")
    print(f"Matched filtered image: {matched_filtered_path}")
    print(f"Matched overlay image: {matched_overlay_path}")


if __name__ == "__main__":
    main()
