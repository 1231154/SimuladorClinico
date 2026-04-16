import type {
  IniciarSessaoRequestDto,
  IniciarSessaoResponseDto,
  ProcessarNovaMensagemResponseDto,
  SessaoDeSimulacaoDto
} from './types';

const apiBaseUrl = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:5070').replace(/\/+$/, '');

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init.headers ?? {})
    }
  });

  const rawBody = await response.text();

  if (!response.ok) {
    const details = rawBody.trim();
    throw new Error(details || `Pedido falhou com HTTP ${response.status}`);
  }

  if (!rawBody) {
    return undefined as T;
  }

  return JSON.parse(rawBody) as T;
}

export const api = {
  baseUrl: apiBaseUrl,
  ping: () => request<{ status: string }>('/health'),
  iniciarSessao: (body: IniciarSessaoRequestDto) =>
    request<IniciarSessaoResponseDto>('/api/simulacoes/sessoes', {
      method: 'POST',
      body: JSON.stringify(body)
    }),
  enviarMensagem: (sessaoId: string, textoDaMensagem: string) =>
    request<ProcessarNovaMensagemResponseDto>(`/api/simulacoes/sessoes/${sessaoId}/mensagens`, {
      method: 'POST',
      body: JSON.stringify({ textoDaMensagem })
    }),
  obterSessao: (sessaoId: string) => request<SessaoDeSimulacaoDto>(`/api/simulacoes/sessoes/${sessaoId}`),
  concluirSessao: (sessaoId: string) =>
    request<SessaoDeSimulacaoDto>(`/api/simulacoes/sessoes/${sessaoId}/concluir`, {
      method: 'POST'
    })
};