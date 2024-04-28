# bot/api/tiktok.py

import asyncio
import json
import logging
import random
import string
from datetime import datetime
from functools import wraps
from typing import AsyncIterator
import httpx
from aiogram.types import Message
from bs4 import BeautifulSoup
from settings import USER_AGENT

class Retrying(Exception):
    pass

def retries(times: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except Retrying as ex:
                    logging.warning(f"Retrying attempt {attempt + 1} of {times} failed: {str(ex)}")
                    last_exception = ex
                    await asyncio.sleep(0.5 * (attempt + 1))
            logging.error("All retry attempts failed.")
            raise last_exception
        return wrapper
    return decorator

class TikTokAPI:

    def __init__(self, headers=None):
        self.headers = headers or {}
        self.link = 'tiktok.com'
        self.script_selector = 'script[id="SIGI_STATE"]'

    async def handle_message(self, message: Message) -> AsyncIterator[bytes]:
        urls = self._extract_urls_from_message(message)
        for url in urls:
            video = await self.download_video(url)
            yield video

    def _extract_urls_from_message(self, message: Message):
        entries = (message.text[e.offset:e.offset + e.length] for e in message.entities)
        return map(
            lambda u: u if u.startswith('http') else f'https://{u}',
            filter(lambda e: self.link in e, entries)
        )
    
    async def _primary_method(self, soup, client, page_id):
        script = soup.select_one(self.script_selector)
        if not script:
            raise Retrying("No script found with selector.")

        try:
            data = json.loads(script.text)
        except json.JSONDecodeError:
            raise Retrying("Failed to decode JSON from script.")

        modules = tuple(script.get("ItemModule").values())
        if not modules:
            raise Retrying("no modules")

        for data in modules:
            if data["id"] != page_id:
                raise Retrying("video_id is different from page_id")
            link = data["video"]["downloadAddr"].encode('utf-8').decode('unicode_escape')
            if video := await client.get(link, headers=self._user_agent):
                video.raise_for_status()
                return video.content
        raise Retrying("video not found")
    
    async def _secondary_method(self, client, url):
        response = await client.get(url, headers=self._user_agent)
        if response.status_code != 200:
            raise Retrying("Invalid response status code")

        start_marker = '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
        end_marker = '</script>'
        start = response.text.find(start_marker)
        if start == -1:
            raise Retrying("No __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag found")

        start += len(start_marker)
        end = response.text.find(end_marker, start)
        if end == -1:
            raise Retrying("Malformed __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag")

        data_json = response.text[start:end]
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            raise Retrying("Failed to parse JSON from __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag")

        default_scope = data.get("__DEFAULT_SCOPE__", {})
        video_detail = default_scope.get("webapp.video-detail", {})
        if video_detail.get("statusCode", 0) != 0:
            raise Retrying("Invalid response structure in __UNIVERSAL_DATA_FOR_REHYDRATION__")

        video_info = video_detail.get("itemInfo", {}).get("itemStruct")
        if not video_info:
            raise Retrying("No video information found in __UNIVERSAL_DATA_FOR_REHYDRATION__")

        download_link = video_info.get("video", {}).get("downloadAddr")
        if not download_link:
            raise Retrying("No download link found in video information")

        video_response = await client.get(download_link, headers=self._user_agent)
        if video_response.status_code != 200:
            raise Retrying("Failed to download the video")

        return video_response.content


    @retries(times=3)
    async def download_video(self, url: str) -> bytes:
        async with httpx.AsyncClient(headers=self.headers, timeout=30,
                                    cookies=self._tt_webid_v2, follow_redirects=True) as client:
            page = await client.get(url, headers=self._user_agent)
            page.raise_for_status()  # Ensure the page is loaded correctly
            page_id = page.url.path.rsplit('/', 1)[-1]
            soup = BeautifulSoup(page.text, 'html.parser')

            try:
                return await self._primary_method(soup, client, page_id)
            except Retrying as primary_error:
                logging.info(f"Primary method failed: {primary_error}, attempting secondary method.")
                return await self._secondary_method(client, url)

    @property
    def _user_agent(self) -> dict:
        return {
            'User-Agent': USER_AGENT or (
                f"{''.join(random.choices(string.ascii_lowercase, k=random.randint(4,10)))}-"
                f"{''.join(random.choices(string.ascii_lowercase, k=random.randint(3,7)))}/"
                f"{random.randint(10, 300)} "
                f"({datetime.now().replace(microsecond=0).timestamp()})"
            )
        }

    @property
    def _tt_webid_v2(self):
        return {'tt_webid_v2': f"{random.randint(10 ** 18, (10 ** 19) - 1)}"}
