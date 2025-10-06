from requests_html import AsyncHTMLSession
import asyncio
from datetime import datetime
from src.OutputMessage import OutputMessage


PYPPETEER_CHROMIUM_REVISION = "1263111"


class WebScraper:
    def __init__(self, time_cutoff: datetime, link: str = "", use_render: bool = True, need_render: bool = False):
        self.links = []
        self.vacancies = []
        self.link = link
        self.cutoff = time_cutoff
        self.use_render = use_render
        self.need_render = need_render

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if self.need_render is True and self.use_render is False:
            print(f"INFO: Can't parse {self.link}, skip this parser")
            return

        self.session = AsyncHTMLSession()
        self.session.run(self._scrap_data)

    async def _scrap_data(self):
        await self._parse_page()

        await self._parse_vacancies()

        await self.session.close()

    async def _get_page(self, link: str):
        response = await self.session.get(link)

        if self.use_render:
            await response.html.arender(wait=2, sleep=1)

        return response

    async def _parse_page(self):
        raise NotImplementedError("Use DerivedClass")

    async def process_in_batches(self, tasks, batch_size=5):
        results = []
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        return results

    async def _parse_vacancies(self):
        tasks = [self._parse_vacancy(l) for l in self.links]
        await self.process_in_batches(tasks, batch_size=5)

    async def _parse_vacancy(self, link: str):
        raise NotImplementedError("Use DerivedClass")

    def get_vacancies(self):
        return self.vacancies


class HitMakerScraper(WebScraper):
    def __init__(self, time_cutoff, use_render):
        super().__init__(time_cutoff, link="https://hitmarker.net/jobs?page=3", 
                         use_render=use_render, need_render=True)

    async def _parse_page(self):
        print("parsing", self.link)
        response = await self._get_page(self.link)

        for container in response.html.find(".space-y-3"):
            for a in container.find("a"):
                span = next(
                        (span for span in a.find("span") if "data-datetime" in span.attrs),
                        None)

                date_str = span.attrs.get("data-datetime")
                href = a.attrs.get("href")
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if href and (dt > self.cutoff):
                    self.links.append(href)

    async def _parse_vacancy(self, link: str):
        print("parsing", link)
        response = await self._get_page(link)

        div = response.html.find(".prose")[0]
        self.vacancies.append(OutputMessage(div.text, link))

