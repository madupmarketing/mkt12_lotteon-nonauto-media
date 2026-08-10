"""
Toss Ads(ads-platform.toss.im) 디스플레이 광고 리포트 정찰용 스크립트.
Sheets/Slack 미사용. 각 단계 스크린샷만 /tmp에 남긴다.

TOSS_COOKIES(Cookie-Editor로 내보낸 JSON) 환경변수를 브라우저에 주입해서
이메일/비밀번호 로그인 + 2FA 없이 바로 리포트 화면에 들어가는지 확인하는 용도.
확인 끝나면 이 파일은 삭제할 것.
"""

import json
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

REPORT_URL = "https://ads-platform.toss.im/reports/3606"
SHOT_DIR = "/tmp"


def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def shot(driver, name: str):
    path = os.path.join(SHOT_DIR, f"toss_{name}.png")
    try:
        driver.save_screenshot(path)
        print(f"스크린샷 저장: {path}")
    except Exception as e:
        print(f"스크린샷 실패({name}): {e}")


def dump_html(driver, name: str):
    path = os.path.join(SHOT_DIR, f"toss_{name}.html")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML 저장: {path}")
    except Exception as e:
        print(f"HTML 저장 실패({name}): {e}")


def inject_cookies(driver, cookies_json: str):
    cookies = json.loads(cookies_json)
    print(f"쿠키 {len(cookies)}개 로드")

    # 쿠키를 넣으려면 먼저 해당 도메인 페이지에 있어야 함
    driver.get("https://ads-platform.toss.im")
    time.sleep(1)

    ok, fail = 0, 0
    for c in cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "path": c.get("path", "/"),
        }
        domain = c.get("domain")
        if domain:
            cookie["domain"] = domain
        if c.get("expirationDate"):
            cookie["expiry"] = int(c["expirationDate"])
        if "secure" in c:
            cookie["secure"] = c["secure"]
        try:
            driver.add_cookie(cookie)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"쿠키 추가 실패({c.get('name')}, domain={domain}): {e}")

    print(f"쿠키 주입 결과: 성공 {ok}개 / 실패 {fail}개")


def main():
    cookies_json = os.environ["TOSS_COOKIES"]

    driver = build_driver()
    try:
        inject_cookies(driver, cookies_json)

        print(f"리포트 화면 접속: {REPORT_URL}")
        driver.get(REPORT_URL)
        time.sleep(5)
        print(f"최종 URL: {driver.current_url}")
        print(f"페이지 제목: {driver.title}")
        shot(driver, "cookie_01_report")
        dump_html(driver, "cookie_01_report")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
