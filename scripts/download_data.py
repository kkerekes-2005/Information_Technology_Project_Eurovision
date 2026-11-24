"""Download the three raw CSV files of the Eurovision dataset into data/raw/.

    python scripts/download_data.py

Source: https://github.com/Spijkervet/eurovision-dataset, release 2023.
License: Creative Commons Attribution 4.0 International (CC BY 4.0).
The release is fixed in the address, so every run fetches the same files and the
row counts of the report stay valid. The raw files are never committed to Git.
"""
import os
import urllib.request

RELEASE = "2023"
BASE_URL = f"https://github.com/Spijkervet/eurovision-dataset/releases/download/{RELEASE}"
FILES = ["contestants.csv", "votes.csv", "betting_offices.csv"]
TARGET = "data/raw"


def main():
    os.makedirs(TARGET, exist_ok=True)
    for name in FILES:
        path = os.path.join(TARGET, name)
        urllib.request.urlretrieve(f"{BASE_URL}/{name}", path)
        print(f"{name:22} {os.path.getsize(path):9} bytes -> {path}")


if __name__ == "__main__":
    main()
