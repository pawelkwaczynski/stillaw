"""Stillaw: is this still the law?

Resolves whether a Polish consolidated statute text is current, superseded, or waiting in
vacatio legis, from the ELI API of the Dziennik Ustaw alone. No language model in the loop.
"""
__version__ = "0.1.0"

STATUSES = ("current", "superseded", "vacatio_legis", "undetermined")
