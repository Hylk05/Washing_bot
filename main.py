import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackQuery
from aiogram.types import Message

from bd_funcs import *
from help_funcs import check_correct_name, check_correct_room
from table_class import Table, DateCallback, MachineCallback, TimeCallback
from service_data import start_message, occupy_message, main_kb, check_occupied_msg, BOT_TOKEN, check_free_msg


dp = Dispatcher()
table = Table()

@dp.callback_query(DateCallback.filter())
async def process_datecallback(query: CallbackQuery, callback_data: DateCallback):
    if callback_data.cancel:
        user_data = get_user_info(query.message.chat.id)
        user_info = user_data[0] + " " + str(user_data[1])
        response = table.get_cancel_kb(callback_data, user_info)
        if not response:
            await query.message.edit_text("На эту дату у вас нет записей")
            await query.answer("Записей нет(")
        else:
            await query.message.edit_text("Выберите запись для отмены...", reply_markup=response)
    else:
        await query.message.edit_text("Выберите машинку...", reply_markup=table.get_machines_kb(callback_data)) #table.get_times(callback_data))
    await query.answer()

@dp.callback_query(MachineCallback.filter())
async def process_machinecallback(query: CallbackQuery, callback_data: MachineCallback):
    times = table.get_times_kb(callback_data)
    if times == "NO FREE TIME":
        await query.message.edit_text("Свободных мест нет😔\nПопробуйте другую дату или машинку...", reply_markup=table.kb_dates)
    else:
        await query.message.edit_text("Выберите свободное время...", reply_markup=table.get_times_kb(callback_data))
    await query.answer()

@dp.callback_query(TimeCallback.filter())
async def process_timecallback(query: CallbackQuery, callback_data: TimeCallback):
    if callback_data.cancel:
        edit = table.free_machine(callback_data)
        answer = check_free_msg
    else:
        user_data = get_user_info(query.message.chat.id)
        table.occupy_machine(callback_data, user_data)
        edit = occupy_message % (user_data[0], callback_data.date, callback_data.time.replace("-", ':'))
        answer = "Можете записаться снова ;)"
    await query.message.edit_text(edit, disable_web_page_preview=True)
    await query.message.answer(answer, reply_markup=table.kb_main, disable_web_page_preview=True)
    await query.answer()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(start_message % message.from_user.full_name)

@dp.message(Command("table"))
async def command_start_handler(message: Message) -> None:
    await message.answer(check_occupied_msg, disable_web_page_preview=True)

@dp.message()
async def echo_handler(message: Message) -> None:
    user_id = message.chat.id
    user_info = get_user_info(user_id)
    # НЕЗАРЕГАННЫЙ ЧТО-ТО НАПИСАЛ
    if not user_info:
        add_user(user_id)
        await message.answer("Вы не зарегистрированы :(\nДля этого напишите фамилию и имя👇")
        return
    elif not user_info[0]:
        name = check_correct_name(message.text)
        if not name:
            await message.answer("Пожалуйста, напишите фамилию и имя👇")
            return
        update_user_name(user_id, name)
        await message.answer("Теперь укажи номер комнаты👇")
        return
    elif not user_info[1]:
        room = check_correct_room(message.text)
        if not room:
            await message.answer("Пожалуйста, напишите номер комнаты👇")
            return
        update_user_room(user_id, room)
        await message.answer("Регистриция завершена :)\nЗаписаться на стирку можно с помощью кнопок",
                             reply_markup=table.kb_main)
        return
    # ЗАРЕГАНЫЙ НАЖАЛ НА КНОПКУ
    if message.text in main_kb:
        if message.text == main_kb[0]:
            await message.answer("Выберите доступную дату..." + "\n" + check_occupied_msg,
                                 reply_markup=table.kb_dates, disable_web_page_preview=True)
        elif message.text == main_kb[1]:
            await message.answer("Выберите дату отмены записи..." + "\n" + check_occupied_msg,
                                 reply_markup=table.kb_cancel_dates, disable_web_page_preview=True)
        return
    # ЗАРЕГАНЫЙ ЧТО-ТО НАПИСАЛ
    await message.answer("Записаться на стирку можно с помощью кнопок" + "\n" + check_occupied_msg,
                         reply_markup=table.kb_main, disable_web_page_preview=True)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

    scheduler = table.get_scheduler()
    scheduler.start()
    # run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())