class RecoverableException(Exception):
    """
    The exception should be thrown in cases when the task failed, but the reason for the fall is not critical
    (e.g. temporary service unavailability) and the task can be performed in the next iteration.
    """
    pass
