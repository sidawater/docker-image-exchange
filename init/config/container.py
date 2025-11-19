"""
config container
"""
import os
from typing import Callable
from dataclasses import dataclass, fields, field
from typing import Any, Optional, get_type_hints


def Attr(
    *,
    default: Any = ...,
    default_factory: Optional[Callable[[], Any]] = None,
    env: str = ""
):
    metadata = {"env": env}

    if default is not ... and default_factory is not None:
        raise ValueError("Cannot specify both 'default' and 'default_factory'")

    if default is not ...:
        return field(default=default, metadata=metadata)
    elif default_factory is not None:
        return field(default_factory=default_factory, metadata=metadata)
    else:
        return field(metadata=metadata)


@dataclass
class EnvLoadable:
    @classmethod
    def load_from_env(cls):
        kwargs = {}
        type_hints = get_type_hints(cls)
        for f in fields(cls):
            env_var = f.metadata.get("env")
            if not env_var:
                continue
            env_value = os.getenv(env_var)
            if env_value is None:
                continue
            target_type = type_hints[f.name]
            converted = cls._convert_value(env_value, target_type)
            kwargs[f.name] = converted
        return cls(**kwargs)

    @staticmethod
    def _convert_value(value: str, target_type):
        origin = getattr(target_type, "__origin__", None)
        if origin is Optional or origin is type(Optional[int]):  # handle Optional[T]
            # Optional[T] == Union[T, None]
            if len(target_type.__args__) == 2 and type(None) in target_type.__args__:
                real_type = next(t for t in target_type.__args__ if t is not type(None))
                return EnvLoadable._convert_value(value, real_type)
        if target_type is bool:
            return value.lower() in ("1", "true", "yes", "on")
        if target_type is int:
            return int(value)
        if target_type is float:
            return float(value)
        if target_type is str:
            return value
        return value


class DictObject(dict):
    """
    use dict as object
    """

    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    # def __str__(self):    # for debug 
    #     old = super().__str__()
    #     return f'DictObject({old})'

    # def __repr__(self):    # for debug 
    #     old = super().__repr__()
    #     return f'DictObject({old})'

    @classmethod
    def trans_from_dict(cls, item: dict):
        """
        将 dict 循环转换为 DictObject
        :param item:
        :return:
        """
        dict_object = DictObject()
        for key, value in item.items():
            if isinstance(value, DictObject) or (not isinstance(value, dict)):
                dict_object[key] = value
            else:
                dict_object[key] = cls.trans_from_dict(value)

        return dict_object
