class DataRegistryError(Exception):
    """Base class for exceptions from within this module"""


class RecoverableException(DataRegistryError):
    """Raised if the failure is expected to be temporary."""


class IrrecoverableError(DataRegistryError):
    """Raised if the failure is permanent but not unexpected."""


class LockFileError(DataRegistryError):
    """Raised if a lock file exists."""
