#meta developer: chernykh-mykhailo (@Div4unka_z_kare)
# t.me/myshcode_ai

from .. import loader, utils
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class GiftClaimerMod(loader.Module):
    """Модуль для автоматичного збору подарунків з вказаного Телеграм-каналу через кнопки з логуванням"""
    
    strings = {
        "name": "GiftClaimer",
        "config_channel": "Юзернейм або ID каналу для моніторингу (без @)",
        "config_log_chat": "ID або юзернейм чату для відправки звітів про збір",
        "enabled": "✅ <b>Авто-збір увімкнено:</b> <code>{}</code>",
        "status": "ℹ️ <b>Статус модуля:</b>\nКанал: <code>{}</code>\nЛог-чат: <code>{}</code>\nАктивний: <code>{}</code>",
        "set_channel": "✅ <b>Канал для моніторингу змінено на:</b> <code>{}</code>",
        "set_log": "✅ <b>Чат для логів змінено на:</b> <code>{}</code>",
        "no_args": "⚠️ <b>Вкажіть значення після команди!</b>",
        "log_report": "🎁 <b>[GiftClaimer] Спроба збору!</b>\n\n🏙 <b>Джерело:</b> <code>{}</code>\n📝 <b>Повідомлення:</b> <i>{}</i>\n🔘 <b>Кнопка:</b> <code>{}</code>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "target_channel",
                "mafiauachannel",
                lambda: self.strings["config_channel"],
            ),
            loader.ConfigValue(
                "log_chat",
                "",
                lambda: self.strings["config_log_chat"],
            ),
            loader.ConfigValue(
                "enabled",
                True,
                lambda: "Увімкнути/Вимкнути автоматичний збір",
            ),
        )

    async def giftsetcmd(self, message):
        """Вказати юзернейм каналу для збору подарунків"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return
        
        channel = args.replace("@", "").strip()
        self.config["target_channel"] = channel
        await utils.answer(message, self.strings["set_channel"].format(channel))

    async def giftlogcmd(self, message):
        """Вказати ID або юзернейм чату куди присилати звіти"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return
        
        log_chat = args.strip()
        self.config["log_chat"] = log_chat
        await utils.answer(message, self.strings["set_log"].format(log_chat))

    async def giftclaimcmd(self, message):
        """Перевірити статус налаштувань авто-збору"""
        status = "ТАК" if self.config["enabled"] else "НІ"
        channel = self.config["target_channel"]
        log_chat = self.config["log_chat"] if self.config["log_chat"] else "Не встановлено"
        await utils.answer(message, self.strings["status"].format(channel, log_chat, status))

    async def giftclaimtogglecmd(self, message):
        """Увімкнути або вимкнути авто-збір"""
        self.config["enabled"] = not self.config["enabled"]
        await utils.answer(message, self.strings["enabled"].format(self.config["enabled"]))

    async def watcher(self, message):
        """Спостерігач за новими повідомленнями"""
        if not self.config["enabled"]:
            return

        if not message or not message.chat:
            return

        # Налаштування цільового каналу
        target = str(self.config["target_channel"]).replace("@", "").lower()
        chat_username = getattr(message.chat, "username", None) or ""
        chat_username = chat_username.lower()
        chat_id = str(message.chat_id)

        # Перевірка чи повідомлення з потрібного чату
        if chat_username == target or chat_id == target or chat_id == f"-100{target}":
            # Якщо повідомлення має кнопки
            if hasattr(message, "reply_markup") and message.reply_markup:
                try:
                    # Отримуємо текст кнопки та повідомлення для звіту
                    btn_text = "Невідомо"
                    try:
                        btn_text = message.reply_markup.rows[0].buttons[0].text
                    except Exception:
                        pass
                    
                    msg_preview = (message.raw_text or "Без тексту")[:150] + "..."
                    
                    # Затримка 0.5с для безпеки
                    await asyncio.sleep(0.5)
                    
                    # Натискаємо на першу кнопку
                    await message.click(0)
                    logger.info(f"GiftClaimer: Натиснуто кнопку в {target}")

                    # Відправка звіту в лог-чат, якщо він вказаний
                    log_target = self.config["log_chat"]
                    if log_target:
                        report_text = self.strings["log_report"].format(
                            chat_username or chat_id,
                            msg_preview,
                            btn_text
                        )
                        try:
                            await self.client.send_message(log_target, report_text)
                        except Exception as log_err:
                            logger.error(f"GiftClaimer Log Error: {log_err}")

                except Exception as e:
                    logger.error(f"GiftClaimer Error: {e}")