"""
신청 버튼 자동 감시 & 클릭 스크립트
------------------------------------
페이지를 주기적으로 새로고침하면서, "신청마감" 상태의 버튼이
"신청하기"(id="aplBtn", class에 col01 포함) 상태로 바뀌는 순간을 감지해
자동으로 클릭합니다.

사용 전 꼭 확인할 것
1) 같은 폴더에 .env 파일을 만들고 아래 값을 채우세요. (.env.example 참고)
   LOGIN_URL, TARGET_URL, USER_ID, USER_PASSWORD, PHONE_NUMBER
2) CSS 선택자는 캡처하신 HTML 구조 기준으로 작성했습니다.
   실제 페이지에서 개발자도구로 다시 한번 확인 후 필요하면 수정하세요.
3) 너무 짧은 새로고침 주기는 서버에 부담을 주거나 IP 차단으로 이어질 수 있으니
   REFRESH_INTERVAL을 과도하게 낮추지 마세요 (2~5초 권장).
4) .env 파일은 절대 깃허브 등에 올리지 마세요 (.gitignore에 추가 권장).

필요 패키지: pip install selenium python-dotenv
크롬 드라이버는 selenium 4.6+ 부터는 자동으로 관리됩니다.
"""

import os
import time
import random
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException,
)

load_dotenv()  # 같은 폴더의 .env 파일을 읽어 환경변수로 등록

# ------------------- 설정 (.env에서 불러옴) -------------------
LOGIN_URL = os.getenv("LOGIN_URL", "")
TARGET_URL = os.getenv("TARGET_URL", "")
USER_ID = os.getenv("USER_ID", "")
USER_PASSWORD = os.getenv("USER_PASSWORD", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")  # 신청 폼에 전화번호 입력이 필요할 경우 사용

# 로그인 폼 여부 - 로그인이 필요 없으면 False로 바꾸세요
REQUIRE_LOGIN = True

# 캡처하신 HTML 기준 로그인 폼 선택자
USER_ID_SELECTOR = "input[name='userId']"      # id="testLoginId"
PASSWORD_SELECTOR = "input[name='password']"   # id="etcPassword"
LOGIN_BUTTON_SELECTOR = "a#etcLoginBtn"

# "신청하기" 상태가 됐을 때의 버튼 선택자
# 캡처하신 HTML 기준: <a href="#;" id="aplBtn" class="btn01 col01 aplBtn" ...>신청하기</a>
OPEN_BUTTON_SELECTOR = "a#aplBtn.col01"

# 새로고침 주기(초) - 약간의 랜덤을 섞어 너무 규칙적인 요청을 피합니다
REFRESH_INTERVAL_MIN = 2.0
REFRESH_INTERVAL_MAX = 4.0

# 로그인 세션 유지가 필요하면, 기존 크롬 프로필을 그대로 사용하는 방법 (선택)
USE_EXISTING_CHROME_PROFILE = False
CHROME_PROFILE_PATH = r"C:\Users\사용자명\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE_DIRECTORY = "Default"
# ---------------------------------------------


def check_required_env():
    missing = []
    if REQUIRE_LOGIN and not LOGIN_URL:
        missing.append("LOGIN_URL")
    if not TARGET_URL:
        missing.append("TARGET_URL")
    if REQUIRE_LOGIN and not USER_ID:
        missing.append("USER_ID")
    if REQUIRE_LOGIN and not USER_PASSWORD:
        missing.append("USER_PASSWORD")
    if missing:
        raise SystemExit(
            f".env 파일에 다음 값이 비어 있습니다: {', '.join(missing)}\n"
            f".env.example을 참고해서 .env 파일을 채워주세요."
        )


def build_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if USE_EXISTING_CHROME_PROFILE:
        options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
        options.add_argument(f"profile-directory={CHROME_PROFILE_DIRECTORY}")
    options.add_argument("--start-maximized")
    # 자동화 탐지 완화(선택 사항)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)


def login(driver: webdriver.Chrome):
    """로그인 페이지로 이동해 .env의 아이디/비밀번호를 입력하고 로그인 버튼을 클릭."""
    driver.get(LOGIN_URL)

    wait = WebDriverWait(driver, 10)
    id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, USER_ID_SELECTOR)))
    id_input.clear()
    id_input.send_keys(USER_ID)

    pw_input = driver.find_element(By.CSS_SELECTOR, PASSWORD_SELECTOR)
    pw_input.clear()
    pw_input.send_keys(USER_PASSWORD)

    login_btn = driver.find_element(By.CSS_SELECTOR, LOGIN_BUTTON_SELECTOR)
    login_btn.click()

    # 로그인 후 페이지 전환/세션 반영을 위해 잠깐 대기
    try:
        WebDriverWait(driver, 10).until(EC.staleness_of(login_btn))
    except TimeoutException:
        # 로그인 실패(알림창 등)일 수 있으니 사용자가 직접 확인하도록 안내
        print("로그인 처리 확인이 필요합니다. 브라우저 화면을 확인해주세요.")
        time.sleep(3)


def try_click_apply_button(driver: webdriver.Chrome) -> bool:
    """신청하기 버튼이 보이면 클릭하고 True, 아니면 False 반환."""
    try:
        btn = driver.find_element(By.CSS_SELECTOR, OPEN_BUTTON_SELECTOR)
    except NoSuchElementException:
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        return True
    except (StaleElementReferenceException, ElementClickInterceptedException):
        # 클릭 순간 DOM이 바뀌었을 수 있음 -> 다음 루프에서 재시도
        return False


def main():
    check_required_env()
    driver = build_driver()

    if REQUIRE_LOGIN:
        login(driver)

    driver.get(TARGET_URL)

    print("감시를 시작합니다. 버튼 상태가 바뀔 때까지 새로고침을 반복합니다...")
    attempt = 0
    try:
        while True:
            attempt += 1
            if try_click_apply_button(driver):
                print(f"[{attempt}회 시도] 신청하기 버튼 클릭 완료! 페이지를 확인하세요.")
                # 클릭 후 팝업/확인창이 뜨는 경우가 많으니, 여기서 멈추고
                # 사람이 직접 다음 단계를 확인하도록 종료합니다.
                break

            wait_sec = random.uniform(REFRESH_INTERVAL_MIN, REFRESH_INTERVAL_MAX)
            time.sleep(wait_sec)
            driver.refresh()

    except KeyboardInterrupt:
        print("사용자가 중단했습니다.")
    finally:
        input("브라우저를 닫으려면 Enter를 누르세요...")
        driver.quit()


if __name__ == "__main__":
    main()