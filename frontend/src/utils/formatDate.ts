export function formatRelativeDate(dateStr: string): string {
  // 네이버 날짜 형식 파싱 "Wed, 06 May 2026 09:00:00 +0900"
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "오늘";
  if (diffDays < 7) return `${diffDays}일 전`;
  if (diffDays < 14) return "1주 전";
  if (diffDays < 21) return "2주 전";
  if (diffDays < 28) return "3주 전";
  if (diffDays < 30) return "4주 전";

  // 30일 이상은 날짜 직접 표시
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}월 ${day}일`;
}
