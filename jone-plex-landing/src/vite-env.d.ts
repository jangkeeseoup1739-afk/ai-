/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 상담 폼 전송 주소 (site.ts 의 form.endpoint 보다 우선) */
  readonly VITE_CONSULT_ENDPOINT?: string;
}
