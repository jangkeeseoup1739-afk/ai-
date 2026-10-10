/**
 * 페이지 전체 조립 파일
 * 섹션 순서를 바꾸거나 섹션을 빼고 싶다면 아래 JSX 순서만 바꾸면 됩니다.
 */
import { useCallback, useState } from 'react';
import { ConsultForm } from './components/ConsultForm';
import { CoreInfoCards } from './components/CoreInfoCards';
import { FixedContactBar } from './components/FixedContactBar';
import { FloorGuideSection } from './components/FloorGuideSection';
import { Footer } from './components/Footer';
import { Header } from './components/Header';
import { HeroSection } from './components/HeroSection';
import { KeyMeritsSection } from './components/KeyMeritsSection';
import { LocationSection } from './components/LocationSection';
import { SetupNoticeProvider } from './components/SetupNotice';
import { UnitTypesSection } from './components/UnitTypesSection';
import { SECTION, scrollToId } from './lib/links';

export default function App() {
  // 층별 정보 → 상담 폼으로 "관심 층"을 넘겨주기 위한 상태
  const [floorPreset, setFloorPreset] = useState<{ floorId: string; token: number } | null>(null);

  const handleConsultFloor = useCallback((floorId: string) => {
    setFloorPreset({ floorId, token: Date.now() });
    scrollToId(SECTION.consult);
  }, []);

  return (
    <SetupNoticeProvider>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-navy-900">
        본문 바로가기
      </a>
      <Header />
      <main id="main">
        <HeroSection />
        <CoreInfoCards />
        <KeyMeritsSection />
        <FloorGuideSection onConsultFloor={handleConsultFloor} />
        <UnitTypesSection />
        <LocationSection />
        <ConsultForm preset={floorPreset} />
      </main>
      <Footer />
      <FixedContactBar />
    </SetupNoticeProvider>
  );
}
