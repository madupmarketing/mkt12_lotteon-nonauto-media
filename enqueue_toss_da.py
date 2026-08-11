"""
'토스DA큐' 시트에 재수집 요청만 등록하는 가벼운 진입점.
Slack "재실행" 버튼 → GitHub Actions workflow_dispatch → 이 스크립트 → 큐 등록
→ 로컬 스케줄러가 폴링해서 실제 처리.

크롤링을 하지 않으므로 몇 초 안에 끝난다.
"""

import json
from pathlib import Path

from sheets import uploader
from utils.dates import get_target_date


def main():
    target_date = get_target_date()

    config_path = Path(__file__).parent / "config.json"
    with open(config_path, encoding="utf-8") as f:
        static_cfg = json.load(f)

    uploader.enqueue_toss_display_ads(static_cfg["spreadsheet_id"], target_date)
    print(f"토스DA큐 등록 완료: {target_date}")


if __name__ == "__main__":
    main()
