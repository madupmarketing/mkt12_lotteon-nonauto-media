"""
Toss Ads(ads-platform.toss.im) 디스플레이 광고 리포트 정찰용 스크립트.
Sheets/Slack 미사용. 각 단계 스크린샷만 /tmp에 남긴다.
클라우드에서 로그인이 실제로 되는지, 리포트 화면 구조가 어떤지 확인하는 용도.
확인 끝나면 이 파일은 삭제할 것.
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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


def try_login(driver, email: str, password: str) -> bool:
    """일반적인 이메일/비밀번호 폼을 찾아 로그인 시도. 성공 여부를 최선을 다해 판단."""
    selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[name="username"]',
        'input[type="text"]',
    ]
    email_input = None
    for sel in selectors:
        found = driver.find_elements(By.CSS_SELECTOR, sel)
        if found:
            email_input = found[0]
            print(f"이메일 입력 필드 발견: {sel}")
            break

    if email_input is None:
        print("이메일 입력 필드를 못 찾음")
        return False

    email_input.clear()
    email_input.send_keys(email)

    pw_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
    if not pw_inputs:
        print("비밀번호 입력 필드를 못 찾음")
        return False
    pw_inputs[0].clear()
    pw_inputs[0].send_keys(password)

    shot(driver, "02_form_filled")

    submit_candidates = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
    if not submit_candidates:
        submit_candidates = [
            b for b in driver.find_elements(By.TAG_NAME, "button")
            if any(t in b.text for t in ["로그인", "Login", "확인", "다음"])
        ]
    if not submit_candidates:
        print("제출 버튼을 못 찾음")
        return False

    submit_candidates[0].click()
    time.sleep(4)
    return True


def main():
    email = os.environ["TOSS_EMAIL"]
    password = os.environ["TOSS_PASSWORD"]

    driver = build_driver()
    try:
        print(f"1단계: {REPORT_URL} 접속")
        driver.get(REPORT_URL)
        time.sleep(4)
        print(f"현재 URL: {driver.current_url}")
        shot(driver, "01_initial")
        dump_html(driver, "01_initial")

        if "login" in driver.current_url.lower() or driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]'):
            print("2단계: 로그인 폼으로 판단 → 로그인 시도")
            ok = try_login(driver, email, password)
            print(f"로그인 시도 결과: {ok}")
            time.sleep(3)
            print(f"로그인 후 URL: {driver.current_url}")
            shot(driver, "03_after_login")
            dump_html(driver, "03_after_login")
        else:
            print("로그인 폼이 안 보임 (이미 로그인 상태이거나 다른 구조)")

        print("4단계: 리포트 화면 재접속 시도")
        driver.get(REPORT_URL)
        time.sleep(4)
        print(f"최종 URL: {driver.current_url}")
        shot(driver, "04_report_final")
        dump_html(driver, "04_report_final")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
