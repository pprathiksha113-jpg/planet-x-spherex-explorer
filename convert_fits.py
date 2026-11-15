import ssl, certifi
ctx = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ctx

import csv, io, os, time
import urllib.parse
import urllib.request
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt

RA, DEC = 127.69444, -39.17760
os.makedirs("fits_files", exist_ok=True)
os.makedirs("public/images", exist_ok=True)


def retry(func, tries=6, wait=15):
    for attempt in range(1, tries + 1):
        try:
            return func()
        except Exception as err:
            print(f"  attempt {attempt} failed: {err}")
            time.sleep(wait)
    raise RuntimeError("NASA still unavailable, try again later")


params = urllib.parse.urlencode({
    "COLLECTION": "spherex_qr3",
    "POS": f"CIRCLE {RA} {DEC} 0.01",
    "RESPONSEFORMAT": "CSV",
    "MAXREC": "10",
})


def search():
    with urllib.request.urlopen("https://irsa.ipac.caltech.edu/SIA?" + params) as r:
        return r.read().decode("utf-8")


rows = list(csv.DictReader(io.StringIO(retry(search))))
print("Observations found:", len(rows))

for i, row in enumerate(rows, start=1):
    out_file = f"public/images/spherex_converted_{i}.jpg"
    if os.path.exists(out_file):
        print("Skipping (already done):", out_file)
        continue

    url = row.get("access_url")
    if not url:
        print(i, "no link found")
        continue

    fits_path = f"fits_files/obs_{i}.fits"
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
        print("Failed", i, e)