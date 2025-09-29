import os
from enum import Enum
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
# from src.OutputMessage import OutputMessage
from src.TelegramScraper import TgScraper
from src.WebScrapers import *

class Parser:
    class ParseType(Enum):
        channel = "channels"
        websites = "websites"
        keyword = "keywords"
        stopword = "stopwords"
        none = ""

    def __init__(self):
        self.channels = []
        self.websites = []
        self.keywords = []
        self.stopwords = []
        self.output_messages = []
        self.parseType = self.ParseType.none
        self.cutoff = datetime.now(timezone.utc) - timedelta(days=1, hours=1)
        
        self.parse_config()
        
        # scrap all data
        if(len(self.channels) > 0):
            scraper = TgScraper(self.channels, self.cutoff)
            self.output_messages.extend(scraper.get_vacancies())
        if(len(self.websites) > 0):
            scraper_mapping = {
                    "https://hitmarker.net/jobs": HitMakerScraper,
                    }
            for website in self.websites:
                scraper = scraper_mapping[website](self.cutoff)
                self.output_messages.extend(scraper.get_vacancies())
        
        # filter only nessesary data
        self.filter_messages()

        # send messages to stdout and bot
        if(len(self.output_messages) > 0):
            self.send_messages()
    
    def parse_category(self, line: str) -> bool:
        for s in self.ParseType:
            if line == s.value:
                self.parseType = s
                return True
        return False

    def parse_config(self):
        with open("config.txt", "r", encoding="utf-8") as file:
            data = file.readlines()
            channels_to_fetch = []
            for line in data:
                line = line.strip()
                if(line.startswith(("#", "-"))):
                    # it is comment or disabled line
                    continue

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
        async def send_message(message):
            await bot.send_message(user_id, str(message))

        token = os.getenv("TOKEN")
        user_id = os.getenv("USER_ID")
        if token and user_id:
            bot = await TelegramClient("bot_session", os.getenv("API_ID"), os.getenv("API_HASH")) .start(bot_token=token)
            async with bot:
                tasks = [send_message(message) for message in self.output_messages]
                await asyncio.gather(*tasks)
            
 

    def send_messages(self):
        asyncio.run(self.send_messages_to_bot())
        print(*self.output_messages)

if __name__ == "__main__":
    Parser()
    
