from typing import Any
from uuid import UUID
from enum import Enum
from decimal import Decimal
import datetime
import json

class DefaultEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        if isinstance(o, datetime.timedelta):
            o.total_seconds()
        if isinstance(o, (Decimal, UUID)):
            return str(o)

        if isinstance(o, (set, frozenset)):
            return list(o)

        if isinstance(o, Enum):
            return o.value

        if callable(getattr(o, "model_dump", None)):
            return getattr(o, "model_dump")()

        return str(o)
