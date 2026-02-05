import gspread
from datetime import datetime, date, timedelta
import locale
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from service_data import SERVICE_ACCOUNT_FILENAME, get_month
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData, CallbackQuery
from service_data import main_kb, machines_kb, times_rows, cancel_rows, cancel_cols

locale.setlocale(locale.LC_TIME, 'ru')   # чтобы месяц в datetime по-русски писался

scheduler = AsyncIOScheduler()

gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILENAME)
washing_sh = gc.open_by_key("1zzDqgjeGJi-727oqofMmWJekHm_8TveNYZvP-ju7gJo")
reference_sh = gc.open_by_key("1_4AdbHAg-iNajRjOHl2cK7zZqPkXGr2NJBFvOEc6fTI")
reference_wsh = reference_sh.get_worksheet_by_id(0)

class DateCallback(CallbackData, prefix="wash date"):
    cancel: bool
    date: str

class MachineCallback(CallbackData, prefix="wash cells"):
    cancel: bool
    date: str
    cells: str
    machine: str

class TimeCallback(CallbackData, prefix="wash time"):
    cancel: bool
    date: str
    cells: str
    machine: str
    time: str

class Table:
    def __init__(self):
        self.update_dates()
        self.kb_main = self.create_main_kb()

        scheduler.add_job(self.update_sheets,'cron', hour=5, id='daily_sheet_updating', next_run_time=datetime.now())

    def update_dates(self):
        self.dates = [i.title for i in washing_sh.worksheets()]

        builder = InlineKeyboardBuilder()
        builder_cancel = InlineKeyboardBuilder()
        for date in self.dates:
            builder.button(text=date, callback_data=DateCallback(date=date, cancel=False).pack())
            builder_cancel.button(text=date, callback_data=DateCallback(date=date, cancel=True).pack())
        builder.adjust(2, 3)
        builder_cancel.adjust(2, 3)

        self.kb_dates = builder.as_markup()
        self.kb_cancel_dates = builder_cancel.as_markup()

    async def update_sheets(self):
        today = date.today()
        new_date = today + timedelta(days=4)
        new_title = new_date.strftime("%d") + " " + get_month(new_date.strftime("%m"))

        yesterday = today - timedelta(days=1)
        yesterday_title = yesterday.strftime("%d") + " " + get_month(yesterday.strftime("%m"))

        if yesterday_title in self.dates:
            yesterday_sh = washing_sh.worksheet(yesterday_title)
            washing_sh.del_worksheet_by_id(yesterday_sh.id)
        if new_title not in self.dates:
            new_sh_data = reference_wsh.copy_to(destination_spreadsheet_id=washing_sh.id)
            new_sh = washing_sh.get_worksheet_by_id(new_sh_data["sheetId"])
            new_sh.update_title(new_title)
        self.update_dates()

    @staticmethod
    def get_scheduler():
        return scheduler

    @staticmethod
    def create_main_kb():
        builder = ReplyKeyboardBuilder()
        for button in main_kb:
            builder.button(text=button)
        builder.adjust(2, 3)

        return builder.as_markup()

    @staticmethod
    def get_machines_kb(callback_data: DateCallback):
        builder = InlineKeyboardBuilder()
        for machine, cells in machines_kb.items():
            builder.button(text=machine, callback_data=MachineCallback(cells=cells, date=callback_data.date, cancel=False, machine=machine).pack())
        builder.adjust(2, 3)

        return builder.as_markup()

    @staticmethod
    def get_cancel_kb(callback_data: DateCallback, user_info: str):
        date = callback_data.date
        wsh = washing_sh.worksheet(date)

        cell_list = wsh.findall(user_info)
        if not cell_list:
            return None
        print(cell_list, print(cell_list[0]), print(type(cell_list[0])))

        builder = InlineKeyboardBuilder()
        for cell in cell_list:
            time, machine = cancel_rows[cell.row], cancel_cols[cell.col]
            builder.button(text=time + " " + machine,
                           callback_data=TimeCallback(cells=cell.address, date=date,
                                                      time=time.replace(':', '-'),
                                                      cancel=True, machine=machine).pack())
        return builder.as_markup()

    @staticmethod
    def get_times_kb(callback_data: MachineCallback):
        cells = callback_data.cells.replace("-", ":")
        date = callback_data.date

        wsh = washing_sh.worksheet(date)
        data = wsh.get(cells)

        builder = InlineKeyboardBuilder()
        free_times = 0
        for time in data:
            if len(time) < 2:
                free_times += 1
                builder.button(text=time[0],
                               callback_data=TimeCallback(cells=callback_data.cells, date=date,
                                                          time=time[0].replace(':', '-'),
                                                          cancel=False, machine=callback_data.machine).pack())
        if not free_times:
            return "NO FREE TIME"

        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def free_machine(callback_data: TimeCallback):
        date = callback_data.date
        address = callback_data.cells

        wsh = washing_sh.worksheet(date)
        wsh.update_acell(address, " ")
        return "Запись успешно отменена!"

    @staticmethod
    def occupy_machine(callback_data: TimeCallback, user_data: tuple):
        date = callback_data.date
        time_cell = callback_data.cells[3] + times_rows[callback_data.time]

        wsh = washing_sh.worksheet(date)
        wsh.update_acell(time_cell, user_data[0] + " " + str(user_data[1]))