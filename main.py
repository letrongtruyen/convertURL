#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRUYEN.TECH Tool: Facebook URL to Share Wrapped Converter (Bản quyền TRUYEN.TECH)

  _______ _____  _    ___     ________ _   _       _______ ______ _____ _    _ 
 |__   __|  __ \| |  | \ \   / /  ____| \ | |     |__   __|  ____/ ____| |  | |
    | |  | |__) | |  | |\ \_/ /| |__  |  \| |        | |  | |__ | |    | |__| |
    | |  |  _  /| |  | | \   / |  __| | . ` |        | |  |  __|| |    |  __  |
    | |  | | \ \| |__| |  | |  | |____| |\  |  _     | |  | |___| |____| |  | |
    |_|  |_|  \_\\____/   |_|  |______|_| \_| (_)    |_|  |______\_____|_|  |_|
                                                                               
                                                                               
Version     : 1.0
Author      : LE TRONG TRUYEN
Website     : https://TRUYEN.TECH
License     : MIT (chỉ dùng cho mục đích học tập / nghiên cứu cá nhân)
Description : Chuyển đổi URL Facebook (profile/group/post) sang dạng share wrapped URL
"""

import re
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("truyen-fb-url-converter")

LOGO = r"""
  _______ _____  _    ___     ________ _   _       _______ ______ _____ _    _ 
 |__   __|  __ \| |  | \ \   / /  ____| \ | |     |__   __|  ____/ ____| |  | |
    | |  | |__) | |  | |\ \_/ /| |__  |  \| |        | |  | |__ | |    | |__| |
    | |  |  _  /| |  | | \   / |  __| | . ` |        | |  |  __|| |    |  __  |
    | |  | | \ \| |__| |  | |  | |____| |\  |  _     | |  | |___| |____| |  | |
    |_|  |_|  \_\\____/   |_|  |______|_| \_| (_)    |_|  |______\_____|_|  |_|
