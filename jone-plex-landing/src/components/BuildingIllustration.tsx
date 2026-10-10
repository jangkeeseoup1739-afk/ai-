/**
 * 첫 화면 배경용 건물 일러스트 (SVG)
 * - 실제 현장 사진이 준비되기 전 임시로 쓰는 "그림"입니다. 실제 건물 외관을 표현한 것이 아닙니다.
 * - 이미지 파일이 아니라 코드로 그려 용량이 거의 0에 가깝습니다.
 */
export function BuildingIllustration({ className }: { className?: string }) {
  // 10개 층 × 7칸 창문을 반복해서 그립니다.
  const floors = Array.from({ length: 10 }, (_, i) => i);
  const cols = Array.from({ length: 7 }, (_, i) => i);

  return (
    <svg viewBox="0 0 520 560" className={className} aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="bi-body" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#2A4473" />
          <stop offset="1" stopColor="#152A4E" />
        </linearGradient>
        <linearGradient id="bi-glass" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#E2C78C" stopOpacity=".55" />
          <stop offset="1" stopColor="#94A7C8" stopOpacity=".15" />
        </linearGradient>
      </defs>
      {/* 뒤쪽 보조 동 */}
      <rect x="10" y="200" width="120" height="360" fill="#152A4E" />
      {/* 본동 */}
      <rect x="120" y="40" width="360" height="520" fill="url(#bi-body)" />
      <rect x="120" y="40" width="360" height="8" fill="#C29A4E" />
      {floors.map((f) =>
        cols.map((c) => (
          <rect key={`${f}-${c}`} x={140 + c * 48} y={70 + f * 44} width="36" height="28" rx="2" fill="url(#bi-glass)" />
        )),
      )}
      {/* 램프(차량 경사로) 표현 */}
      <path d="M0 560 L180 470 L200 470 L200 560 Z" fill="#0F1F3D" />
      <path d="M0 560 L180 470" stroke="#C29A4E" strokeWidth="3" strokeDasharray="10 8" />
      <rect x="0" y="556" width="520" height="4" fill="#C29A4E" opacity=".6" />
    </svg>
  );
}
