import asyncio
import os
from telethon import TelegramClient
from src.OutputMessage import OutputMessage

class TgScraper:
    def __init__(self, channels: list, time_cutoff):
        self.vacancies = []
        self.channels = channels
        self.cutoff = time_cutoff

        asyncio.run(self.parse_channels())

    async def parse_channel(self, scrapper, channel: str):  
        async for message in scrapper.iter_messages(channel, offset_date=self.cutoff, reverse=True):
            self.vacancies.append(OutputMessage(message.text, channel + "/" + str(message.id)))
        
            

    async def parse_channels(self):
        scrapper = await TelegramClient("scrapper_session", os.getenv("API_ID"), os.getenv("API_HASH")) .start()
        async with scrapper:
            tasks = [self.parse_channel(scrapper, channel) for channel in self.channels]
            await asyncio.gather(*tasks)
     
    def get_vacancies(self):
        return self.vacancies