"""

def truyen_print_logo():
    print(LOGO)
    print("TRUYEN.TECH Facebook URL Converter Toolkit\n")


class TruyenFacebookURLConverter:
    def __init__(self, tr_cookies: str, tr_cache_file: str = "tr_fb_tokens_cache.json"):
        self.tr_cookies = tr_cookies.strip()
        self.tr_cache_file = Path(tr_cache_file)

        self.tr_c_user = self._tr_extract_c_user()

        self.tr_base_headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"19.0.0"',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-full-version-list': '"Google Chrome";v="143.0.7499.170", "Chromium";v="143.0.7499.170", "Not=A?Brand";v="24.0.0.0"',
            'sec-ch-prefers-color-scheme': "dark",
            'accept-language': "vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6",
            'Cookie': self.tr_cookies
        }

        truyen_print_logo()
        logger.info("Khởi tạo TRUYEN.TECH URL Converter...")
        self.tr_tokens = self._tr_load_or_fetch_tokens()

    def _tr_extract_c_user(self) -> Optional[str]:
        match = re.search(r'c_user=(\d+)', self.tr_cookies)
        if match:
            c_user = match.group(1)
            logger.info(f"Đã trích xuất c_user: {c_user}")
            return c_user
        logger.warning("Không tìm thấy c_user trong cookies")
        return None

    def _tr_load_cache(self) -> Optional[Dict]:
        if not self.tr_cache_file.is_file():
            return None

        try:
            data = json.loads(self.tr_cache_file.read_text(encoding="utf-8"))
            cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
            if datetime.now() - cache_time < timedelta(hours=24):
                logger.info(f"Đã load tokens từ cache (thời gian: {cache_time})")
                return data
            else:
                logger.info("Cache đã hết hạn (>24h)")
                return None
        except Exception as e:
            logger.warning(f"Lỗi đọc cache: {e}")
            return None

    def _tr_save_cache(self, tokens: Dict):
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'c_user': self.tr_c_user,
                **tokens
            }
            self.tr_cache_file.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Đã lưu tokens vào cache: {self.tr_cache_file}")
        except Exception as e:
            logger.error(f"Lỗi lưu cache: {e}")

    def _tr_fetch_tokens(self, group_url: str = "https://www.facebook.com/groups/989741155480965") -> Dict:
        logger.info("Đang lấy tokens mới từ Facebook...")

        headers = self.tr_base_headers.copy()
        headers.update({
            'cache-control': "max-age=0",
            'dpr': "1",
            'viewport-width': "1920",
            'upgrade-insecure-requests': "1",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'priority': "u=0, i",
        })

        resp = requests.get(group_url, headers=headers, timeout=30)
        resp.raise_for_status()

        lsd_match   = re.search(r'\["LSD",\[\],\{"token":"([^"]+)"\}', resp.text)
        dtsg_match  = re.search(r'\["DTSGInitialData",\[\],\{"token":"([^"]+)"\}', resp.text)
        nonce_match = re.search(r'\["ServerNonce",\[\],\{"ServerNonce":"([^"]+)"\}', resp.text)

        if not (lsd_match and dtsg_match):
            raise RuntimeError("Không thể trích xuất LSD hoặc DTSG token")

        tokens = {
            'lsd': lsd_match.group(1),
            'dtsg': dtsg_match.group(1),
            'server_nonce': nonce_match.group(1) if nonce_match else None
        }

        logger.info(f"LSD: {tokens['lsd'][:10]}...")
        logger.info(f"DTSG: {tokens['dtsg'][:10]}...")
        if tokens['server_nonce']:
            logger.info(f"Server Nonce: {tokens['server_nonce']}")

        return tokens

    def _tr_load_or_fetch_tokens(self) -> Dict:
        cache = self._tr_load_cache()
        if cache and cache.get('c_user') == self.tr_c_user:
            return {
                'lsd': cache['lsd'],
                'dtsg': cache['dtsg'],
                'server_nonce': cache.get('server_nonce')
            }

        tokens = self._tr_fetch_tokens()
        self._tr_save_cache(tokens)
        return tokens

    def tr_refresh_tokens(self):
        logger.info("Làm mới tokens...")
        self.tr_tokens = self._tr_fetch_tokens()
        self._tr_save_cache(self.tr_tokens)

    def tr_convert_url(self, original_url: str) -> Dict[str, str]:
        logger.info(f"Chuyển đổi URL: {original_url}")

        api_url = "https://www.facebook.com/api/graphql/"

        payload = {
            'av': self.tr_c_user,
            '__aaid': "0",
            '__user': self.tr_c_user,
            '__a': "1",
            '__req': "19",
            '__hs': "20458.HCSV2:comet_pkg.2.1...0",
            'dpr': "1",
            '__ccg': "EXCELLENT",
            '__rev': "1031620744",
            '__s': "br5fvc:wyy0xk:y2semw",
            '__hsi': "7591793638026791261",
            '__comet_req': "15",
            'fb_dtsg': self.tr_tokens['dtsg'],
            'jazoest': "25609",
            'lsd': self.tr_tokens['lsd'],
            '__spin_r': "1031620744",
            '__spin_b': "trunk",
            '__spin_t': "1767602199",
            '__crn': "comet.fbweb.CometGroupDiscussionRoute",
            'qpl_active_flow_ids': "431626709",
            'fb_api_caller_class': "RelayModern",
            'fb_api_req_friendly_name': "useLinkSharingCreateWrappedUrlMutation",
            'server_timestamps': "true",
            'variables': json.dumps({
                "input": {
                    "client_mutation_id": "2",
                    "actor_id": self.tr_c_user,
                    "original_content_url": original_url,
                    "product_type": "FB_GROUPS"
                }
            }),
            'doc_id': "30568280579452205",
            'fb_api_analytics_tags': '["qpl_active_flow_ids=431626709"]'
        }

        headers = self.tr_base_headers.copy()
        headers.update({
            'sec-ch-ua-full-version-list': '"Google Chrome";v="143.0.7499.170", "Chromium";v="143.0.7499.170", "Not=A?Brand";v="24.0.0.0"',
            'x-fb-friendly-name': "useLinkSharingCreateWrappedUrlMutation",
            'x-asbd-id': "359341",
            'x-fb-lsd': self.tr_tokens['lsd'],
            'origin': "https://www.facebook.com",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://www.facebook.com",
            'priority': "u=1, i",
        })

        try:
            resp = requests.post(api_url, data=payload, headers=headers, verify=False, timeout=30)
            resp.raise_for_status()

            data = resp.json()

            share_data = data.get('data', {}).get('xfb_create_share_url_wrapper', {}).get('share_url_wrapper', {})

            result = {
                'id': share_data.get('id'),
                'original_url': share_data.get('original_content_url', original_url),
                'wrapped_url': share_data.get('wrapped_url')
            }

            logger.info("Chuyển đổi thành công")
            logger.info(f"ID          : {result['id']}")
            logger.info(f"Original    : {result['original_url']}")
            logger.info(f"Wrapped URL : {result['wrapped_url']}")

            return result

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                logger.warning("Token có thể hết hạn → làm mới...")
                self.tr_refresh_tokens()
                return self.tr_convert_url(original_url)
            else:
                logger.error(f"Lỗi HTTP {e.response.status_code if e.response else 'Unknown'}: {e}")
                raise
        except Exception as e:
            logger.error(f"Lỗi chuyển đổi URL: {e}")
            raise


if __name__ == "__main__":
    COOKIES = ""  # Điền cookie Facebook đầy đủ vào đây

    if not COOKIES.strip():
        print("Vui lòng điền COOKIES vào biến COOKIES")
        exit(1)

    converter = TruyenFacebookURLConverter(COOKIES)
    test_urls = [
        "https://www.facebook.com/musaddekalakib",
    ]

    for url in test_urls:
        try:
            result = converter.tr_convert_url(url)
            print(f"\nKết quả:")
            print(f"  ID          : {result['id']}")
            print(f"  Original    : {result['original_url']}")
            print(f"  Wrapped URL : {result['wrapped_url']}")
            print("-" * 60)
        except Exception as e:
            print(f"Lỗi xử lý {url}: {e}")
