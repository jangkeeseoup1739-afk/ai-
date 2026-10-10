import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConsultForm } from '../components/ConsultForm';

async function fillValid() {
  await userEvent.type(screen.getByLabelText(/이름/), '홍길동');
  await userEvent.type(screen.getByLabelText(/연락처/), '01012345678');
  await userEvent.click(screen.getByLabelText('임대'));
  await userEvent.click(screen.getByLabelText(/개인정보 수집 및 이용에 동의/));
}

afterEach(() => vi.unstubAllGlobals());

describe('상담 신청 폼', () => {
  it('빈 값 제출 시 필수 항목 오류 표시', async () => {
    render(<ConsultForm endpoint="" />);
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(screen.getByText('이름을 입력해 주세요.')).toBeInTheDocument();
    expect(screen.getByText('연락처를 입력해 주세요.')).toBeInTheDocument();
    expect(screen.getByText('상담 목적을 선택해 주세요.')).toBeInTheDocument();
    expect(screen.getByText('개인정보 수집 및 이용에 동의해 주세요.')).toBeInTheDocument();
    expect(screen.getByLabelText(/이름/)).toHaveFocus();
  });

  it('연락처 자동 하이픈 + 잘못된 번호 오류', async () => {
    render(<ConsultForm endpoint="" />);
    const phone = screen.getByLabelText(/연락처/);
    await userEvent.type(phone, '01012345678');
    expect(phone).toHaveValue('010-1234-5678');
    await userEvent.clear(phone);
    await userEvent.type(phone, '0101234');
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(screen.getByText(/휴대전화 번호를 정확히/)).toBeInTheDocument();
  });

  it('테스트 모드: 전송하지 않고, 접수 완료라고 표시하지 않음', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    render(<ConsultForm endpoint="" />);
    expect(screen.getByText(/테스트 모드 – 온라인 신청이 아직 전송되지 않습니다/)).toBeInTheDocument();
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/신청서는 전송되지 않았습니다/)).toBeInTheDocument();
    expect(screen.queryByText('상담 신청이 접수되었습니다')).not.toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('전송 주소 연결 시 서버 성공 응답이면 접수 완료', async () => {
    const fetchSpy = vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
    vi.stubGlobal('fetch', fetchSpy);
    render(<ConsultForm endpoint="/api/consult" />);
    expect(screen.queryByText(/테스트 모드/)).not.toBeInTheDocument();
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText('상담 신청이 접수되었습니다')).toBeInTheDocument();
    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe('/api/consult');
    const body = JSON.parse(init.body);
    expect(body).toMatchObject({ name: '홍길동', phone: '010-1234-5678', purpose: '임대', floor: '미정', _gotcha: '' });
  });

  it('서버 오류면 접수 완료가 아니라 오류 표시', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })));
    render(<ConsultForm endpoint="/api/consult" />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/설정이 완료되지 않았습니다/)).toBeInTheDocument();
    expect(screen.queryByText('상담 신청이 접수되었습니다')).not.toBeInTheDocument();
  });

  const APPS_SCRIPT = 'https://script.google.com/macros/s/abc/exec';

  it('구글 Apps Script: 기존 홈페이지와 같은 형식(text/plain JSON)으로 전송 → 접수 완료', async () => {
    const fetchSpy = vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
    vi.stubGlobal('fetch', fetchSpy);
    render(<ConsultForm endpoint={APPS_SCRIPT} />);
    await fillValid();
    await userEvent.selectOptions(screen.getByLabelText('관심 층'), '3f');
    await userEvent.type(screen.getByLabelText(/문의 내용/), '30평대 문의');
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText('상담 신청이 접수되었습니다')).toBeInTheDocument();

    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe(APPS_SCRIPT);
    expect(init.headers['Content-Type']).toMatch(/^text\/plain/);
    const lead = JSON.parse(init.body);
    expect(lead).toMatchObject({
      name: '홍길동',
      phone: '010-1234-5678',
      interestCategory: '관심 층: 지상 3층',
      preferredType: '상담 목적: 임대',
      preferredTime: '',
      message: '30평대 문의',
      privacyAgreed: true,
    });
    expect(lead.id).toMatch(/^LP-\d{6}$/);
    expect(typeof lead.createdAt).toBe('string');
  });

  it('구글 Apps Script: 응답 ok:false 면 실패 표시', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"ok":false,"error":"name_and_phone_required"}', { status: 200 })));
    render(<ConsultForm endpoint={APPS_SCRIPT} />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/접수가 처리되지 않았습니다/)).toBeInTheDocument();
  });

  it('구글 Apps Script: 응답을 못 읽으면 no-cors 로 같은 접수번호를 한 번 더 전송', async () => {
    const fetchSpy = vi.fn().mockRejectedValueOnce(new TypeError('cors')).mockResolvedValueOnce(new Response(null, { status: 200 }));
    vi.stubGlobal('fetch', fetchSpy);
    render(<ConsultForm endpoint={APPS_SCRIPT} />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText('상담 신청이 접수되었습니다')).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(2);
    expect(fetchSpy.mock.calls[1][1].mode).toBe('no-cors');
    expect(fetchSpy.mock.calls[1][1].body).toBe(fetchSpy.mock.calls[0][1].body); // 같은 접수번호 → 시트에서 중복 제거
  });

  it('구글 Apps Script: 두 번 다 실패하면 오류 표시', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    render(<ConsultForm endpoint={APPS_SCRIPT} />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/네트워크 오류/)).toBeInTheDocument();
    expect(screen.queryByText('상담 신청이 접수되었습니다')).not.toBeInTheDocument();
  });

  it('네트워크 오류 처리', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fail')));
    render(<ConsultForm endpoint="https://example.com/form" />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/네트워크 오류/)).toBeInTheDocument();
  });

  it('개인정보 전문 보기: 보유 기간·보호책임자·처리방침 링크', async () => {
    render(<ConsultForm endpoint="" />);
    await userEvent.click(screen.getByRole('button', { name: '전문 보기' }));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveTextContent('상담 완료 및 분양 종료 시까지');
    expect(dialog).toHaveTextContent('개인정보 보호책임자: 분양 상담 담당자');
    expect(dialog).toHaveTextContent('Google LLC');
    expect(dialog).not.toHaveTextContent('운영자 입력 필요');
    expect(screen.getByRole('link', { name: /개인정보처리방침 전문 보기/ })).toHaveAttribute('href', 'https://joneflex.homefixweb.com/privacy');
  });
});
