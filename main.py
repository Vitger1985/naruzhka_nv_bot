import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.client.session.aiohttp import AiohttpSession

# Включаем логирование, чтобы видеть всё в консоли хостинга
logging.basicConfig(level=logging.INFO)

# Инициализируем только диспетчер. Бота создадим внутри main()
dp = Dispatcher()

class AdminStates(StatesGroup):
    choosing_surface_for_price = State()
    entering_new_price = State()
    entering_broadcast_text = State()

# База данных рекламных поверхностей Нижневартовска
SURFACES = {
    1: {
        "name": "Цифровой экран 3х6 (Альберта Хаус)", 
        "type": "Цифровой экран", "size": "3х6", "side": "А", 
        "loc": "Нижневартовск (Альберта Хаус)", 
        "light": "Да", "status": "Свободно", "price": 35000, 
        "extra": "Выходов в сутки: 288\n▪️ *Блок:* 5 минут\n▪️ *Режим:* Круглосуточно",
        "photo": "https://unsplash.com", 
        "map_url": "https://yandex.ru"
    },
    2: {
        "name": "Цифровой экран 5х9 Северная х Интернациональная", 
        "type": "Цифровой экран", "size": "5х9", "side": "А", 
        "loc": "Пересечение ул. Северная и ул. Интернациональная", 
        "light": "Да", "status": "Свободно", "price": 45000, 
        "extra": "Выходов в сутки: 288\n▪️ *Блок:* 5 минут\n▪️ *Режим:* Круглосуточно",
        "photo": "https://unsplash.com", 
        "map_url": "https://yandex.ru"
    },
    3: {
        "name": "Цифровой экран 7х15 МФК Европа сити", 
        "type": "Цифровой экран", "size": "7х15", "side": "А", 
        "loc": "МФК Европа сити", 
        "light": "Да", "status": "Свободно", "price": 55000, 
        "extra": "Выходов в сутки: 288\n▪️ *Блок:* 5 минут\n▪️ *Режим:* Круглосуточно",
        "photo": "https://unsplash.com", 
        "map_url": "https://yandex.ru"
    },
    4: {
        "name": "Конструкция 4х18 ТЦ Подсолнух Сторона А", 
        "type": "Призматрон (динамическая, 3 стороны)", "size": "4х18", "side": "А", 
        "loc": "Возле ТЦ 'Подсолнух'", 
        "light": "Да", "status": "Свободно", "price": 80000, 
        "extra": "Тип конструкции: Динамическая трехсторонняя",
        "photo": "https://unsplash.com", 
        "map_url": "https://yandex.ru"
    },
    5: {
        "name": "Конструкция 4х18 ТЦ Подсолнух Сторона Б", 
        "type": "Призматрон (динамическая, 3 стороны)", "size": "4х18", "side": "Б", 
        "loc": "Возле ТЦ 'Подсолнух'", 
        "light": "Да", "status": "Свободно", "price": 80000, 
        "extra": "Тип конструкции: Динамическая трехсторонняя",
        "photo": "https://unsplash.com", 
        "map_url": "https://yandex.ru"
    },
}

USER_SUBSCRIBERS = set()

# Получаем ID админа глобально, но безопасно
ADMIN_ID_ENV = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_ENV) if ADMIN_ID_ENV and ADMIN_ID_ENV.isdigit() else 0

