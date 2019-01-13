import asyncio

import aiocron
import aiosqlite
from aiohttp import ClientSession

BOT_TOKEN = "some_token"
CHAT_ID = "@some_public"


async def json_post(url, json_data):
    async with ClientSession() as session:
        try:
            return await session.post(url, json=json_data)
        except Exception as e:
            print("post error: '{}'".format(str(e)))


async def post_message(bot_token, chat_id, text, reply_id=None):
    url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
    json_data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_id:
        json_data["reply_to_message_id"] = reply_id

    return await json_post(url, json_data)


@aiocron.crontab("0 12 * * *")
async def post_fact():
    select_fact = """
        SELECT f.id,
               c.display_name AS header,
               f.data         AS fact
        FROM   fact AS f
               INNER JOIN category AS c
                       ON c.id = f.category
               INNER JOIN (SELECT used_count
                           FROM   fact
                           GROUP  BY used_count
                           ORDER  BY used_count
                           LIMIT  3) AS u
                       ON u.used_count = f.used_count
        ORDER  BY Random()
        LIMIT  1 
    """

    inc_usage = """
        UPDATE fact
        SET    used_count = used_count + 1
        WHERE  id = :id 
    """

    async with aiosqlite.connect("facts.db3") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(select_fact) as cursor:
            row = await cursor.fetchone()

            header = row["header"]
            body = row["fact"]
            footer = "Узнавайте новое 👨‍🎓, делитесь с друзьями 🤳, *подписывайтесь* 📢 на паблик " \
                     "[CamelSpiders](https://t.me/camel_spiders/).\r\n\r\n" \
                     "#CamelSpiders #CamelSpidersFact #ФактыCamelSpiders #ИнтересныеФакты #ФактыПауки #ФактыСкорпионы #ФактыКлещи #ФактыАрахниды"

            fact_msg = f"{header}\r\n\r\n{body}\r\n\r\n{footer}"
            await post_message(BOT_TOKEN, CHAT_ID, fact_msg)

        await db.execute(inc_usage, {"id": row["id"]})
        await db.commit()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_forever()
