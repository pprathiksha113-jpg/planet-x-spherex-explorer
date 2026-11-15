import ssl, certifi
ctx = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ctx

import csv, io, os, time
import urllib.parse
import urllib.request
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt

REGIONS = {
    "m101": (210.80, 54.35, 6),
    "m42": (83.82, -5.39, 6),
    "m31": (10.68, 41.27, 6),
}

def retry(func, tries=5, wait=15):
    for attempt in range(1, tries + 1):
        try:
            return func()
        except Exception as err:
            print(f"  attempt {attempt} failed: {err}")
            time.sleep(wait)
    raise RuntimeError("NASA unavailable, run again later")

os.makedirs("fits_files", exist_ok=True)

for key, (RA, DEC, N) in REGIONS.items():
    out_dir = f"public/images/{key}"
    os.makedirs(out_dir, exist_ok=True)
    params = urllib.parse.urlencode({
        "COLLECTION": "spherex_qr3",
        "POS": f"CIRCLE {RA} {DEC} 0.01",
        "RESPONSEFORMAT": "CSV",
        "MAXREC": str(N),
    })

    def search():
        with urllib.request.urlopen("https://irsa.ipac.caltech.edu/SIA?" + params) as r:
            return r.read().decode("utf-8")

    try:
        rows = list(csv.DictReader(io.StringIO(retry(search))))
    except Exception as e:
        print(key, "search failed:", e)
        continue
    print(key, "observations found:", len(rows))

    for i, row in enumerate(rows, start=1):
        out_file = f"{out_dir}/spherex_converted_{i}.jpg"
        if os.path.exists(out_file):
            print("Skipping:", out_file)
            continue
        url = row.get("access_url")
        if not url:
            continue
        fits_path = f"fits_files/{key}_obs_{i}.fits"
        try:
            retry(lambda: urllib.request.urlretrieve(
                f"{url}?center={RA},{DEC}d&size=0.1", fits_path))
            with fits.open(fits_path) as hdul:
                data = hdul["IMAGE"].data
            data = np.nan_to_num(np.squeeze(data).astype(float))
            vmin, vmax = np.percentile(data, [1, 99])
            plt.imsave(out_file, data, cmap="inferno", origin="lower", vmin=vmin, vmax=vmax)
            print("Created:", out_file)
        except Exception as e:
            print("Failed", key, i, e)