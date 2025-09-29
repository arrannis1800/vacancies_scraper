import os
from enum import Enum
from telethon import TelegramClient
import asyncio
from datetime import datetime, timedelta


class Parser:
    class ParseType(Enum):
        channel = "channels"
        keyword = "keywords"
        stopword = "stopwords"
        none = ""

    class OutputMessage:
        text = ""
        link = ""
        max_descr_size = 100

        def __init__(self, text, link):
            self.text = text.strip()
            self.link = link

        def __str__(self):
            return f"Desription: {self.text[:self.max_descr_size]}\nLink: {self.link}\n\n"


    def __init__(self):
        self.channels = []
        self.keywords = []
        self.stopwords = []
        self.output_messages = []
        self.parseType = self.ParseType.none
        self.cutoff = datetime.now() - timedelta(days=1, hours=1) 
        
        self.parse_config()
        
        # scrap all data
        if(len(self.channels) > 0):
            asyncio.run(self.parse_channels())
        
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
            


    async def parse_channel(self, scrapper, channel: str):  
        async for message in scrapper.iter_messages(channel, offset_date=self.cutoff, reverse=True):
            self.output_messages.append(self.OutputMessage(message.text, channel + "/" + str(message.id)))
        
            

    async def parse_channels(self):
        scrapper = await TelegramClient("scrapper_session", os.getenv("API_ID"), os.getenv("API_HASH")) .start()
        async with scrapper:
            tasks = [self.parse_channel(scrapper, channel) for channel in self.channels]
            await asyncio.gather(*tasks)
        

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
    
