"""
Object-based configuration loader.
"""
from typing import Any, get_type_hints, Union, Dict


class ObjectLoadable:
    """
    Object-based configuration loader for copying and converting attributes from source objects.

    Usage Sample::

        @dataclass
        class SourceConfig:
            name: str = "default"
            port: int = 8080
            debug: bool = False

        @dataclass
        class TargetConfig(ObjectLoadable):
            name: str = "default"
            port: int = 8080
            debug: bool = False

        source = SourceConfig()
        source.name = "myapp"
        source.port = "9000"
        source.debug = "yes"

        target = TargetConfig.load_from_object(source)

    """

    @classmethod
    def load_from_object(cls, source_obj, skip_none: bool = True):
        """
        Load configuration from source object attributes.

        :param source_obj: Source object to copy attributes from
        :param skip_none: Whether to skip None values (preserve field defaults)
        :return: Converted object instance
        """
        kwargs = {}
        type_hints = get_type_hints(cls)

        for field_name in type_hints.keys():
            if not hasattr(source_obj, field_name):
                continue

            value = getattr(source_obj, field_name)
            if value is None and skip_none:
                continue

            target_type = type_hints[field_name]
            converted = cls._convert_value(value, target_type)
            kwargs[field_name] = converted

        return cls(**kwargs)

    @classmethod
    def load_from_object_with_fallback(cls, source_obj, fallback: dict):
        """
        Load configuration from object, fallback to dict for missing attributes.

        :param source_obj: Source object
        :param fallback: Backup dictionary for missing attributes
        :return: Converted object instance
        """
        kwargs = {}
        type_hints = get_type_hints(cls)

        for field_name in type_hints.keys():
            value = None

            if hasattr(source_obj, field_name):
                value = getattr(source_obj, field_name)

            if value is None and field_name in fallback:
                value = fallback[field_name]

            if value is not None:
                target_type = type_hints[field_name]
                converted = cls._convert_value(value, target_type)
                kwargs[field_name] = converted

        return cls(**kwargs)

    @classmethod
    def merge_from_objects(cls, *source_objects, skip_none: bool = True):
        """
        Merge configuration from multiple source objects (later objects override earlier ones).

        :param source_objects: Variable number of source objects
        :param skip_none: Whether to skip None values
        :return: Converted object instance
        """
        kwargs = {}
        type_hints = get_type_hints(cls)

        for source_obj in source_objects:
            for field_name in type_hints.keys():
                if not hasattr(source_obj, field_name):
                    continue

                value = getattr(source_obj, field_name)
                if value is None and skip_none:
                    continue

                target_type = type_hints[field_name]
                converted = cls._convert_value(value, target_type)
                kwargs[field_name] = converted

        return cls(**kwargs)

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
        - Nested ObjectLoadable classes
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
                return ObjectLoadable._convert_value(value, non_none_types[0])

        if origin is Union and not any(t is type(None) for t in target_type.__args__):
            for union_type in target_type.__args__:
                try:
                    return ObjectLoadable._convert_value(value, union_type)
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
            return [ObjectLoadable._convert_value(item, item_type) for item in value]

        if origin is Dict:
            if not isinstance(value, dict):
                return {}

            key_type = target_type.__args__[0] if target_type.__args__ else str
            val_type = target_type.__args__[1] if len(target_type.__args__) > 1 else Any

            result = {}
            for k, v in value.items():
                converted_key = ObjectLoadable._convert_value(k, key_type)
                converted_val = ObjectLoadable._convert_value(v, val_type)
                result[converted_key] = converted_val
            return result

        if isinstance(target_type, type) and issubclass(target_type, ObjectLoadable):
            if hasattr(value, '__dict__'):
                return target_type.load_from_object(value)
            return target_type(**value.__dict__) if hasattr(value, '__dict__') else value

        return value


def create_from_object(cls, source_obj, skip_none: bool = True):
    """
    Factory function: Create instance of any class from source object.

    :param cls: Target class
    :param source_obj: Source object
    :param skip_none: Whether to skip None values
    :return: Instance of target class
    """
    if not hasattr(cls, '__annotations__'):
        raise ValueError(f"Class {cls.__name__} must have type annotations")

    kwargs = {}
    type_hints = get_type_hints(cls)

    for field_name in type_hints.keys():
        if not hasattr(source_obj, field_name):
            continue

        value = getattr(source_obj, field_name)
        if value is None and skip_none:
            continue

        target_type = type_hints[field_name]
        converted = ObjectLoadable._convert_value(value, target_type)
        kwargs[field_name] = converted

    return cls(**kwargs)
