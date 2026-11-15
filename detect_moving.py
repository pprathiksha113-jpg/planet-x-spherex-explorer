import sys, json
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from scipy import ndimage

# ---- Satellite streak settings (tune these if results look wrong) ----
STREAK_MIN_LENGTH = 12      # pixels: shorter shapes are never called streaks
STREAK_MIN_ELONGATION = 4   # length / width: a streak is long and thin

a = int(sys.argv[1]) if len(sys.argv) > 1 else 2
b = int(sys.argv[2]) if len(sys.argv) > 2 else 3

def load(i):
    with fits.open(f"fits_files/obs_{i}.fits") as h:
        data = np.nan_to_num(np.squeeze(h["IMAGE"].data).astype(float))
        hdr = h["IMAGE"].header.copy()
    return data, hdr

def normalise(d):
    _, med, std = sigma_clipped_stats(d)
    return (d - med) / (std if std > 0 else 1)

def shape_of(label_img, k, sl):
    """Length, width and elongation of region k, using the spread of its pixels."""
    ys, xs = np.nonzero(label_img[sl] == k)
    if len(xs) < 3:
        return 0.0, 1.0, 1.0
    pts = np.vstack([xs, ys]).astype(float)
    eig = np.sort(np.linalg.eigvalsh(np.cov(pts)))   # small, large
    length = float(np.sqrt(12 * max(eig[1], 0)))      # a uniform line of length L has variance L^2/12
    width = float(max(np.sqrt(12 * max(eig[0], 0)), 1.0))
    return length, width, length / width

dA, hA = load(a)
dB, hB = load(b)

# Align image B onto image A's sky coordinates
try:
    from reproject import reproject_interp
    dB, _ = reproject_interp((dB, WCS(hB).celestial), WCS(hA).celestial, shape_out=dA.shape)
    dB = np.nan_to_num(dB)
    print("Aligned using WCS")
except Exception as e:
    print("WCS alignment failed, cropping instead:", e)
    h = min(dA.shape[0], dB.shape[0]); w = min(dA.shape[1], dB.shape[1])
    dA, dB = dA[:h, :w], dB[:h, :w]

zA, zB = normalise(dA), normalise(dB)
diff = ndimage.gaussian_filter(zB - zA, 1)
_, _, dstd = sigma_clipped_stats(diff)

mask = np.abs(diff) > 5 * dstd
labels, n = ndimage.label(mask)
slices = ndimage.find_objects(labels)

objects = []
for k in range(1, n + 1):
    sl = slices[k - 1]
    if sl is None:
        continue
    size = int((labels[sl] == k).sum())
    if size < 3:
        continue
    y, x = ndimage.center_of_mass(mask, labels, k)
    length, width, elong = shape_of(labels, k, sl)
    is_streak = length >= STREAK_MIN_LENGTH and elong >= STREAK_MIN_ELONGATION
    objects.append({
        "x": round(x, 1),
        "y": round(y, 1),
        "size": size,
        "change": round(float(diff[int(y), int(x)]), 2),
        "type": "satellite streak" if is_streak else "moving object",
        "length": round(length, 1),
        "elongation": round(elong, 1),
    })

streaks = [o for o in objects if o["type"] == "satellite streak"]
movers = [o for o in objects if o["type"] != "satellite streak"]
print("Possible moving objects:", len(movers))
print("Possible satellite streaks:", len(streaks))
for o in objects[:10]:
    print(o)

lo, hi = np.percentile(zA, [1, 99])
plt.figure(figsize=(8, 8))
plt.imshow(zA, cmap="gray", origin="lower", vmin=lo, vmax=hi, interpolation="nearest")
for o in objects:
    is_streak = o["type"] == "satellite streak"
    radius = max(2.5, o["length"] / 2) if is_streak else 2.5
    plt.gca().add_patch(plt.Circle((o["x"], o["y"]), radius,
                                   color="orange" if is_streak else "red", fill=False, lw=1))
plt.title(f"obs {a} vs obs {b}: {len(movers)} moving objects (red), {len(streaks)} satellite streaks (orange)")
plt.axis("off")
plt.savefig("public/images/moving_objects.jpg", dpi=150, bbox_inches="tight")
plt.savefig(f"public/images/motion_{a}_{b}.jpg", dpi=150, bbox_inches="tight")
with open("public/moving_objects.json", "w") as f:
    json.dump(objects, f)
print("Saved public/images/moving_objects.jpg")