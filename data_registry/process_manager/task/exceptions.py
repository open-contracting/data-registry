class RecoverableException(Exception):
    """
    Raised when it is expected that the failure is temporary. For example, a request to a service's API might only be
    expected to fail if the service is temporarily unavailable.
    """
