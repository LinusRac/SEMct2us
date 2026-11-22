from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def save_ct_overlay(ct, labels, path):
    path = Path(path)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(ct, cmap="gray", vmin=-1000, vmax=1000)
    ax.contour(labels > 0, levels=[0.5], colors="lime", linewidths=0.5)
    ax.set_title("CT slice with segmentation overlay")
    ax.axis("off")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_us_overlay(bmode, boundary, path, lateral_extent_mm=1.0, depth_mm=1.0):
    path = Path(path)
    fig, ax = plt.subplots(figsize=(6, 6))
    extent = [-lateral_extent_mm / 2, lateral_extent_mm / 2, depth_mm, 0]
    ax.imshow(bmode.T, cmap="gray", origin="upper", aspect="auto", extent=extent)
    x = np.linspace(-lateral_extent_mm / 2, lateral_extent_mm / 2, boundary.shape[1])
    y = np.linspace(0, depth_mm, boundary.shape[0])
    ax.contour(x, y, boundary, levels=[0.5], colors="cyan", linewidths=0.4)
    ax.set_title("Simulated B-mode with projected anatomy boundaries")
    ax.set_xlabel("Lateral position (mm)")
    ax.set_ylabel("Depth (mm)")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
