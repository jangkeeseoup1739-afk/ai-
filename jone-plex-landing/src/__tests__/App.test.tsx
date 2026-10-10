import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import { floors } from '../config/floors';

beforeAll(() => {
  // jsdom 에는 scrollIntoView 가 없어서 빈 함수로 대체
  Element.prototype.scrollIntoView = () => {};
});

describe('랜딩페이지 전체', () => {
  it('메인 제목과 상담 버튼 3개가 첫 화면에 있다', () => {
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('주안국가산단역 초역세권제이원플렉스지식산업센터');
    const hero = screen.getByRole('heading', { level: 1 }).closest('section')!;
    expect(within(hero).getByRole('link', { name: /분양 상담 신청/ })).toHaveAttribute('href', '#consult');
    expect(within(hero).getByRole('link', { name: /전화 상담/ })).toHaveAttribute('href', 'tel:01088737258');
    expect(within(hero).getByRole('button', { name: /카카오톡 상담/ })).toBeInTheDocument();
  });

  it('카카오톡 채널 미설정 시 가짜 링크 대신 설정 안내창', async () => {
    render(<App />);
    const hero = screen.getByRole('heading', { level: 1 }).closest('section')!;
    await userEvent.click(within(hero).getByRole('button', { name: /카카오톡 상담/ }));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveTextContent('kakaoChannelUrl');
    await userEvent.click(within(dialog).getByRole('button', { name: '확인' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('층 탭을 누르면 안내 영역이 바뀌고, 값이 없으면 "상담 문의"로 표시', async () => {
    render(<App />);
    const panel = screen.getByRole('tabpanel');
    for (const f of floors) {
      await userEvent.click(screen.getByRole('tab', { name: f.label }));
      expect(screen.getByRole('tab', { name: f.label })).toHaveAttribute('aria-selected', 'true');
      expect(within(panel).getByRole('heading', { level: 3 })).toHaveTextContent(f.label);
      expect(within(panel).getByRole('button', { name: `${f.label} 상담 문의` })).toBeInTheDocument();
    }
    expect(within(panel).getAllByText('상담 문의').length).toBe(3);
    // 도면이 등록된 층은 이미지, 없는 층은 "도면 준비 중"
    for (const f of floors) {
      await userEvent.click(screen.getByRole('tab', { name: f.label }));
      if (f.planImage) {
        expect(within(panel).getByRole('img', { name: f.planImageAlt })).toHaveAttribute('src', f.planImage);
        expect(within(panel).getByRole('link', { name: '도면 크게 보기' })).toHaveAttribute('target', '_blank');
      } else {
        expect(within(panel).getByText(/도면 준비 중/)).toBeInTheDocument();
      }
    }
  });

  it('키보드 → 로 다음 층 탭 이동', async () => {
    render(<App />);
    screen.getByRole('tab', { name: floors[0].label }).focus();
    await userEvent.keyboard('{ArrowRight}');
    expect(screen.getByRole('tab', { name: floors[1].label })).toHaveAttribute('aria-selected', 'true');
  });

  it('층 상담 문의 → 상담 폼 관심 층 자동 선택', async () => {
    render(<App />);
    await userEvent.click(screen.getByRole('tab', { name: '지상 3층' }));
    await userEvent.click(screen.getByRole('button', { name: '지상 3층 상담 문의' }));
    expect(screen.getByLabelText('관심 층')).toHaveValue('3f');
  });

  it('지도 링크 미설정 시 지도 보기 버튼은 안내창을 연다', async () => {
    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: '지도 보기' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('location.maps');
  });
});

describe('기숙사 타입 안내', () => {
  it('타입별 실 수·면적(㎡/평)과 무상 제공 품목 표시', () => {
    render(<App />);
    const typeA = document.getElementById('type-a')!;
    expect(within(typeA).getByText(/A type 12실 · A1 type 54실/)).toBeInTheDocument();
    const contract = within(typeA).getByRole('row', { name: /계약면적/ });
    expect(contract).toHaveTextContent('53.2776');
    expect(within(document.getElementById('type-b')!).getByRole('row', { name: /전용면적/ })).toHaveTextContent('26.5660');
    expect(contract).toHaveTextContent('16.12');
    expect(within(document.getElementById('type-c')!).getByText(/C type 6실 · C1 type 27실/)).toBeInTheDocument();
    expect(screen.getByText('빌트인 냉장고')).toBeInTheDocument();
  });

  it('10층 탭 → C·C1 타입 보기 링크', async () => {
    render(<App />);
    await userEvent.click(screen.getByRole('tab', { name: '지상 10층 (복층)' }));
    expect(screen.getByRole('link', { name: /C · C1 타입 \(복층\) 평면·면적 보기/ })).toHaveAttribute('href', '#type-c');
  });
});
