# CT-to-ultrasound simulation with Field II-compatible Python interfaces

This project converts a real CT volume and its anatomical segmentation into a
tissue-specific acoustic map, a point-scatterer field, RF data, and a B-mode
image from a configurable linear-array acquisition.

## Genuine Field II (MATLAB) backend

The official **Field II 3.30 Linux distribution** is installed at
`third_party/Field_II-3.30/`, including the vendor `Mat_field.mexa64` MEX
binary and MATLAB API. The `fieldii_matlab` backend uses the MATLAB Engine for
Python and calls the genuine Field II functions `field_init`,
`xdc_linear_array`, `xdc_focus`, and `calc_scat` to create every RF line.

It is not a Python reimplementation. It needs a locally installed, licensed
MATLAB version compatible with the Field II 3.30 Linux MEX binary and a Python
version supported by that MATLAB release.

1. Install MATLAB, then install its Engine API into the environment that runs
   this project. From your MATLAB installation, run:

   ```bash
   python -m pip install "<MATLAB_ROOT>/extern/engines/python"
   ```

2. Verify `python -c "import matlab.engine"` succeeds.
3. Run the true Field II configuration:

   ```bash
   python -m ct2us.pipeline --config configs/fieldii_matlab.yaml
   ```

Use `FIELD_II_ROOT=/path/to/Field_II` only when the official distribution is
stored somewhere other than `third_party/Field_II-3.30`.

This configuration uses the same CT-derived scatterers and transducer settings
as the reference example, but Field II itself produces the RF data. It is more
computationally demanding than the reference backend.

## Field II decision

Classic **Field II 3.x is not directly usable from Python**: its public API is
MATLAB MEX code. `pyfield` is a Python wrapper, but it calls the MATLAB Engine,
requires a licensed MATLAB installation, and is therefore not a standalone
Python solution. No MATLAB code is used in this project.

The closest direct Python option is the official **Field IIpro Python release**.
The Field II site states that this release exists, but it is distributed by the
Field II project rather than via PyPI and its public download/API documentation
is incomplete. The `fieldii_pro` backend is deliberately an optional adapter
and provides a precise error until the vendor package is installed.

The included `reference` backend is a fully Python, Field II-style point
scatterer/RF interface. It computes linear-array pulse-echo RF signals from
the same scatterers and acquisition parameters, then reconstructs B-mode. It
is intended for reproducible development and testing; it is **not a numerical
replacement or validation-equivalent implementation of Field IIpro**.

### Installing Field IIpro Python when available

1. Obtain the official Field IIpro Python release from the Field II project and
   accept its usage terms.
2. Install it into this environment following the vendor instructions.
3. Implement the small vendor-specific call in
   `src/ct2us/backends/fieldii_pro.py`; preserve the backend's `simulate`
   method signature.
4. Set `backend.name: fieldii_pro` in a copied configuration.

The rest of the pipeline, including CT loading, acoustic properties,
scatterers, output layout, and reconstruction, remains unchanged.

## Dataset and access terms

The research workflow targets **TotalSegmentator CT**, real clinical CT scans
with masks for 117 anatomical structures. The dataset is published by the
University Hospital Basel on Zenodo under **CC BY 4.0**: attribution is
required and use/share/adaptation is allowed under that licence. Cite
Wasserthal et al., *Radiology: Artificial Intelligence* (2023), and the Zenodo
dataset DOI. Review the current Zenodo terms before downloading.

The official 102-case v2.0.1 subset is about 3.2 GB and can be downloaded
reproducibly by calling:

```python
from ct2us.dataset import download_official_small_subset
download_official_small_subset("data/totalsegmentator_small")
```

For a small executable demonstration, `scripts/download_example.py` downloads
the TotalSegmentator repository's public real CT reference volume and paired
reference segmentation. It is a demo case only; use the official Zenodo subset
for research-scale experiments.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## End-to-end example

```bash
python scripts/download_example.py
python -m ct2us.pipeline --config configs/example.yaml
```

For an interactive walkthrough, install the optional notebook tools and open
`notebooks/ct_to_ultrasound_demo.ipynb`:

```bash
python -m pip install -e '.[notebook]'
jupyter lab notebooks/ct_to_ultrasound_demo.ipynb
```

With MATLAB's Python engine installed, use the genuine Field II notebook:

```bash
jupyter lab notebooks/ct_to_ultrasound_fieldii.ipynb
```

Outputs are written to `outputs/example/`:

- `rf.npy`: simulated RF lines, shaped `(scan_lines, samples)`.
- `bmode.npy` and `bmode_overlay.png`: envelope-detected log-compressed B-mode.
- `ct_overlay.png`: source CT slice with segmentation outline.
- `acoustic_properties_3d.npz`: full-volume speed, density, attenuation,
  impedance, diffuse scattering, label boundary, and source labels.
- `acoustic_properties_plane.npz`: the resampled property map used for the
  selected B-mode acquisition.
- `scatterers.npz`: position and amplitude of diffuse and boundary scatterers.
- `metadata.json` and `config_used.yaml`: acquisition/provenance.

## Acoustic model

CT HU values initialize air, fat, soft tissue, and bone behavior. Segmentation
masks override ambiguous non-air voxels as anatomy, retain every anatomy
interface, and produce stronger boundary reflectors. The stored maps include:

| Property | Units | Use |
| --- | --- | --- |
| Speed of sound | m/s | Two-way delay model |
| Density | kg/m3 | Acoustic impedance |
| Attenuation | dB/cm/MHz | Saved for Field IIpro extension |
| Impedance | Rayl | Boundary contrast proxy |
| Diffuse scattering | relative | Tissue speckle scatterers |
| Boundary map | binary | Strong interface reflectors |

## Configuration

`configs/example.yaml` controls center and sampling frequency, element count,
width, height, kerf, transmit/receive focus, line count, depth, imaging plane,
lateral width, output resolution, and maximum scatterer count. The reference
backend supports `axial`, `coronal`, and `sagittal` CT planes. Field IIpro can
extend the same schema to arbitrary 3D plane poses.
