import asyncio
import math
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==================== НАСТРОЙКИ БОТА ====================
API_TOKEN = '8613701511:AAEdc67CjsPcmIT7wB4UylX_VQF1iRX3Dhg'

# Данные вашей карты для перевода (получатель убран)
CARD_NUMBER = "4441 1144 3532 9550"  # Укажите номер карты
BANK_NAME = "Monobank "   # Название банка

# Курс Telegram Stars к грн (1 Star ≈ 0.9 грн)
STAR_RATE_UAH = 0.9
# =======================================================

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# База данных выбранного языка пользователей (в памяти)
user_languages = {}

# Прайс-листы
PRICES = {
    "roblox": [
        {"id": "r_100", "amount": 100, "price_uah": 29},
        {"id": "r_250", "amount": 250, "price_uah": 70},
        {"id": "r_500", "amount": 500, "price_uah": 150},
        {"id": "r_1000", "amount": 1000, "price_uah": 300},
        {"id": "r_5000", "amount": 5000, "price_uah": 999},
        {"id": "r_10000", "amount": 10000, "price_uah": 1800},
    ],
    "standoff": [
        {"id": "s_100", "amount": 100, "price_uah": 67},
        {"id": "s_250", "amount": 250, "price_uah": 150},
        {"id": "s_500", "amount": 500, "price_uah": 300},
        {"id": "s_1000", "amount": 1000, "price_uah": 550},
        {"id": "s_3000", "amount": 3000, "price_uah": 1200},
        {"id": "s_5000", "amount": 5000, "price_uah": 1700},
        {"id": "s_8000", "amount": 8000, "price_uah": 2400},
        {"id": "s_10000", "amount": 10000, "price_uah": 3000},
    ]
}

def find_item_by_id(item_id: str):
    for game_items in PRICES.values():
        for item in game_items:
            if item["id"] == item_id:
                return item
    return None

# ----- КЛАВИАТУРЫ -----

def lang_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Українська", callback_data="lang_ua")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.adjust(2)
    return builder.as_markup()

def games_keyboard(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔵 Roblox (Робукси)" if lang == "ua" else "🔵 Roblox (Робуксы)", callback_data="game_roblox")
    builder.button(text="🟡 Standoff 2 (Голда)", callback_data="game_standoff")
    builder.adjust(1)
    return builder.as_markup()

def prices_keyboard(game: str, lang: str):
    builder = InlineKeyboardBuilder()
    unit = "R$" if game == "roblox" else "G"
    
    for item in PRICES[game]:
        builder.button(
            text=f"{item['amount']} {unit} — {item['price_uah']} грн",
            callback_data=f"item_{item['id']}"
        )
    
    builder.button(text="⬅ Назад", callback_data="back_to_games")
    builder.adjust(1)
    return builder.as_markup()

def payment_methods_keyboard(item_id: str, lang: str):
    builder = InlineKeyboardBuilder()
    
    if lang == "ua":
        builder.button(text="💳 Переказ на карту (від 100 грн)", callback_data=f"pay_card_{item_id}")
        builder.button(text="⭐ Telegram Stars (+15% комісія)", callback_data=f"pay_stars_{item_id}")
        builder.button(text="⬅ Назад", callback_data="back_to_games")
    else:
        builder.button(text="💳 Перевод на карту (от 100 грн)", callback_data=f"pay_card_{item_id}")
        builder.button(text="⭐ Telegram Stars (+15% комиссия)", callback_data=f"pay_stars_{item_id}")
        builder.button(text="⬅ Назад", callback_data="back_to_games")
        
    builder.adjust(1)
    return builder.as_markup()


# ----- ОБРАБОТЧИКИ КОМАНД И НАЖАТИЙ -----

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Оберіть мову / Выберите язык:",
        reply_markup=lang_keyboard()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def select_language(callback: types.CallbackQuery):
    await callback.answer()
    lang = callback.data.replace("lang_", "")
    user_languages[callback.from_user.id] = lang
    
    text = "Оберіть гру:" if lang == "ua" else "Выберите игру:"
    await callback.message.edit_text(text, reply_markup=games_keyboard(lang))

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: types.CallbackQuery):
    await callback.answer()
    lang = user_languages.get(callback.from_user.id, "ru")
    text = "Оберіть гру:" if lang == "ua" else "Выберите игру:"
    await callback.message.edit_text(text, reply_markup=games_keyboard(lang))

