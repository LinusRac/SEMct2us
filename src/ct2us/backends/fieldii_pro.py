class FieldIIProBackend:
    """Optional adapter placeholder for the official Field IIpro Python release.

    Field IIpro's Python distribution is obtained from Field II directly and is
    not a public PyPI dependency. This adapter intentionally fails clearly until
    its documented Python package/API is installed locally.
    """
    name = "fieldii_pro"

    def simulate(self, *args, **kwargs):
        raise RuntimeError(
            "Field IIpro Python is not installed. Follow README.md to obtain the official "
            "Python release, then implement the vendor API binding in this adapter. "
            "Use backend.name: reference for the fully runnable open example."
        )
