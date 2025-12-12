"""
Environment variable based configuration loader.
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
    """
    Create a dataclass field with environment variable metadata.

    :param default: Default value for the field
    :param default_factory: Factory function for default values
    :param env: Environment variable name to load from
    :return: dataclass field with metadata
    """
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
    """
    Base class for loading configuration from environment variables.

    Usage Sample::

        @dataclass
        class Config(EnvLoadable):
            host: str = Attr(default='localhost', env='HOST')
            port: int = Attr(default=8080, env='PORT')

        config = Config.load_from_env()
    """

    @classmethod
    def load_from_env(cls):
        """
        Load configuration from environment variables.

        :return: Instance with values loaded from environment
        """
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
        """
        Convert string value from environment to target type.

        :param value: String value from environment
        :param target_type: Target type to convert to
        :return: Converted value
        """
        origin = getattr(target_type, "__origin__", None)
        if origin is Optional or origin is type(Optional[int]):
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
