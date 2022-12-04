import re


def is_alphanumeric_lowercase_nonempty(candidate):
    if not isinstance(candidate, str):
        return False
    else:
        lowercase_alphanumeric_nonempty = re.compile("[a-z]+")
        return lowercase_alphanumeric_nonempty.fullmatch(candidate) is not None
