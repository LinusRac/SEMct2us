from pathlib import Path
import yaml


def load_config(path: str | Path) -> dict:
    path = Path(path).resolve()
    with path.open() as stream:
        config = yaml.safe_load(stream)
    root = path.parent.parent
    for key in ("case_dir",):
        value = Path(config["dataset"][key])
        config["dataset"][key] = str(value if value.is_absolute() else root / value)
    output = Path(config["output_dir"])
    config["output_dir"] = str(output if output.is_absolute() else root / output)
    config["_config_path"] = str(path)
    return config
