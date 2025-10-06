import re


class OutputMessage:
    def __init__(self, text, link, max_descr_size=100):
        self.text = re.sub("\n+", "\n", text.strip())
        self.link = link
        self.max_descr_size = max_descr_size

    def format_str(self, max_descr_size: int) -> str:
        return f"Desription: {self.text[:max_descr_size]}\n" \
               f"Link: {self.link}\n\n"

    def __str__(self):
        return self.format_str(self.max_descr_size)


