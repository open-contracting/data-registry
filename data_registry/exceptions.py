class DataRegistryError(Exception):
    """Base class for exceptions from within this module"""


class RecoverableException(DataRegistryError):
    """Raised if the failure is expected to be temporary. For example, a request to a service's API might only be
    expected to fail if the service is temporarily unavailable."""


class LockFileError(DataRegistryError):
    """Raised if a lock file exists."""
