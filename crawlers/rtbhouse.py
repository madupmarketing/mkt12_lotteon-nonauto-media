"""
RTB House 크롤러 — REST API 방식 (Selenium 불필요)

API: https://api.panel.rtbhouse.com/v5
인증: HTTP Basic Auth (RTBHOUSE_EMAIL / RTBHOUSE_PASSWORD)
광고주 해시: dashboard URL의 /dashboard/{hash}/ 부분
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

API_BASE = "https://api.panel.rtbhouse.com/v5"
TIMEOUT  = 60


def _get_credentials() -> tuple[str, str]:
    email    = os.environ.get("RTBHOUSE_EMAIL", "")
    password = os.environ.get("RTBHOUSE_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("RTBHOUSE_EMAIL 또는 RTBHOUSE_PASSWORD 환경변수가 없습니다.")
    return email, password


def _call_api(email: str, password: str, advertiser_hash: str, params: dict[str, Any]) -> list[dict]:
    url = f"{API_BASE}/advertisers/{advertiser_hash}/rtb-stats"
    logger.info(f"RTB API 호출: {url} | params={params}")

    resp = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(email, password),
        timeout=TIMEOUT,
    )

    if not resp.ok:
        raise RuntimeError(f"RTB API 오류: {resp.status_code} {resp.text[:300]}")

    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"RTB API 응답 오류: {payload}")

    return payload.get("data", [])


def _extract_hash_from_url(dashboard_url: str) -> str:
    """
    'https://panel.rtbhouse.com/dashboard/zjgMiqEIsN3oQNMPG6hc?...'
    → 'zjgMiqEIsN3oQNMPG6hc'
    """
    path = dashboard_url.split("?")[0].rstrip("/")
    return path.split("/")[-1]


def fetch_campaign_day_rows(advertiser_hash: str, target_date: str, campaign_map: dict, label: str) -> list[dict] | None:
    """
    캠페인(서브캠페인)별로 나뉜 하루치 지표를 조회해 시트 행 후보 목록으로 반환.
    campaign_map: config.json의 "app_campaign_map" (서브캠페인명 → {label, material}).
    campaign_map에 없는 서브캠페인은 건너뛰고 경고 로그만 남긴다.
    반환값: [{"campaign_label": str, "material": str, "imps": int, "clicks": int, "cost": int}, ...] 또는 실패 시 None.

    RTB House rtb-stats를 groupBy=subcampaign으로 조회하면 각 행의 "subcampaign" 필드에
    캠페인 이름이 직접 들어온다(별도 이름 조회 API 불필요. 2026-08-10 실 API 응답으로 확인).
    """
    email, password = _get_credentials()

    rows = _call_api(
        email=email,
        password=password,
        advertiser_hash=advertiser_hash,
        params={
            "dayFrom": target_date,
            "dayTo":   target_date,
            "groupBy": "subcampaign",
            "metrics": "impsCount-clicksCount-campaignCost",
        },
    )
    logger.info(f"[RTB {label} 캠페인별] API 응답 행 수: {len(rows)}")

    if not rows:
        logger.warning(f"[RTB {label} 캠페인별] {target_date} 데이터 없음")
        return None

    results = []
    for r in rows:
        campaign_name = r.get("subcampaign")
        mapping = campaign_map.get(campaign_name) if campaign_name else None

        if mapping is None:
            logger.warning(
                f"[RTB {label} 캠페인별] 매핑 안 된 캠페인 건너뜀 "
                f"(name={campaign_name}) — config.json의 app_campaign_map에 추가 필요"
            )
            continue

        imps   = int(float(r.get("impsCount",      0) or 0))
        clicks = int(float(r.get("clicksCount",    0) or 0))
        cost   =       float(r.get("campaignCost", 0) or 0)

        results.append({
            "campaign_label": mapping["label"],
            "material":       mapping["material"],
            "imps":   imps,
            "clicks": clicks,
            "cost":   int(round(cost)),
        })

    if not results:
        logger.warning(f"[RTB {label} 캠페인별] 매핑된 캠페인이 하나도 없음")
        return None

    logger.info(f"[RTB {label} 캠페인별] 수집 완료 → {results}")
    return results


def fetch_day_totals(advertiser_hash: str, target_date: str, label: str) -> dict | None:
    """
    target_date: 'YYYY-MM-DD'
    returns: {"imps": int, "clicks": int, "cost": int} or None
    """
    try:
        email, password = _get_credentials()
        rows = _call_api(
            email=email,
            password=password,
            advertiser_hash=advertiser_hash,
            params={
                "dayFrom": target_date,
                "dayTo":   target_date,
                "groupBy": "day",
                "metrics": "impsCount-clicksCount-campaignCost",
            },
        )
        logger.info(f"[RTB {label}] API 응답 행 수: {len(rows)}")

        if not rows:
            logger.warning(f"[RTB {label}] {target_date} 데이터 없음")
            return None

        imps   = sum(int(float(r.get("impsCount",      0) or 0)) for r in rows)
        clicks = sum(int(float(r.get("clicksCount",    0) or 0)) for r in rows)
        cost   = sum(      float(r.get("campaignCost", 0) or 0)  for r in rows)

        result = {"imps": imps, "clicks": clicks, "cost": int(round(cost))}
        logger.info(f"[RTB {label}] 수집 완료 → {result}")
        return result

    except Exception as e:
        logger.error(f"[RTB {label}] 오류: {e}")
        return None


def scrape(
    app_url: str,
    web_url: str,
    target_date: str | None = None,
    app_campaign_map: dict | None = None,
) -> tuple[list[dict] | None, dict | None]:
    """
    RTB House APP / WEB 전일자 데이터를 API로 수집.
    target_date: 'YYYY-MM-DD' 형식, None이면 전일자 자동 계산
    app_campaign_map: config.json의 "app_campaign_map"이 있으면 APP은 캠페인별로 나눠서 수집.
                       실패/데이터 없음이면 기존 대시보드 합산 방식으로 폴백.

    반환값:
      app_data: [{"campaign_label", "material", "imps", "clicks", "cost"}, ...] 또는 None
      web_data: {"imps", "clicks", "cost"} 또는 None (WEB은 기존 대시보드 합산 방식 그대로)
    """
    yesterday = target_date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"RTB House API 크롤링 시작 | 대상 날짜: {yesterday}")

    app_hash = _extract_hash_from_url(app_url)
    web_hash = _extract_hash_from_url(web_url)

    app_data: list[dict] | None = None
    if app_campaign_map:
        try:
            app_data = fetch_campaign_day_rows(app_hash, yesterday, app_campaign_map, "APP")
        except Exception as e:
            logger.error(f"[RTB APP 캠페인별] 오류: {e}")
            app_data = None

    if app_data is None:
        logger.warning("[RTB APP] 캠페인별 데이터 없음/실패 → 대시보드 합산 방식으로 폴백")
        fallback = fetch_day_totals(app_hash, yesterday, "APP")
        app_data = [{"campaign_label": "RTB_APP", "material": "없음", **fallback}] if fallback else None

    web_data = fetch_day_totals(web_hash, yesterday, "WEB")

    return app_data, web_data
