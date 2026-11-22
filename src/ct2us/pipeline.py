import argparse
from pathlib import Path
import json
import shutil
import numpy as np
import yaml

from .acoustic import make_acoustic_map
from .backends import get_backend
from .config import load_config
from .ct import extract_plane, load_case
from .reconstruction import bmode_from_rf
from .scatterers import make_scatterers
from .visualize import save_ct_overlay, save_us_overlay


def run(config_path):
    config = load_config(config_path)
    out = Path(config["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    ct, labels, spacing, affine = load_case(**config["dataset"])
    acq = config["acquisition"]
    plane = acq.get("imaging_plane", acq.get("plane", "axial"))
    ct_slice, seg_slice, index = extract_plane(ct, labels, plane, acq.get("slice_index"), acq["image_size"])
    properties_3d = make_acoustic_map(ct, labels)
    properties = {}
    for name, volume in properties_3d.items():
        if volume.ndim == 3:
            properties[name] = extract_plane(volume, labels, plane, index, acq["image_size"])[0]
        else:
            properties[name] = volume
    positions, amplitudes = make_scatterers(properties, acq["lateral_extent_mm"], acq["depth_mm"],
                                            acq["max_scatterers"], config["seed"])
    rf = get_backend(config["backend"]["name"]).simulate(positions, amplitudes, acq, float(properties["speed_m_s"][properties["speed_m_s"] > 1000].mean()))
    bmode, bmode_db = bmode_from_rf(
        rf, acq["dynamic_range_db"], image_size=int(acq["image_size"])
    )
    np.save(out / "rf.npy", rf)
    np.save(out / "bmode.npy", bmode)
    np.savez_compressed(out / "acoustic_properties_3d.npz", **properties_3d)
    np.savez_compressed(out / "acoustic_properties_plane.npz", **properties)
    np.savez_compressed(out / "scatterers.npz", positions_m=positions, amplitudes=amplitudes)
    save_ct_overlay(ct_slice, seg_slice, out / "ct_overlay.png")
    save_us_overlay(
        bmode, properties["boundary"], out / "bmode_overlay.png",
        lateral_extent_mm=float(acq["lateral_extent_mm"]),
        depth_mm=float(acq["depth_mm"]),
    )
    metadata = {"backend": config["backend"]["name"], "ct_shape": list(ct.shape), "spacing_mm": spacing,
                "imaging_plane": plane, "slice_index": index, "scatterer_count": len(amplitudes), "rf_shape": list(rf.shape),
                "bmode_shape": list(bmode.shape),
                "bmode_lateral_extent_mm": float(acq["lateral_extent_mm"]),
                "bmode_depth_mm": float(acq["depth_mm"]), "acquisition": acq}
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2))
    shutil.copy(config["_config_path"], out / "config_used.yaml")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/example.yaml")
    args = parser.parse_args()
    print(f"Wrote simulation outputs to {run(args.config)}")
