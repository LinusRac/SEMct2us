"""Public TotalSegmentator data acquisition helpers."""
from pathlib import Path
from urllib.request import urlretrieve
import zipfile

REFERENCE_BASE = "https://raw.githubusercontent.com/wasserth/TotalSegmentator/master/tests/reference_files"
REFERENCE_FILES = ("example_ct_sm.nii.gz", "example_seg.nii.gz")
OFFICIAL_SMALL_SUBSET = "https://zenodo.org/records/10047263/files/Totalsegmentator_dataset_small_v201.zip?download=1"


def download_reference_case(destination: str | Path) -> Path:
    """Download TotalSegmentator's public CT+segmentation reference pair."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in REFERENCE_FILES:
        target = destination / name
        if not target.exists():
            urlretrieve(f"{REFERENCE_BASE}/{name}", target)
    return destination


def download_official_small_subset(destination: str | Path) -> Path:
    """Download and extract the official 102-case CC BY 4.0 subset (about 3.2 GB)."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "Totalsegmentator_dataset_small_v201.zip"
    if not archive.exists():
        urlretrieve(OFFICIAL_SMALL_SUBSET, archive)
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(destination)
    return destination
