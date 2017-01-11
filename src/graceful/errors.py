from falcon import HTTPBadRequest, HTTPInvalidParam


class DeserializationError(ValueError):
    """Raised when error happened during deserialization of representation."""

    def __init__(
            self, missing=None, forbidden=None, invalid=None, failed=None
    ):
        """Initialize exception instance."""
        self.missing = missing
        self.forbidden = forbidden
        self.invalid = invalid
        self.failed = failed

    def as_bad_request(self):
        """Translate this error to falcon's HTTP specific error exception."""
        return HTTPBadRequest(
            title="Representation deserialization failed",
            description=self._get_description()
        )

    def _get_description(self):
        """Return human readable description error description.

        This description should explain everything that went wrong during
        deserialization.

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
    """Raised when validation error occured."""

    def as_bad_request(self):
        """Translate this error to falcon's HTTP specific error exception.

        Note:
            Exceptions returned by this method should be used to inform about
            resource validation failures. In case of param validation
            failures the ``as_invalid_param()`` method should be used.

        """
        return HTTPBadRequest(
            title="Validation failed",
            description=str(self)
        )

    def as_invalid_param(self, param_name):
        """Translate this error to falcon's HTTP specific error exception.

        Note:
            Exceptions returned by this method should be used to inform about
            param validation failures. In case of resource validation
            failures the ``as_bad_request()`` method should be used.

        Args:
            param_name (str): HTTP query string parameter name

        """
        return HTTPInvalidParam(
            str(self), param_name
        )
