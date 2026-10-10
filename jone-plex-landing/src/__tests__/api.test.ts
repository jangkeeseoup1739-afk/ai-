/**
 * @vitest-environment node
 */
import { POST } from '../../api/consult';

const valid = {
  name: '홍길동',
  phone: '010-1234-5678',
  floor: '지상 3층',
  purpose: '실사용',
  message: '<b>문의</b>',
  agreedAt: '2026-10-10T00:00:00.000Z',
  pageUrl: 'https://example.com/',
  _gotcha: '',
};
const req = (body: unknown) =>
  new Request('http://localhost/api/consult', { method: 'POST', body: typeof body === 'string' ? body : JSON.stringify(body) });

const ENV_KEYS = ['CONSULT_WEBHOOK_URL', 'RESEND_API_KEY', 'CONSULT_TO_EMAIL', 'CONSULT_FROM_EMAIL'];
afterEach(() => {
  ENV_KEYS.forEach((k) => delete process.env[k]);
  vi.unstubAllGlobals();
});

describe('POST /api/consult', () => {
  it('JSON 이 아니면 400', async () => {
    expect((await POST(req('not json'))).status).toBe(400);
  });
  it('필수값 오류면 400', async () => {
    const res = await POST(req({ ...valid, phone: '123', purpose: '아무거나' }));
    expect(res.status).toBe(400);
    expect((await res.json()).fields).toEqual(['phone', 'purpose']);
  });
  it('전달 방법 미설정이면 503 (접수 완료로 보이지 않게)', async () => {
    expect((await POST(req(valid))).status).toBe(503);
  });
  it('스팸 숨은 칸이 채워지면 전달 없이 200', async () => {
    const f = vi.fn();
    vi.stubGlobal('fetch', f);
    process.env.CONSULT_WEBHOOK_URL = 'https://hook.example.com';
    expect((await POST(req({ ...valid, _gotcha: 'bot' }))).status).toBe(200);
    expect(f).not.toHaveBeenCalled();
  });
  it('웹훅 전달 성공 시 200', async () => {
    const f = vi.fn().mockResolvedValue(new Response('ok'));
    vi.stubGlobal('fetch', f);
    process.env.CONSULT_WEBHOOK_URL = 'https://hook.example.com';
    expect((await POST(req(valid))).status).toBe(200);
    expect(f.mock.calls[0][0]).toBe('https://hook.example.com');
    expect(JSON.parse(f.mock.calls[0][1].body)).toMatchObject({ name: '홍길동', floor: '지상 3층' });
  });
  it('이메일(Resend) 전달 시 HTML 이스케이프', async () => {
    const f = vi.fn().mockResolvedValue(new Response('{}'));
    vi.stubGlobal('fetch', f);
    Object.assign(process.env, { RESEND_API_KEY: 're_x', CONSULT_TO_EMAIL: 'a@b.com', CONSULT_FROM_EMAIL: 'c@d.com' });
    expect((await POST(req(valid))).status).toBe(200);
    const sent = JSON.parse(f.mock.calls[0][1].body);
    expect(sent.html).toContain('&lt;b&gt;문의');
    expect(sent.to).toEqual(['a@b.com']);
  });
  it('전달 실패면 502', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 500 })));
    process.env.CONSULT_WEBHOOK_URL = 'https://hook.example.com';
    expect((await POST(req(valid))).status).toBe(502);
  });
});
