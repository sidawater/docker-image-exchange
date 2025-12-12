"""
Intent recognition related data structure definitions
"""

from typing import Literal, TypeGuard
from pydantic import BaseModel


class IntentRecognitionResult(BaseModel):
    """
    Intent recognition result

    Attributes:
        intent: Intent classification result, values are "general" or "it_operation"
    """
    intent: Literal["general", "it_operation"]

    @classmethod
    def is_valid_intent(cls, value: str) -> TypeGuard[Literal["general", "it_operation"]]:
        """
        Type guard: Check if the value is a valid intent type

        :param value: The value to check
        :return: Returns True if the value is a valid intent type, otherwise False
        """
        return value in {"general", "it_operation"}
