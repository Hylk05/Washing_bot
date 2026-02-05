from aiogram.utils.keyboard import ReplyKeyboardBuilder
from service_data import main_kb

class Keyboard():
    def __init__(self):
        self.main_buttons = main_kb
        self.main = 0
        self.dates = 0
        self.times = 0

    def update_main_kb(self):
        builder = ReplyKeyboardBuilder()
        for button in self.main_buttons:
            builder.button(text=button)
        builder.adjust(1, 3)

        self.main = builder.as_markup()

    def update_date_kb(self, dates: list):
        builder = ReplyKeyboardBuilder()
        for date in dates:
            builder.button(text=date)
        builder.adjust(2, 3)

        self.dates = builder.as_markup()

    def update_times_kb(self, times: list):
        builder = ReplyKeyboardBuilder()
        for date in times:
            builder.button(text=date)
        builder.adjust(2, 3)

        self.times = builder.as_markup()