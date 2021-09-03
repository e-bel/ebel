"""Generic methods for the models submodule."""
from sqlalchemy import inspect


def object_as_dict(obj, exclude: list = []) -> dict:
    """Return object values as a dictionary."""
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs if c.key not in exclude}
