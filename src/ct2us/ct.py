from pathlib import Path
import nibabel as nib
import numpy as np


def load_case(case_dir: str | Path, ct_file: str, segmentation_file: str):
    case_dir = Path(case_dir)
    ct_image = nib.load(case_dir / ct_file)
    seg_image = nib.load(case_dir / segmentation_file)
    ct = np.asarray(ct_image.get_fdata(), dtype=np.float32)
    labels = np.asarray(seg_image.get_fdata(), dtype=np.int16)
    if ct.shape != labels.shape:
        raise ValueError(f"CT and segmentation shapes differ: {ct.shape} vs {labels.shape}")
    return ct, labels, tuple(float(v) for v in ct_image.header.get_zooms()[:3]), ct_image.affine


def extract_plane(ct: np.ndarray, labels: np.ndarray, plane: str, index: int | None, size: int):
    """Extract a configurable orthogonal CT imaging plane."""
    axes = {"sagittal": 0, "coronal": 1, "axial": 2}
    if plane not in axes:
        raise ValueError(f"imaging_plane must be one of {sorted(axes)}, got {plane!r}")
    axis = axes[plane]
    index = ct.shape[axis] // 2 if index is None else int(index)
    if not 0 <= index < ct.shape[axis]:
        raise ValueError(f"slice_index {index} is outside 0..{ct.shape[axis] - 1} for {plane}")
    ct_slice = np.take(ct, index, axis=axis)
    seg_slice = np.take(labels, index, axis=axis)
    row = np.linspace(0, ct_slice.shape[0] - 1, size).astype(int)
    col = np.linspace(0, ct_slice.shape[1] - 1, size).astype(int)
    return ct_slice[np.ix_(row, col)], seg_slice[np.ix_(row, col)], index
