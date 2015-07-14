# -*- coding: utf-8 -*-
from falcon import HTTPBadRequest


class DeserializationError(ValueError):
    """
    Raised when error happened during deserialization of object
    """
    def __init__(
            self, missing=None, forbidden=None, invalid=None, failed=None
    ):
        self.missing = missing
        self.forbidden = forbidden
        self.invalid = invalid
        self.failed = failed

    def as_bad_request(self):
        return HTTPBadRequest(
            title="Representation deserialization failed",
            description=self._get_description()
        )

    def _get_description(self):
        """
        Return human readable description that explains everything that
        went wrong with deserialization.

        """
        return ", ".join([
            part for part in [
                "missing: {}".format(self.missing) if self.missing else "",
                (
                    "forbidden: {}".format(self.forbidden)
                    if self.forbidden else ""
                ),
                "invalid: {}:".format(self.invalid) if self.invalid else "",
                (
                    "failed to parse: {}".format(self.failed)
                    if self.failed else ""
                )
            ] if part
        ])


class ValidationError(ValueError):
    """Raised when validation error occured"""
    def as_bad_request(self):
        return HTTPBadRequest(
            title="Validation failed deserialization failed",
            description=str(self)
        )
