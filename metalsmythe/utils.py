import re
import datetime


def string_to_date(txt):
    """Tries to parse a datetime object from a string using a variety of patterns"""
    try:
        return datetime.datetime.fromisoformat(txt)
    except ValueError:
        pass

    try:
        return datetime.datetime.fromisoformat(txt.replace("Z", "+00:00"))
    except ValueError:
        pass

    # the patterns below are actually covered by fromisoformat()
    #try_patterns = [
    #    "%Y-%m-%d %H:%M:%S",
    #    "%Y-%m-%d"
    #]
    #for pattern in try_patterns:
    #    try:
    #        return datetime.datetime.strptime(txt, pattern)
    #    except ValueError:
    #        pass

    raise ValueError("Unable to parse string to date: '" + str(txt) + "'")


def format_date(obj, __format):
    """Calls format(obj, __format) on the object to convert dates to strings.
    This will first attempt to parse 'obj' as a datetime object in case it
    isn't one already.
    """
    if isinstance(obj, str):
        obj = string_to_date(obj)

    return format(obj, __format)


class GlobPattern(object):
    """Matches glob patterns to strings.  Examples:
        glob = GlobPattern(pattern)
        glob.is_match("path/to/file.md")

    This is done using regular expressions.  It's probably not 100% perfect,
    but it gets pretty close for patterns such as:

        *.md
        blog/*.md
        **/*.md

    NOTE: pathlib.PurePath(file).match(pattern) doesn't work the way I'd want.
    """
    def __init__(self, pattern):
        self.pattern = pattern
        self.cpattern = (
            pattern
            .replace(".", "\\.")  # escape periods
            .replace("**/", "([^/]<asterisk>/)<asterisk>")  # match zero or more path segments
            .replace("*", "[^/]*")  # match anything except '/' (zero or more occurs)
            .replace("<asterisk>", "*")
        )

    def is_match(self, path):
        return re.fullmatch(self.cpattern, path) is not None
