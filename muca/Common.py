"""This are common used definitions and statements."""

def build():
    """This function just returns the program version.

    This should be a global constant but global values are defined only for a
    module. To make the vesion number available ta all modules, this function
    is importable.
    """
    return '2'

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
