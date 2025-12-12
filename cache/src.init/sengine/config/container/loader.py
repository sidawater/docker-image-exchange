"""
Unified configuration loader providing all loading methods in one place.

This module imports and re-exports all loader classes and functions from
the container package submodules for convenient access.
"""

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        tomli = None


class DictObject(dict):
    """
    Dictionary that can be accessed as attributes.

    Usage Sample::

        obj = DictObject()
        obj.name = "value"
        print(obj.name)  # "value"
    """

    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def trans_from_dict(cls, item: dict):
        """
        Recursively convert dictionary to DictObject.

        :param item: Source dictionary
        :return: DictObject instance
        """
        dict_object = DictObject()
        for key, value in item.items():
            if isinstance(value, DictObject) or (not isinstance(value, dict)):
                dict_object[key] = value
            else:
                dict_object[key] = cls.trans_from_dict(value)
        return dict_object


def load_from_toml(file_path: str) -> DictObject:
    """
    Load configuration from TOML file and convert to DictObject.

    This function reads a TOML configuration file and recursively converts
    all nested dictionaries into DictObject instances, allowing attribute-style
    access to configuration values.

    :param file_path: Path to the TOML configuration file
    :return: DictObject instance containing the loaded configuration

    Usage Sample::

        config = load_from_toml("config.toml")
        print(config.database.host)  # Access nested values as attributes
        print(config["database"]["host"])  # Also supports dict-style access

    :raises ImportError: If tomli/tomllib is not available
    :raises FileNotFoundError: If the TOML file does not exist
    :raises TOMLDecodeError: If the TOML file is malformed
    """
    if tomli is None:
        raise ImportError(
            "TOML support requires 'tomli' (Python < 3.11) or 'tomllib' (Python >= 3.11). "
            "Install tomli: pip install tomli"
        )

    with open(file_path, "rb") as f:
        data = tomli.load(f)

    return DictObject.trans_from_dict(data)
