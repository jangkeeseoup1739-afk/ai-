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

  it('구글 Apps Script 주소면 text/plain 으로 전송, 응답 ok:false 는 실패 처리', async () => {
    const url = 'https://script.google.com/macros/s/abc/exec';
    const fetchSpy = vi.fn().mockResolvedValue(new Response('{"ok":false,"error":"validation"}', { status: 200 }));
    vi.stubGlobal('fetch', fetchSpy);
    render(<ConsultForm endpoint={url} />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/접수가 처리되지 않았습니다/)).toBeInTheDocument();
    expect(fetchSpy.mock.calls[0][1].headers['Content-Type']).toMatch(/^text\/plain/);
    expect(JSON.parse(fetchSpy.mock.calls[0][1].body)).toMatchObject({ name: '홍길동', purpose: '임대' });
  });

  it('구글 Apps Script 응답 ok:true 면 접수 완료', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 })));
    render(<ConsultForm endpoint="https://script.google.com/macros/s/abc/exec" />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText('상담 신청이 접수되었습니다')).toBeInTheDocument();
  });

  it('네트워크 오류 처리', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fail')));
    render(<ConsultForm endpoint="https://example.com/form" />);
    await fillValid();
    await userEvent.click(screen.getByRole('button', { name: '상담 신청하기' }));
    expect(await screen.findByText(/네트워크 오류/)).toBeInTheDocument();
  });

  it('개인정보 전문 보기 팝업에 미입력 운영자 정보가 표시됨', async () => {
    render(<ConsultForm endpoint="" />);
    await userEvent.click(screen.getByRole('button', { name: '전문 보기' }));
    expect(screen.getByRole('dialog')).toHaveTextContent('운영자 입력 필요');
  });
});
