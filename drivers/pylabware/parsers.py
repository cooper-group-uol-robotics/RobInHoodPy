"""pylabware utility functions for reply parsing"""

import re


def slicer(reply: str, *args) -> str:
    """This is a wrapper function for reply parsing to provide consistent
    arguments order.

    Args:
        reply: Sequence object to slice.

    Returns:
        (any): Slice of the original object.
    """

    return reply[slice(*args)]


def researcher(reply, *args):
    """This is a wrapper function for reply parsing to provide consistent
    arguments order.

    Args:
        reply: Reply to parse with regular expression.

    Returns:
        (re.Match): Regular expression match object.
    """

    return re.search(*args, reply)

def findall_parser(reply: str, regex: str) -> list:
    """
    This is a wrapper around findall - provides list of tuples of groups of 
    regex

    Args: 
        reply: Reply to parse with a regular expression
        regex: regular expression

    Returns:
        A list of non-overlapping matches. Empty list if no match. List of tuples if regex had groups.

    """
    re.findall(regex, reply)
    findall_ouput = []





    return re.findall(regex, reply)

def findall_stripper(raw_findall: str) -> list:

    out_list = []
    
    for inner_list in raw_findall:
        for item in inner_list:
            if item != '':
                out_list.append(item)

    return out_list



def stripper(reply: str, prefix=None, suffix=None) -> str:
    """This is a helper function used to strip off reply prefix and
    terminator. Standard Python str.strip() doesn't work reliably because
    it operates on character-by-character basis, while prefix/terminator
    is usually a group of characters.

    Args:
        reply: String to be stripped.
        prefix: Substring to remove from the beginning of the line.
        suffix: Substring to remove from the end of the line.

    Returns:
        (str): Naked reply.
    """

    if prefix is not None and reply.startswith(prefix):
        reply = reply[len(prefix) :]

    if suffix is not None and reply.endswith(suffix):
        reply = reply[: -len(suffix)]

    return reply


def left_strip(reply: str, char: str) -> str:
    """This is a helper function for stripping off left leading characters in replies.
    Often this is for leading zeros.

    Args:
        reply: String to be stripped
        char: Character to be removed

    Returns:
        (str): Naked reply.
    """

    reply = reply.lstrip(char)

    return reply
