/** @type {import('tailwindcss').Config} */
// ─────────────────────────────────────────────────────────────
// Tailwind 설정
// 브랜드 색상(네이비·골드)은 여기서 한 번에 바꿀 수 있습니다.
// 예) bg-navy-900, text-gold-500, border-gold-300
// ─────────────────────────────────────────────────────────────
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#F2F5FA',
          100: '#E3E9F3',
          200: '#C3CFE3',
          300: '#94A7C8',
          600: '#2A4473',
          700: '#1D345E',
          800: '#152A4E',
          900: '#0F1F3D',
          950: '#0A1529',
        },
        gold: {
          100: '#F7EFDD',
          200: '#EEDDB6',
          300: '#E2C78C',
          400: '#D4B06A',
          500: '#C29A4E',
          600: '#A37F3B',
          700: '#7F622D',
        },
      },
      fontFamily: {
        sans: [
          'Pretendard Variable',
          'Pretendard',
          '-apple-system',
          'BlinkMacSystemFont',
          'Apple SD Gothic Neo',
          'Noto Sans KR',
          'Malgun Gothic',
          'sans-serif',
        ],
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 31, 61, 0.06), 0 8px 24px rgba(15, 31, 61, 0.08)',
        'card-hover': '0 2px 4px rgba(15, 31, 61, 0.08), 0 16px 40px rgba(15, 31, 61, 0.14)',
      },
      maxWidth: {
        content: '1180px',
      },
    },
  },
  plugins: [],
};
