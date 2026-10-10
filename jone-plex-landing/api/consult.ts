/**
 * Vercel 서버 함수: 상담 신청 접수  (POST /api/consult)
 *
 * 사용하려면
 *  1) src/config/site.ts → form.endpoint 를 '/api/consult' 로 변경
 *  2) Vercel 프로젝트 → Settings → Environment Variables 에 아래 중 하나 이상 설정
 *
 *  [방법 A] 웹훅으로 전달 (Google Apps Script·Make·Zapier·Slack 등)
 *     CONSULT_WEBHOOK_URL = 신청 내용을 JSON 으로 받을 주소
 *
 *  [방법 B] 이메일로 받기 (Resend - https://resend.com)
 *     RESEND_API_KEY     = re_xxxxxxxx
 *     CONSULT_TO_EMAIL   = 신청서를 받을 관리자 이메일
 *     CONSULT_FROM_EMAIL = Resend 에서 인증한 발신 주소 (예: '분양상담 <noreply@내도메인.com>')
 *
 * 아무 것도 설정하지 않으면 503 을 돌려주고, 화면에는 "설정이 완료되지 않았습니다" 오류가 표시됩니다.
 * (설정이 안 된 상태에서 "접수 완료"로 보이는 일이 없도록 하기 위함)
 *
 * ※ Vercel 함수는 별도로 묶여 배포되므로 src 폴더의 코드를 가져오지 않고 이 파일 안에서 검증합니다.
 */

interface ConsultBody {
  name?: unknown;
  phone?: unknown;
  floor?: unknown;
  purpose?: unknown;
  message?: unknown;
  agreedAt?: unknown;
  pageUrl?: unknown;
  _gotcha?: unknown;
}

const PURPOSES = ['실사용', '임대', '투자 검토', '기타'];

const json = (status: number, body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json; charset=utf-8' } });

const str = (v: unknown, max: number) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

/** HTML 이메일에 넣을 때 태그가 실행되지 않도록 변환 */
const escapeHtml = (v: string) =>
  v.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export async function POST(request: Request): Promise<Response> {
  let body: ConsultBody;
  try {
    body = (await request.json()) as ConsultBody;
  } catch {
    return json(400, { ok: false, error: 'invalid_json' });
  }

  // 스팸 로봇이 숨은 칸을 채운 경우: 성공처럼 응답하고 실제로는 버림
  if (str(body._gotcha, 200)) return json(200, { ok: true });

  const data = {
    name: str(body.name, 30),
    phone: str(body.phone, 20),
    floor: str(body.floor, 30) || '미정',
    purpose: str(body.purpose, 20),
    message: str(body.message, 1000),
    agreedAt: str(body.agreedAt, 40),
    pageUrl: str(body.pageUrl, 300),
    receivedAt: new Date().toISOString(),
  };

  // 서버 쪽 필수값 검증 (화면 검증을 우회한 요청 차단)
  const digits = data.phone.replace(/\D/g, '');
  const errors: string[] = [];
  if (data.name.length < 2) errors.push('name');
  if (!/^010\d{8}$/.test(digits) && !/^01[16789]\d{7,8}$/.test(digits)) errors.push('phone');
  if (!PURPOSES.includes(data.purpose)) errors.push('purpose');
  if (!data.agreedAt) errors.push('agree');
  if (errors.length) return json(400, { ok: false, error: 'validation', fields: errors });

  const webhookUrl = process.env.CONSULT_WEBHOOK_URL;
  const resendKey = process.env.RESEND_API_KEY;
  const toEmail = process.env.CONSULT_TO_EMAIL;
  const fromEmail = process.env.CONSULT_FROM_EMAIL;
  const emailReady = Boolean(resendKey && toEmail && fromEmail);

  if (!webhookUrl && !emailReady) {
    return json(503, { ok: false, error: 'not_configured' });
  }

  const tasks: Promise<Response>[] = [];

  if (webhookUrl) {
    tasks.push(
      fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    );
  }

  if (emailReady) {
    const rows = [
      ['이름', data.name],
      ['연락처', data.phone],
      ['관심 층', data.floor],
      ['상담 목적', data.purpose],
      ['문의 내용', data.message || '-'],
      ['개인정보 동의', data.agreedAt],
      ['접수 페이지', data.pageUrl],
    ];
    tasks.push(
      fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${resendKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from: fromEmail,
          to: [toEmail],
          subject: `[분양 상담 신청] ${data.name} / ${data.floor} / ${data.purpose}`,
          html: `<table cellpadding="6" style="border-collapse:collapse">${rows
            .map(([k, v]) => `<tr><th align="left" style="background:#f2f5fa">${k}</th><td>${escapeHtml(v).replace(/\n/g, '<br>')}</td></tr>`)
            .join('')}</table>`,
        }),
      }),
    );
  }

  // 설정된 전달 방법이 하나라도 성공하면 접수 성공으로 처리
  const results = await Promise.allSettled(tasks);
  const delivered = results.some((r) => r.status === 'fulfilled' && r.value.ok);
  if (!delivered) {
    console.error('[consult] delivery failed', results.map((r) => (r.status === 'fulfilled' ? r.value.status : String(r.reason))));
    return json(502, { ok: false, error: 'delivery_failed' });
  }
  return json(200, { ok: true });
}
