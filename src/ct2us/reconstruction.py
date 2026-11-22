import numpy as np
from scipy.ndimage import zoom
from scipy.signal import hilbert


def bmode_from_rf(rf: np.ndarray, dynamic_range_db: float, image_size: int | None = None):
    """Envelope-detect RF lines and resample them to a display image.

    ``rf`` is sampled in time (typically tens of samples per millimetre), not
    in screen pixels. A B-mode image therefore needs axial decimation before
    display. This avoids moire-like stripes from rendering every temporal
    sample in a compact figure.
    """
    envelope = np.abs(hilbert(rf, axis=1))
    envelope /= max(float(envelope.max()), 1e-12)
    image_db = 20 * np.log10(np.maximum(envelope, 1e-8))
    image = np.clip((image_db + dynamic_range_db) / dynamic_range_db, 0, 1)
    if image_size is not None:
        if image_size < 2:
            raise ValueError("image_size must be at least 2")
        scale = (image_size / image.shape[0], image_size / image.shape[1])
        image = zoom(image, scale, order=1, prefilter=False)
        image_db = zoom(image_db, scale, order=1, prefilter=False)
    return image.astype(np.float32), image_db.astype(np.float32)
