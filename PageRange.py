from Page import *

class PageRange:
    def __init__(self, range_config):
        self.data = []
        self.range_config = range_config
        self.pages = Page(range_config)
