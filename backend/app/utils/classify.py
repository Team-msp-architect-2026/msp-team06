# HomeLens AI - 뉴스 카테고리 분류 유틸

def classify_category(title: str) -> str:
    if any(kw in title for kw in [
        "정책", "규제", "법안", "세금", "대출", "금리",
        "LTV", "DSR", "공급", "청약", "임대차", "전월세",
        "보증금", "상한제", "GTX", "지하철", "노선",
        "금융", "은행", "이자", "부채", "완화", "강화"
    ]):
        return "policy"
    elif any(kw in title for kw in [
        "개발", "재건축", "재개발", "착공", "분양", "입주",
        "신축", "정비구역", "용적률", "건축", "도로",
        "아파트", "단지", "공사", "허가", "준공"
    ]):
        return "development"
    elif any(kw in title for kw in [
        "법원", "판결", "소송", "계약", "중개", "사기",
        "위반", "처벌", "고발", "수사", "구속"
    ]):
        return "law"
    else:
        return "market"