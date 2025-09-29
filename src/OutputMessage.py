class OutputMessage:
    text = ""
    link = ""
    max_descr_size = 100

    def __init__(self, text, link):
        self.text = text.strip()
        self.link = link

    def __str__(self):
        return f"Desription: {self.text[:self.max_descr_size]}\nLink: {self.link}\n\n"



