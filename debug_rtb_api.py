"""
RTB House API 경로 진단 전용 스크립트.
Sheets/Slack에는 전혀 손대지 않고, subcampaign 관련 API 후보 경로들을 조회해서
상태 코드와 응답 본문을 출력한다. 문제 해결되면 이 파일은 삭제할 것.
"""

import os

import requests
from requests.auth import HTTPBasicAuth

API_BASE = "https://api.panel.rtbhouse.com/v5"
APP_HASH = "zjgMiqEIsN3oQNMPG6hc"
TARGET_DATE = os.environ.get("TARGET_DATE", "2026-08-09")


def _auth():
    return HTTPBasicAuth(os.environ["RTBHOUSE_EMAIL"], os.environ["RTBHOUSE_PASSWORD"])


def probe_get(label: str, url: str, params: dict | None = None):
    print(f"\n--- {label} ---")
    print(f"GET {url} params={params}")
    try:
        resp = requests.get(url, params=params, auth=_auth(), timeout=30)
        print(f"status={resp.status_code}")
        print(resp.text[:1500])
    except Exception as e:
        print(f"예외: {e}")


if __name__ == "__main__":
    # 1) advertiser 정보 자체 (해시가 유효한지, 응답 구조 확인용)
    probe_get("advertiser info", f"{API_BASE}/advertisers/{APP_HASH}")

    # 2) subcampaign 목록 후보 경로들
    for path in ["subcampaigns", "sub-campaigns", "campaigns"]:
        probe_get(f"list via /{path}", f"{API_BASE}/advertisers/{APP_HASH}/{path}")

    # 3) rtb-stats groupBy=subcampaign 자체 응답에 이름 필드가 있는지 확인
    probe_get(
        "rtb-stats groupBy=subcampaign",
        f"{API_BASE}/advertisers/{APP_HASH}/rtb-stats",
        params={
            "dayFrom": TARGET_DATE,
            "dayTo": TARGET_DATE,
            "groupBy": "subcampaign",
            "metrics": "impsCount-clicksCount-campaignCost",
        },
    )
