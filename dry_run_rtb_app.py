"""
드라이런 테스트 스크립트 (Sheets 업로드/Slack 알림 없음, RTB House 조회만 수행).

사용법 (본인 PC에서 직접 실행):
    setx RTBHOUSE_EMAIL "본인 RTB House 로그인 이메일"
    setx RTBHOUSE_PASSWORD "본인 RTB House 비밀번호"
    (새 터미널 열고)
    python dry_run_rtb_app.py 2026-08-09

RTB House API 조회(GET)만 하고 아무 것도 쓰거나 전송하지 않습니다.
"""

import json
import sys
from pathlib import Path

from crawlers import rtbhouse

target_date = sys.argv[1] if len(sys.argv) > 1 else "2026-08-09"

with open(Path(__file__).parent / "config.json", encoding="utf-8") as f:
    cfg = json.load(f)

app_data, web_data = rtbhouse.scrape(
    app_url=cfg["rtbhouse"]["app_dashboard_url"],
    web_url=cfg["rtbhouse"]["web_dashboard_url"],
    target_date=target_date,
    app_campaign_map=cfg["rtbhouse"]["app_campaign_map"],
)

print(f"\n=== {target_date} 조회 결과 (시트/Slack 미반영) ===")
print("RTB_APP (캠페인별):")
if app_data:
    for row in app_data:
        print(f"  - {row['campaign_label']:<20} {row['material']:<30} "
              f"imps={row['imps']} clicks={row['clicks']} cost={row['cost']}")
else:
    print("  (데이터 없음)")
print(f"RTB_WEB: {web_data}")
