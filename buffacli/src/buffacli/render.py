import re
from datetime import datetime, timedelta
from enum import Enum

from buffacli.export import BaseExporter
from buffacli.formatters import FormatOptions
from buffacli.globals import console, vprint


class RenderOptions(str, Enum):
    """Available display modes for rendering content."""

    less = "less"
    shell = "shell"
    paginate = "paginate"
    default = ""


class Render:
    """
    Handles the rendering of API response content based on selected format
    and display mode (pager, shell, or direct print).
    """

    def __init__(self, formatter: FormatOptions, mode: str = None, page_size: int = None, exporter: BaseExporter = None):
        """
        Initialize the Render object with formatting and display options.

        :param formatter: The formatter object to transform raw content.
        :param mode: The display mode (less, shell, paginate).
        :param page_size: The number of objects per page for pagination mode.
        :param exporter: An optional exporter object for saving content to a file.
        """
        self.formatter = formatter
        self.mode = mode
        self.page_size = page_size
        self.exporter = exporter
        self.console = console

    def less(self, formatted_content: str):
        """Display the content using the terminal's built-in pager (e.g., 'less')."""
        vprint("debug", "Displaying output with less pager")
        with self.console.pager():
            self.console.print(formatted_content)

    def shell(self, formatted_content: str):
        """Render the content in a format suitable for shell scripting (e.g., raw JSON)."""
        # Logic for shell output goes here
        pass

    def paginate(self, formatted_content: str, page_size: int, caller: callable):
        """
        Display paginated API calls.

        :param formatted_content: The formatted API response for the first page.
        :param page_size: The number of objects per page.
        :param caller: A callable that returns the next page of the API response.
        """
        # Logic for paginated display goes here
        pass

    def __call__(self, content, mode: str = "", **formatter_kwargs):
        """
        The main rendering entry point. Decides how to display or export the content.

        :param content: The raw API response content object.
        :param mode: Overrides the mode set during initialization.
        :param formatter_kwargs: Additional keyword arguments passed to the formatter.
        """
        # If not a terminal, print raw content and exit
        if not self.console.is_terminal:
            print(content.raw)
            return

        # If an exporter is defined, export the content and exit
        if self.exporter:
            self.exporter.export(content)
            return

        # Format the content
        mode = self.mode or mode
        vprint("debug", f"Mode : {mode}")
        formatted_content = self.formatter(content, **formatter_kwargs)

        # Match the rendering mode
        match mode.lower():
            case "less":
                self.less(formatted_content)
            case "shell":
                self.shell(formatted_content)
            case "paginate":
                # For now defaults to direct print
                self.console.print(formatted_content)
            case _:
                self.console.print(formatted_content)


def make_renderable(format_option: FormatOptions, mode: str = "less", page_size: int = 50, exporter: BaseExporter = None) -> FormatOptions:
    """
    Attaches a Render object instance to the FormatOptions object's 'print' attribute
    and returns the updated FormatOptions.

    :param format_option: The FormatOptions object to update.
    :param mode: The default display mode for the renderer.
    :param page_size: The default pagination size.
    :param exporter: The default exporter object.
    :return: The updated FormatOptions object.
    """
    render = Render(format_option.formatter, mode=mode, page_size=page_size, exporter=exporter)
    format_option.print = render
    return format_option
