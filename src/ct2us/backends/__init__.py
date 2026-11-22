from .reference import ReferenceScattererBackend
from .fieldii_pro import FieldIIProBackend
from .fieldii_matlab import FieldIIMatlabBackend


def get_backend(name: str):
    if name == "reference":
        return ReferenceScattererBackend()
    if name == "fieldii_pro":
        return FieldIIProBackend()
    if name == "fieldii_matlab":
        return FieldIIMatlabBackend()
    raise ValueError(f"Unknown backend: {name}")
