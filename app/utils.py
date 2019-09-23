def validate_expire_in(s):
    """
    Raises ValueError if specified string is not numeric
    :param s: string to validate
    :return: None
    >>> validate_expire_in("123")
    >>>
    >>> validate_expire_in("123test")
    Traceback (most recent call last):
    ValueError
    """
    if not s.isnumeric():
        raise ValueError()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