def get_main_menu():
    buttons = []
    for idx, item in SURFACES.items():
        buttons.append([InlineKeyboardButton(text=f"📦 {item['name']} — {item['price']}₽", callback_query_data=f"view_{idx}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    USER_SUBSCRIBERS.add(message.from_user.id)
    await message.answer(
        "👋 Приветствуем! Доступно 5 рекламных поверхностей для наружной рекламы в Нижневартовске.\nВыбирайте интересующий объект:",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data.startswith("view_"))
async def view_surface(callback: CallbackQuery):
    idx = int(callback.data.split("_")[1])
    item = SURFACES[idx]
    
    text = (
        f"📋 *{item['name']}*\n\n"
        f"▪️ *Тип:* {item['type']}\n"
        f"▪️ *Размер:* {item['size']} | *Сторона:* {item['side']}\n"
        f"▪️ *Локация:* {item['loc']}\n"
        f"▪️ *Подсветка:* {item['light']}\n"
        f"▪️ *Статус:* {item['status']}\n"
        f"▪️ {item['extra']}\n\n"
        f"💰 *Цена за месяц размещения:* {item['price']} руб.\n"
    )
    
    btn_book = InlineKeyboardButton(text="🤝 Забронировать", callback_query_data=f"book_{idx}")
    btn_map = InlineKeyboardButton(text="📍 Показать на карте", url=item['map_url'])
    btn_back = InlineKeyboardButton(text="⬅️ Назад в меню", callback_query_data="back_to_menu")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_book], [btn_map], [btn_back]])
    
    await callback.message.delete()
    try:
        photo_file = URLInputFile(item['photo'])
        await callback.message.answer_photo(photo=photo_file, caption=text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Не удалось загрузить фото по URL: {e}. Отправляем только текст.")
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Выбирайте интересующий объект:", reply_markup=get_main_menu())

@dp.callback_query(F.data.startswith("book_"))
async def book_surface(callback: CallbackQuery):
    idx = int(callback.data.split("_")[1])
    item = SURFACES[idx]
    
    if ADMIN_ID != 0:
        try:
            user = callback.from_user
            user_info = f"@{user.username}" if user.username else f"ID: {user.id}"
            await callback.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 *НОВАЯ ЗАЯВКА ОТ КЛИЕНТА!*\nПользователь {user_info} хочет забронировать объект:\n*{item['name']}*\nСтоимость: {item['price']} руб.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление администратору: {e}")
            
    await callback.answer("✅ Заявка отправлена! Менеджер свяжется с вами.", show_alert=True)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    await message.answer("🛠 *Панель администратора*\n\nКоманды:\n/price — Изменить цену объекта\n/broadcast — Сделать рассылку")

@dp.message(Command("price"))
async def cmd_price(message: Message):
    if message.from_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    buttons = []
    for idx, item in SURFACES.items():
        buttons.append([InlineKeyboardButton(text=item['name'], callback_query_data=f"editprice_{idx}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите объект для изменения цены:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("editprice_"))
async def select_price_object(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    await state.update_data(edit_idx=idx)
    await state.set_state(AdminStates.entering_new_price)
    await callback.message.answer(f"Введите новую цену (только цифры) для: {SURFACES[idx]['name']}")
    await callback.answer()

@dp.message(AdminStates.entering_new_price)
async def save_new_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ошибка! Введите цену только цифрами.")
        return
    data = await state.get_data()
    idx = data['edit_idx']
    new_price = int(message.text)
    SURFACES[idx]['price'] = new_price
    await state.clear()
    await message.answer(f"💰 Цена для *{SURFACES[idx]['name']}* изменена на {new_price}₽!", parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    await state.set_state(AdminStates.entering_broadcast_text)
    await message.answer("Введите текст объявления для рассылки всем:")

@dp.message(AdminStates.entering_broadcast_text)
async def start_broadcast(message: Message, state: FSMContext):
    text_to_send = message.text
    await state.clear()
    count = 0
    for user_id in USER_SUBSCRIBERS:
        try:
            await message.bot.send_message(chat_id=user_id, text=f"📢 *Объявление:*\n\n{text_to_send}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    await message.answer(f"📢 Рассылка завершена! Получили *{count}* пользователей.", parse_mode="Markdown")

async def main():
    # Извлекаем токен строго в момент старта функции
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        logging.error("❌ ОШИБКА: Переменная BOT_TOKEN пустая или не задана в BotHost!")
        return

    # Защитная очистка токена от случайных кавычек/пробелов при копировании
    bot_token = bot_token.strip().replace("'", "").replace('"', '')
        
    session = AiohttpSession()
    bot = Bot(token=bot_token, session=session)
    
    logging.info("🚀 Бот успешно инициализирован. Запуск polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())