@dp.callback_query(F.data.startswith("game_"))
async def select_game(callback: types.CallbackQuery):
    await callback.answer()
    game = callback.data.replace("game_", "")
    lang = user_languages.get(callback.from_user.id, "ru")
    
    text = "Оберіть потрібну суму:" if lang == "ua" else "Выберите нужную сумму:"
    await callback.message.edit_text(text, reply_markup=prices_keyboard(game, lang))

@dp.callback_query(F.data.startswith("item_"))
async def select_item(callback: types.CallbackQuery):
    await callback.answer()
    item_id = callback.data.replace("item_", "")
    lang = user_languages.get(callback.from_user.id, "ru")
    item = find_item_by_id(item_id)
    
    if not item:
        return

    currency_name = "Робуксів" if "r_" in item_id else "Голди"
    if lang == "ru":
        currency_name = "Робуксов" if "r_" in item_id else "Голды"

    if lang == "ua":
        text = f"Ви обрали: **{item['amount']} {currency_name}** ({item['price_uah']} грн)\n\nОберіть спосіб оплати:"
    else:
        text = f"Вы выбрали: **{item['amount']} {currency_name}** ({item['price_uah']} грн)\n\nВыберите способ оплаты:"

    await callback.message.edit_text(text, reply_markup=payment_methods_keyboard(item_id, lang), parse_mode="Markdown")

# --- Оплата Переводом на Карту ---
@dp.callback_query(F.data.startswith("pay_card_"))
async def pay_card(callback: types.CallbackQuery):
    await callback.answer()
    item_id = callback.data.replace("pay_card_", "")
    item = find_item_by_id(item_id)
    lang = user_languages.get(callback.from_user.id, "ru")

    if item['price_uah'] < 100:
        err_msg = "⚠️ Оплата переводом на карту доступна только для заказов от 100 грн!" if lang == "ru" else "⚠️ Оплата переказом на карту доступна тільки для замовлень від 100 грн!"
        await callback.message.answer(err_msg)
        return

    if lang == "ua":
        text = (
            f"💳 **Оплата переказом на карту**\n\n"
            f"Сума до сплати: **{item['price_uah']} грн**\n\n"
            f"📌 **Реквізити:**\n"
            f"Банк: **{BANK_NAME}**\n"
            f"Номер карти: `{CARD_NUMBER}`\n\n"
            f"⚠️ **Після сплати:** Надішліть скріншот чека у цей чат!"
        )
    else:
        text = (
            f"💳 **Оплата переводом на карту**\n\n"
            f"Сумма к оплате: **{item['price_uah']} грн**\n\n"
            f"📌 **Реквизиты:**\n"
            f"Банк: **{BANK_NAME}**\n"
            f"Номер карты: `{CARD_NUMBER}`\n\n"
            f"⚠️ **После оплаты:** Отправьте скриншот чека в этот чат!"
        )

    await callback.message.edit_text(text, parse_mode="Markdown")

# --- Оплата Telegram Stars (+15% комиссия) ---
@dp.callback_query(F.data.startswith("pay_stars_"))
async def pay_stars(callback: types.CallbackQuery):
    await callback.answer()
    item_id = callback.data.replace("pay_stars_", "")
    item = find_item_by_id(item_id)

    # Расчет звёзд с +15% комиссией
    base_stars = item['price_uah'] / STAR_RATE_UAH
    stars_with_fee = math.ceil(base_stars * 1.15)

    game_title = "Roblox Robux" if "r_" in item_id else "Standoff 2 Gold"

    prices = [types.LabeledPrice(label=f"{item['amount']} ({game_title})", amount=stars_with_fee)]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Покупка {item['amount']} ({game_title})",
        description=f"Оплата {item['amount']} с учётом комиссии +15%",
        payload=f"stars_{item_id}",
        provider_token="",
        currency="XTR",
        prices=prices
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    lang = user_languages.get(message.from_user.id, "ru")
    
    if lang == "ua":
        msg = "🎉 **Оплата Stars пройшла успішно!**\n\nНадішліть дані для отримання товару в цей чат."
    else:
        msg = "🎉 **Оплата Stars прошла успешно!**\n\nОтправьте данные для получения товара в этот чат."
        
    await message.answer(msg, parse_mode="Markdown")

async def main():
    print("Бот-магазин запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
