def should_upload(errors: list[str], allow_partial: bool = False) -> bool:
    return not errors or allow_partial


def already_uploaded(all_values: list[list], target_date: str) -> bool:
    """시트 전체 값에서 첫 번째 열(날짜)이 target_date인 행이 있으면 True."""
    return any(row and str(row[0]).strip() == target_date for row in all_values)


def is_auto_run(event_name: str, target_date: str = "", date_from: str = "", date_to: str = "") -> bool:
    """
    자동 실행 여부 판정.
    - schedule 이벤트는 자동 실행.
    - workflow_dispatch라도 날짜 입력이 하나도 없으면(예: Apps Script 정시 호출) 자동 실행.
      재실행 페이지/수동 실행은 항상 날짜를 넘기므로 자동으로 취급하지 않는다.
    """
    if event_name == "schedule":
        return True
    if event_name == "workflow_dispatch":
        return not any(v.strip() for v in (target_date, date_from, date_to))
    return False
