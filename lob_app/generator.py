from __future__ import annotations

from datetime import datetime
from typing import Optional


def _normalize_yes_no(value: str | bool | None) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return "No"
    text = str(value).strip().lower()
    return "Yes" if text in {"y", "yes", "true", "1"} else "No"


def _detect_issue_keywords(text: str) -> set[str]:
    lowered = text.lower()
    keywords: set[str] = set()
    if any(k in lowered for k in ["ordered by mistake", "by mistake", "accidentally ordered", "wrong product"]):
        keywords.add("ordered_by_mistake")
    if any(k in lowered for k in ["open", "opened", "unboxed"]):
        keywords.add("opened")
    if any(k in lowered for k in ["wrong item", "expectation mismatch", "mismatch", "different from pdp", "pdp", "product mismatch"]):
        keywords.add("pdp_mismatch")
    if any(k in lowered for k in ["defect", "defective", "damaged", "not working", "faulty"]):
        keywords.add("defective")
    return keywords


def _choose_offered_resolution(issue_type: str, voc: str, stock_yes_no: str) -> str:
    text = f"{issue_type} {voc}".lower()
    keys = _detect_issue_keywords(text)

    if "ordered_by_mistake" in keys:
        return "Service No"

    if "pdp_mismatch" in keys:
        return "Replacement" if stock_yes_no == "Yes" else "Service No"

    if "defective" in keys:
        return "Replacement" if stock_yes_no == "Yes" else "Service No"

    # Fallback: if stock not available, default to Service No; otherwise Replacement
    return "Service No" if stock_yes_no == "No" else "Replacement"


def _resolution_reason(offered_resolution: str, issue_type: str, voc: str) -> str:
    text = f"{issue_type} {voc}".lower()
    keys = _detect_issue_keywords(text)

    if offered_resolution == "Service No" and "ordered_by_mistake" in keys:
        return (
            "Service No – As per SOP for accidental orders, no RPU is initiated for "
            "unintended purchases. Customer advised politely."
        )
    if offered_resolution == "Service No" and "pdp_mismatch" in keys:
        return (
            "Service No – Replacement not possible due to stock/slot unavailability as per SOP."
        )
    if offered_resolution == "Replacement" and "pdp_mismatch" in keys:
        return (
            "Replacement – As per Wrong Item / Expectation Mismatch SOP where stock is available."
        )
    if offered_resolution == "Replacement" and "defective" in keys:
        return (
            "Replacement – As per SOP for defective/damaged items when stock is available."
        )
    if offered_resolution == "Service No" and "defective" in keys:
        return (
            "Service No – Stock/slot unavailable for replacement as per SOP."
        )
    # Generic reasons
    if offered_resolution == "Service No":
        return "Service No – Applied per SOP based on the provided scenario."
    if offered_resolution == "Replacement":
        return "Replacement – Applied per SOP when stock/slot is available."
    return f"{offered_resolution} – Applied per SOP."


def _format_follow_up(date_text: Optional[str]) -> str:
    if not date_text:
        return "NA"
    cleaned = date_text.strip()
    known_formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in known_formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            continue
    # If unparseable, return as-is to avoid fabricating data
    return cleaned


def generate_lob_summary(
    *,
    issue_type: str,
    voc: str,
    stock_available: str | bool,
    follow_up_date: Optional[str] = None,
    dp_sm_call: Optional[str] = None,
) -> str:
    """Generate a LOB summary using the specified template and SOP rules.

    Parameters:
        issue_type: Short label of the issue (e.g., "Ordered by Mistake").
        voc: Voice of Customer / customer statement.
        stock_available: Yes/No or boolean.
        follow_up_date: Optional date; various formats accepted; returned as DD-MM-YYYY.
        dp_sm_call: Override for DP/SM call; default is "NA".
    """
    stock_yes_no = _normalize_yes_no(stock_available)
    offered_resolution = _choose_offered_resolution(issue_type, voc, stock_yes_no)
    reason = _resolution_reason(offered_resolution, issue_type, voc)

    summary_line = "Ordered by Mistake / By mistake ordered / Service No" if _detect_issue_keywords(issue_type + " " + voc) & {"ordered_by_mistake"} else issue_type.strip() or "Service No"

    dp_sm_value = (dp_sm_call or "NA").strip() or "NA"
    follow_value = _format_follow_up(follow_up_date)

    # Customer response cannot be assumed; keep Pending by default
    customer_response = "Pending"

    lines = [
        f"Brief summary of customer concern: {summary_line}",
        f"\nDP/SM call: {dp_sm_value}",
        f"\nResolution shared along with the reason: {reason}",
        f"\nStock/Slot Available: {stock_yes_no}",
        f"\nOffered resolution: {offered_resolution}",
        f"\nCustomer response: {customer_response}",
        f"\nFollow up – date and time: {follow_value}",
    ]
    return "\n".join(lines)


