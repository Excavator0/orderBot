from PIL import Image
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ShippingOption, ShippingQuery, LabeledPrice, PreCheckoutQuery, CallbackQuery, \
    InputMediaPhoto
from aiogram import Router, F

from database.db import Database
from image_processing import paste, image_to_bytes
from messages import MESSAGES
from config import PAYMENTS_TOKEN, ADMIN_ID

router = Router()

colors = {(20, 20, 20): "Чёрный", (232, 232, 232): "Белый", (176, 37, 37): "Красный", (224, 208, 58): "Жёлтый",
          (24, 54, 122): "Синий", "magenta": "Фиолетовый"}
shipping_types = {"superspeed": "Супер быстрая", "post": "Почта Росии", "pickup": "Самовывоз"}

PRICES = [
    LabeledPrice(label='Футболка с принтом', amount=10000),
]

SUPERSPEED_SHIPPING_OPTION = ShippingOption(
    id='superspeed',
    title='Супер быстрая!',
    prices=[
        LabeledPrice(
            label='Лично в руки!',
            amount=50000
        )
    ]
)

POST_SHIPPING_OPTION = ShippingOption(
    id='post',
    title='Почта России',
    prices=[
        LabeledPrice(
            label='Картонная коробка',
            amount=10000
        ),
        LabeledPrice(
            label='Срочное отправление!',
            amount=30000
        )
    ]
)

PICKUP_SHIPPING_OPTION = ShippingOption(
    id='pickup',
    title='Самовывоз',
    prices=[
        LabeledPrice(
            label='Самовывоз в Санкт-Петербурге',
            amount=15000
        )
    ]
)


@router.callback_query(F.data == "checkout")
async def buy_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = data["order_type"]
    await callback.message.delete()
    await callback.message.answer_invoice(
        title=MESSAGES[item]['item_title'],
        description=MESSAGES[item]['item_description'],
        provider_token=PAYMENTS_TOKEN,
        currency='rub',
        need_email=True,
        need_phone_number=True,
        is_flexible=True,
        prices=PRICES,
        start_parameter='example',
        payload='some_invoice')


@router.shipping_query(lambda q: True)
async def shipping_process(shipping_query: ShippingQuery):
    shipping_options = [SUPERSPEED_SHIPPING_OPTION]

    if shipping_query.shipping_address.country_code == 'RU':
        shipping_options.append(POST_SHIPPING_OPTION)

        if shipping_query.shipping_address.city == 'Санкт-Петербург':
            shipping_options.append(PICKUP_SHIPPING_OPTION)

    await shipping_query.bot.answer_shipping_query(
        shipping_query.id,
        ok=True,
        shipping_options=shipping_options

    )


@router.pre_checkout_query(lambda q: True)
async def checkout_process(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    image = Image.open(f"prints/{user_id}.png")
    item = data["order_type"]
    color = data["color"]
    print_pos = data["pos"]
    bg_deleted = data["bg_deleted"]
    angle = data["angle"]
    size = data["size"]
    size_order = data["order_size"]

    await message.answer(
        MESSAGES[item]['successful_payment'].format(total_amount=message.successful_payment.total_amount // 100,
                                                    currency=message.successful_payment.currency)
    )
    await state.clear()
    # отправка админу
    image1 = image.resize(tuple(size[0]), Image.Resampling.BICUBIC)
    front = paste(image1, color, print_pos[0], item, 0, angle[0], bg_deleted[0])
    file1 = image_to_bytes(front)
    file1 = InputMediaPhoto(media=file1)

    if print_pos[1][0] == -1:
        print_pos[1] = "deleted"

    image2 = image.resize(tuple(size[1]), Image.Resampling.BICUBIC)
    back = paste(image2, color, print_pos[1], item, 1, angle[1], bg_deleted[1])
    file2 = image_to_bytes(back)
    file2 = InputMediaPhoto(media=file2)
    await message.bot.send_message(chat_id=ADMIN_ID, text=f"Новый заказ!\n{PRICES[0].label}\nЦвет {colors.get(color)}\n"
                                                          f"Размер: {size_order.upper()}\n"
                                                          f"Адрес: {message.successful_payment.order_info.shipping_address.state}, "
                                                          f"{message.successful_payment.order_info.shipping_address.city}, "
                                                          f"{message.successful_payment.order_info.shipping_address.street_line1} "
                                                          f"{message.successful_payment.order_info.shipping_address.street_line2}, "
                                                          f"{message.successful_payment.order_info.shipping_address.post_code}.\n"
                                                          f"Вариант доставки: {shipping_types.get(message.successful_payment.shipping_option_id)}\n"
                                                          f"Номер телефона заказчика: {message.successful_payment.order_info.phone_number}\n"
                                                          f"Сумма {message.successful_payment.total_amount // 100} {message.successful_payment.currency}"
                                   )
    await message.bot.send_media_group(chat_id=ADMIN_ID, media=[file1, file2])
    file = image_to_bytes(image)
    await message.bot.send_document(chat_id=ADMIN_ID, document=file)
    # запись в бд
    if print_pos[0] == "deleted":
        print_pos[0] = [-1, -1]
    if print_pos[1] == "deleted":
        print_pos[1] = [-1, -1]
    db = Database("database/example.db")
    db.cursor.execute("INSERT INTO users (tg_id, name, address, city, country, phone, email, shipping_type) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (user_id, message.successful_payment.order_info.name,
                       message.successful_payment.order_info.shipping_address.street_line1 + ", " +
                       message.successful_payment.order_info.shipping_address.street_line2,
                       message.successful_payment.order_info.shipping_address.state + ", " +
                       message.successful_payment.order_info.shipping_address.city,
                       message.successful_payment.order_info.shipping_address.country_code,
                       message.successful_payment.order_info.phone_number,
                       message.successful_payment.order_info.email,
                       message.successful_payment.shipping_option_id))
    db.cursor.execute("INSERT INTO orders (tg_id, type, size, color) "
                      "VALUES (?, ?, ?, ?)", (user_id, item, size_order.upper(), colors.get(color)))
    db.cursor.execute("INSERT INTO front_print (tg_id, position_x, position_y, width, height, bg_deleted, angle) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, print_pos[0][0], print_pos[0][1], size[0][0], size[0][1],
                                                       bg_deleted[0], angle[0]))

    db.cursor.execute("INSERT INTO back_print (tg_id, position_x, position_y, width, height, bg_deleted, angle) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, print_pos[1][0], print_pos[1][1], size[1][0], size[1][1],
                                                       bg_deleted[1], angle[1]))
    db.conn.commit()
    db.close()
