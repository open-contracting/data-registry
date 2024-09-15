class DataRegistryError(Exception):
    """Base class for exceptions from within this module"""


class ConfigurationError(DataRegistryError):
    """Raised if the project is misconfigured."""


class UnexpectedError(DataRegistryError):
    """Raised if the failure is unexpected."""


class RecoverableError(DataRegistryError):
    """Raised if the failure is expected to be temporary."""


class IrrecoverableError(DataRegistryError):
    """Raised if the failure is permanent but not unexpected."""


class LockFileError(DataRegistryError):
    """Raised if a lock file exists."""
