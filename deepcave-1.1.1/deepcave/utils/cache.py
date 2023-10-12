from typing import Any, Dict, Optional

import json
import logging
from copy import deepcopy
from pathlib import Path

from deepcave.utils.compression import JSON_DENSE_SEPARATORS
from deepcave.utils.logs import get_logger
from deepcave.utils.util import short_string

logger = get_logger(__name__)


class Cache:
    """
    Cache handles a json file. Decided not to use flask_caching
    since code is easier to change to our needs.
    """

    def __init__(
        self,
        filename: Optional[Path] = None,
        defaults: Dict = None,
        debug: bool = False,
        write_file: bool = True,
    ) -> None:
        self._defaults = {} if defaults is None else defaults

        # Fields set by self._setup()
        self._data: Dict[Any, Any] = {}
        self._filename: Optional[Path] = None
        self._debug = debug

        # Initial setup
        self._setup(filename, write_file)

    def _setup(self, filename: Optional[Path], write_file: bool = True) -> None:
        self._data = {}
        self._filename = filename

        if filename is None or not filename.exists():
            self.set_dict(self._defaults, write_file=write_file)
        else:
            self.read()

    def read(self) -> None:
        """Reads content from a file and load into cache as dictionary."""
        if self._filename is None or not self._filename.exists():
            return

        with self._filename.open("r") as f:
            self._data = self._defaults.copy()
            self._data.update(json.load(f))

    def write(self) -> None:
        """Write content of cache into file."""
        if self._filename is None:
            return

        self._filename.parent.mkdir(exist_ok=True, parents=True)
        with self._filename.open("w") as f:
            if self._debug:
                json.dump(self._data, f, indent=4)
            else:
                json.dump(self._data, f, separators=JSON_DENSE_SEPARATORS)

    def set(self, *keys, value: Any, write_file: bool = True) -> None:
        """
        Set a value from a chain of keys.
        E.g. set("a", "b", "c", value=4) creates following dictionary:
        {"a": {"b": {"c": 4}}}
        """
        name = "(empty)"
        if self._filename is not None:
            name = self._filename.name

        logger.debug(
            f"{name}: Set \"{','.join(keys)}\" to \"{short_string(value, 60, mode='suffix')}\"."
        )
        d = self._data
        for key in keys[:-1]:
            if type(key) != str:
                raise RuntimeError("Key must be a string. Ints/floats are not supported by JSON.")

            if key not in d:
                d[key] = {}

            d = d[key]

        d[keys[-1]] = value
        if write_file:
            self.write()

    def set_dict(self, d: Dict, write_file: bool = True) -> None:
        """Updates cache to a specific value"""
        self._data.update(d)

        if write_file:
            self.write()

    def get(self, *keys) -> Optional[Any]:
        """Retrieve value for a specific key"""
        d = deepcopy(self._data)
        for key in keys:
            if key not in d:
                return None

            d = d[key]

        return d

    def has(self, *keys) -> bool:
        """Check whether cache has specific key"""
        d = self._data
        for key in keys:
            if key not in d:
                return False
            d = d[key]

        return True

    def clear(self, write_file: bool = True) -> None:
        """Clear all cache and reset to defaults"""
        filename = self._filename

        if filename is not None and filename.exists():
            self._filename.unlink()

        self._setup(filename, write_file=write_file)
