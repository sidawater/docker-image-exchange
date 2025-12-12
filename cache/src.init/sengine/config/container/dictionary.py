"""
Dictionary-based configuration loader.
"""
from typing import Any, get_type_hints, Union, Dict


class DictLoadable:
    """
    Dictionary-based configuration loader with type conversion and nested structure support.

    Usage Sample::

        @dataclass
        class Config(DictLoadable):
            name: str = "default"
            port: int = 8080
            debug: bool = False

        config_dict = {"name": "myapp", "port": 9000, "debug": "true"}
        config = Config.load_from_dict(config_dict)
    """

    @classmethod
    def load_from_dict(cls, data: dict, skip_none: bool = True):
        """
        Load configuration from dictionary and convert to specified types.

        :param data: Source dictionary
        :param skip_none: Whether to skip None values (preserve field defaults)
        :return: Converted object instance
        """
        kwargs = {}
        type_hints = get_type_hints(cls)

        for field_name, value in data.items():
            if field_name not in type_hints:
                continue

            if value is None and skip_none:
                continue

            target_type = type_hints[field_name]
            converted = cls._convert_value(value, target_type)
            kwargs[field_name] = converted

        return cls(**kwargs)

    @classmethod
    def load_from_dict_with_fallback(cls, data: dict, fallback: dict):
        """
        Load configuration from dictionary, fallback to backup dict for missing keys.

        :param data: Source dictionary (higher priority)
        :param fallback: Backup dictionary
        :return: Converted object instance
        """
        merged = {**fallback, **data}
        return cls.load_from_dict(merged)

    @staticmethod
    def _convert_value(value: Any, target_type):
        """
        Recursively convert value to target type.

        Supported types:
        - Basic types: bool, int, float, str
        - Optional[T]
        - List[T]
        - Dict[K, V]
        - Union[T1, T2, ...]
        - Nested DictLoadable classes
        """
        if value is None:
            return None

        origin = getattr(target_type, "__origin__", None)
        if origin is Union:
            args = target_type.__args__
            non_none_types = [t for t in args if t is not type(None)]
            if len(non_none_types) == 1:
                if value is None:
                    return None
                return DictLoadable._convert_value(value, non_none_types[0])

        if origin is Union and not any(t is type(None) for t in target_type.__args__):
            for union_type in target_type.__args__:
                try:
                    return DictLoadable._convert_value(value, union_type)
                except (ValueError, TypeError):
                    continue
            return value

        if target_type is bool or origin is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("1", "true", "yes", "on", "y", "t")
            if isinstance(value, (int, float)):
                return bool(value)
            return False

        if target_type is int or origin is int:
            if isinstance(value, (int, float)):
                return int(value)
            return int(value)

        if target_type is float or origin is float:
            if isinstance(value, (int, float)):
                return float(value)
            return float(value)

        if target_type is str or origin is str:
            return str(value)

        if origin is list:
            if not isinstance(value, list):
                return [value] if value is not None else []

            item_type = target_type.__args__[0] if target_type.__args__ else Any
            return [DictLoadable._convert_value(item, item_type) for item in value]

        if origin is Dict:
            if not isinstance(value, dict):
                return {}

            key_type = target_type.__args__[0] if target_type.__args__ else str
            val_type = target_type.__args__[1] if len(target_type.__args__) > 1 else Any

            result = {}
            for k, v in value.items():
                converted_key = DictLoadable._convert_value(k, key_type)
                converted_val = DictLoadable._convert_value(v, val_type)
                result[converted_key] = converted_val
            return result

        if isinstance(target_type, type) and issubclass(target_type, DictLoadable):
            if isinstance(value, dict):
                return target_type.load_from_dict(value)
            return target_type(**value) if isinstance(value, dict) else value

        return value


def create_from_dict(cls, data: dict, skip_none: bool = True):
    """
    Factory function: Create instance of any class from dictionary.

    :param cls: Target class
    :param data: Source dictionary
    :param skip_none: Whether to skip None values
    :return: Instance of target class
    """
    if not hasattr(cls, '__annotations__'):
        raise ValueError(f"Class {cls.__name__} must have type annotations")

    kwargs = {}
    type_hints = get_type_hints(cls)

    for field_name, value in data.items():
        if field_name not in type_hints:
            continue

        if value is None and skip_none:
            continue

        target_type = type_hints[field_name]
        converted = DictLoadable._convert_value(value, target_type)
        kwargs[field_name] = converted

    return cls(**kwargs)
