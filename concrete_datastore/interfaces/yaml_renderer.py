# coding: utf-8
class DatamodelYamlToHtml:
    """
    This class renders a json into a yaml format for html input.
    A JSON content should be given to this class.
    The return value of the "render_yaml()" method can be used in a HTML
    template as follows:
        <pre>{{ rendered_result | safe }}</pre>
    """

    bool_color = "#bc3753"
    string_color = "#0a6969"

    def __init__(self, content, indent=4):
        self.indent = indent
        self.json_content = content

    def format_with_color(self, val, color=None):
        if not val:
            val = '""'
        if color is not None:
            return f'<span style="color:{color}">{val}</span>'
        return f'<span>{val}</span>'

    def _render_yaml(self, content, indent_counter, is_list=False):
        if isinstance(content, bool):
            str_value = str(content).lower()
            v = self.format_with_color(val=str_value, color=self.bool_color)
            if is_list is True:
                v = f'{" " * (indent_counter) * self.indent}- {v}'
            return f'{v}\n'
        if content is None:
            v = self.format_with_color(val='null', color=self.bool_color)
            if is_list is True:
                v = f'{" " * (indent_counter) * self.indent}- {v}'
            return f'{v}\n'
        if isinstance(content, list):
            if len(content) == 0:
                return self.format_with_color("[]\n")
            return_value = ''.join(
                [
                    self._render_yaml(
                        elt, indent_counter=indent_counter, is_list=True
                    )
                    for elt in content
                ]
            )
            return f'\n{return_value}'
        if isinstance(content, dict):
            if not content:
                return self.format_with_color("{}\n")
            v = "\n"
            for key, value in content.items():
                formatted_key = self.format_with_color(key)
                add_list_counter = 0
                if is_list:
                    add_list_counter = 1
                value_indent_counter = indent_counter + add_list_counter + 1

                formatted_value = self._render_yaml(
                    content=value, indent_counter=value_indent_counter
                )
                if is_list:
                    v = f'{" " * (indent_counter) * self.indent}- {formatted_key}: {formatted_value}'
                    is_list = False
                    indent_counter += 1
                else:
                    v = f'{v}{" " * indent_counter * self.indent}{formatted_key}: {formatted_value}'
            return v

        v = self.format_with_color(val=content, color=self.string_color)
        if is_list is True:
            v = f'{" " * (indent_counter) * self.indent}- {v}'
        return f'{v}\n'

    def render_yaml(self):
        return self._render_yaml(content=self.json_content, indent_counter=0)
