import os
from enum import Enum
import asyncio
from datetime import datetime, timedelta, timezone
import re
from telethon import TelegramClient
from src.TelegramScraper import TgScraper
from src.WebScrapers import *

class Parser:
    class ParseType(Enum):
        channel = "channels"
        websites = "websites"
        keyword = "keywords"
        stopword = "stopwords"
        params = "params"
        none = ""

    def __init__(self):
        self.channels = []
        self.websites = []
        self.keywords = []
        self.stopwords = []
        self.output_messages = []
        self.parseType = self.ParseType.none
        self.cutoff = datetime.now(timezone.utc) - timedelta(days=1, hours=1)
        self.max_desc_size = 100
        self.group_messages = False
        self.use_render = False

        self.parse_config()
        self.show_config_data()
        
        # scrap all data
        if(len(self.channels) > 0):
            scraper = TgScraper(self.channels, self.cutoff)
            self.output_messages.extend(scraper.get_vacancies())
        if(len(self.websites) > 0):
            scraper_mapping = {
                    "https://hitmarker.net/jobs": HitMakerScraper,
                    }
            for website in self.websites:
                scraper = scraper_mapping[website](self.cutoff, self.use_render)
                self.output_messages.extend(scraper.get_vacancies())
        
        # filter only nessesary data
        self.filter_messages()

        # send messages to stdout and bot
        if(len(self.output_messages) > 0):
            self.send_messages()
    
    def show_config_data(self):
        print(f"INFO: Data will scraped since {self.cutoff.strftime("%Y-%m-%d %H:%M:%S %Z")}")
        print(f"INFO: Vacancy desription size is {self.max_desc_size}")
        print(f"INFO: Send messages {"" if self.group_messages else "un"}grouped")
        print(f"INFO: Render pages {"on" if self.use_render else "off"}")

    def parse_category(self, line: str) -> bool:
        for s in self.ParseType:
            if line == s.value:
                self.parseType = s
                return True
        return False

    def parse_time(self, param: str):
        mapping = {
                "y": ("days", 365),
                "mo": ("days", 30),
                "w": ("weeks", 1),
                "d": ("days", 1),
                "h": ("hours", 1),
                }
        # TODO: run script since last start

        times = [(int(num), unit) for num, unit in re.findall(r"(\d+)([a-zA-Z]+)", param)]
        td = timedelta()
        for num, unit in times:
            if unit not in mapping:
                continue
            field, multiplier = mapping[unit]
            kwargs = {str(field): int(num) * multiplier}
            td += timedelta(**kwargs)
        self.cutoff = datetime.now(timezone.utc) - td


    def parse_params(self, line: str):
        param = line.split("=")
        
        if len(param)>2: 
            print(f"ERROR: can't parse paraps properly for line '{line}'")
            return 

        match param[0]:
            case "cutoff_time":
                self.parse_time(param[1])
            case "max_output_description_size":
                self.max_desc_size = int(param[1])
            case "send_messages":
                match param[1]:
                    case "single":
                        self.group_messages = False
                    case "grouped":
                        self.group_messages = True
                    case _:
                        print("ERROR: Can't parse send_messages param, got ", param[1])
            case "render_pages":
                match param[1].lower():
                    case "false":
                        self.use_render = False
                    case "true":
                        self.use_render = True
                    case _:
                        print("ERROR: Can't parse render_pages param, got ", param[1])

            case _:
                print(f"ERROR: Can't parse '{line}' line")

    def parse_config(self):
        with open("config.txt", "r", encoding="utf-8") as file:
            data = file.readlines()
            channels_to_fetch = []
            for line in data:
                line = line.strip()
                if(line == "" or line.startswith(("--", "-"))):
                    # it is comment or disabled line
                    continue
                if("--" in line): # remove comments
                    line = line.split("--")[0]

                if(self.parse_category(line)):
                    continue

                match self.parseType:
                    case self.ParseType.channel:
                        self.channels.append(line)
                    case self.ParseType.keyword:
                        self.keywords.append(line.lower())
                    case self.ParseType.stopword:
                        self.stopwords.append(line.lower())
                    case self.ParseType.websites:
                        self.websites.append(line)
                    case self.ParseType.params:
                        self.parse_params(line)
                    case _:
                        print("error: ", line)
   

    def filter_messages(self):
        def check_stopwords(text: str) -> bool:
            for stopword in self.stopwords:
                if stopword in text:
                    return True
            return False
        
        def check_keywords(text: str) -> bool:
            for keyword in self.keywords:
                if keyword in text:
                    return True
            return False
        
        filtered = []
        for message in self.output_messages:
            text = message.text.lower()
            if(check_stopwords(text)):
                continue
            if(check_keywords(text)):
                filtered.append(message)

        self.output_messages = filtered 

    async def send_messages_to_bot(self):
        async def send_messages_in_batches():
            batch_size = 3000 // self.max_desc_size if self.group_messages else 1
            messages = []
            for i in range(0, len(self.output_messages), batch_size):
                batch = self.output_messages[i:i+batch_size]
                message = "\n\n".join(m.format_str(self.max_desc_size) for m in batch)
                messages.append(send_message(message))
            
            await asyncio.gather(*messages)
        
        async def send_message(message):
            await bot.send_message(user_id, str(message))

        token = os.getenv("TOKEN")
        user_id = os.getenv("USER_ID")
        if token and user_id:
            bot = await TelegramClient("bot_session", os.getenv("API_ID"), os.getenv("API_HASH")) .start(bot_token=token)
            async with bot:
                await send_messages_in_batches()            
 

    def send_messages(self):
        asyncio.run(self.send_messages_to_bot())
        print(*self.output_messages)

if __name__ == "__main__":
    Parser()
    
