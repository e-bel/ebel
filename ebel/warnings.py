"""Warning class definitions."""
from collections import OrderedDict

TEMPLATE = '{error_class}\tkeyword:{keyword}\tentry:{entry}\tline:{line_number}\tcolumn:{column}' \
           '\turl:{url}\thint:{hint}'


class _Warning:
    """Base class for all errors."""

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.value_dict = OrderedDict([
            ("warning_class", self.class_name),
            ("url", None),
            ("keyword", None),
            ("entry", None),
            ("line_number", None),
            ("column", None),
            ("hint", None)
        ])

    def to_dict(self):
        """Format the properties of error into a dictionary."""
        raise NotImplementedError('to_dict have to be implemented in {}'.format(self.__class__.__name__))

    def to_string(self) -> str:
        self.value_dict.update(self.to_dict())
        return TEMPLATE.format(**self.value_dict)

    def __str__(self):
        return self.to_string()


class AlsoUsedInOtherNamespace(_Warning):
    """Error in entry links to a namespace defined in the header but not exists in namespace url."""

    def __init__(self, keyword: str, entry: str, line_number: int, column: int, hint: str):
        """Initialize warning class.

        :param keyword: Error class type.
        :param hint: Sentence or string to give the user in the error report to help solve error.
        :param line_number: Line number where error was found.
        :param column: Column number where error was found.
        :param entry: String representation where error occurred.
        """
        super(AlsoUsedInOtherNamespace, self).__init__()

        self.ns_keyword = keyword
        self.entry = entry
        self.line_number = line_number
        self.column = column
        self.hint = hint

    def to_dict(self) -> dict:
        """Format the properties of error into a dictionary."""
        return {
            "error_class": self.class_name,
            "keyword": self.ns_keyword,
            "entry": self.entry,
            "line_number": self.line_number,
            "column": self.column,
            "hint": self.hint
        }
