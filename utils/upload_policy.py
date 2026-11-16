def should_upload(errors: list[str], allow_partial: bool = False) -> bool:
    return not errors or allow_partial


def already_uploaded(all_values: list[list], target_date: str) -> bool:
    """시트 전체 값에서 첫 번째 열(날짜)이 target_date인 행이 있으면 True."""
    return any(row and str(row[0]).strip() == target_date for row in all_values)
