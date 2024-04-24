class DataRegistryError(Exception):
    """Base class for exceptions from within this module"""


class RecoverableException(DataRegistryError):
    """Raised if the failure is expected to be temporary: for example, a service's API is temporarily unavailable."""


class LockFileError(DataRegistryError):
    """Raised if a lock file exists."""
