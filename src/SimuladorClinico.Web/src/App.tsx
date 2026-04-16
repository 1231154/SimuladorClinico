import { useEffect, useRef, useState } from 'react';
import { api } from './api';
import type {
  IniciarSessaoRequestDto,
  InteracaoChatDto,
  ProcessarNovaMensagemResponseDto,
  SessaoDeSimulacaoDto
} from './types';

type ChatRole = 'system' | 'profissional' | 'ia';

interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  timestamp: string;
}

interface ScenarioTemplate {
  name: string;
  description: string;
  casoId: string;
}

const DEMO_CASO_ID = '22222222-2222-2222-2222-222222222222';

const SCENARIOS: ScenarioTemplate[] = [
  {
    name: 'Urgência',
    description: 'Doente com dor torácica e avaliação inicial.',
    casoId: DEMO_CASO_ID
  },
  {
    name: 'Medicina interna',
    description: 'Queixa inespecífica, anamnese dirigida.',
    casoId: '44444444-4444-4444-4444-444444444444'
  },
  {
    name: 'Pediatria',
    description: 'Criança com febre e abordagem clínica.',
    casoId: '66666666-6666-6666-6666-666666666666'
  }
];

const ESTADO_LABELS: Record<number, string> = {
  1: 'Criada',
  2: 'Em andamento',
  3: 'Finalizada',
  4: 'Cancelada'
};

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'system',
  text: 'Seleciona um cenário rápido no menu e envia a primeira mensagem para começar a conversa.',
  timestamp: new Date().toISOString()
};

const FEEDBACK_PLACEHOLDER = 'Feature que sera implementada no futuro.';

function makeSystemMessage(text: string): ChatMessage {
  return {
    id: `system-${crypto.randomUUID()}`,
    role: 'system',
    text,
    timestamp: new Date().toISOString()
  };
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return 'Sem registo';
  }

  return new Intl.DateTimeFormat('pt-PT', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(new Date(value));
}

function mapSessionMessages(session: SessaoDeSimulacaoDto): ChatMessage[] {
  if (!session.interacoes.length) {
    return [WELCOME_MESSAGE];
  }

  return session.interacoes.map((interaction: InteracaoChatDto) => ({
    id: interaction.id,
    role: interaction.remetente === 1 ? 'profissional' : 'ia',
    text: interaction.textoDaMensagem,
    timestamp: interaction.timestamp
  }));
}

function normalizeError(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Ocorreu um erro inesperado.';
}

function makeMessageFromResponse(response: ProcessarNovaMensagemResponseDto): ChatMessage[] {
  const messages: ChatMessage[] = [
    {
      id: response.mensagemProfissional.id,
      role: 'profissional',
      text: response.mensagemProfissional.textoDaMensagem,
      timestamp: response.mensagemProfissional.timestamp
    }
  ];

  if (response.respostaIa) {
    messages.push({
      id: response.respostaIa.id,
      role: 'ia',
      text: response.respostaIa.textoDaMensagem,
      timestamp: response.respostaIa.timestamp
    });
  }

  return messages;
}

export default function App() {
  const [casoId, setCasoId] = useState(DEMO_CASO_ID);
  const [scenarioName, setScenarioName] = useState('Urgência');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [textoDaMensagem, setTextoDaMensagem] = useState('');
  const [session, setSession] = useState<SessaoDeSimulacaoDto | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [loadingSession, setLoadingSession] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [finishingSession, setFinishingSession] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.ping();
        setApiStatus('online');
      } catch {
        setApiStatus('offline');
      }
    };

    void checkBackend();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sendingMessage]);

  const useScenario = (scenario: ScenarioTemplate) => {
    setCasoId(scenario.casoId);
    setScenarioName(scenario.name);
    setSession(null);
    setMessages([
      makeSystemMessage(
        `Cenário "${scenario.name}" preparado. Escreve a tua primeira pergunta para iniciar uma nova conversa.`
      )
    ]);
    setTextoDaMensagem('');
    setSidebarOpen(false);
    setErrorMessage(null);
  };

  const ensureSession = async () => {
    if (session && session.estado !== 3) {
      return session;
    }

    const body: IniciarSessaoRequestDto = {
      casoId
    };

    setLoadingSession(true);

    try {
      const response = await api.iniciarSessao(body);
      setSession(response.sessao);
      return response.sessao;
    } finally {
      setLoadingSession(false);
    }
  };

  const handleSendMessage = async () => {
    if (!textoDaMensagem.trim() || sendingMessage || finishingSession) {
      return;
    }

    const trimmed = textoDaMensagem.trim();
    setErrorMessage(null);
    setSendingMessage(true);

    try {
      const activeSession = await ensureSession();
      const response = await api.enviarMensagem(activeSession.id, trimmed);
      const responseMessages = makeMessageFromResponse(response);
      const updatedSession = await api.obterSessao(activeSession.id);

      setSession(updatedSession);
      setMessages((currentMessages) => {
        const filteredMessages = currentMessages.filter((message) => message.id !== response.mensagemProfissional.id && message.id !== response.respostaIa?.id);
        return [...filteredMessages, ...responseMessages];
      });
      setTextoDaMensagem('');
    } catch (error) {
      setErrorMessage(normalizeError(error));
    } finally {
      setSendingMessage(false);
    }
  };

  const handleFinishSession = async () => {
    if (!session || session.estado === 3 || finishingSession || sendingMessage) {
      return;
    }

    setErrorMessage(null);
    setFinishingSession(true);

    try {
      const finalizada = await api.concluirSessao(session.id);
      setSession(finalizada);
      setMessages(mapSessionMessages(finalizada));
    } catch (error) {
      setErrorMessage(normalizeError(error));
    } finally {
      setFinishingSession(false);
    }
  };

  return (
    <div className="app-shell app-shell--focus">
      <div className="orb orb--a" />
      <div className="orb orb--b" />
      <div className="orb orb--c" />

      <button
        type="button"
        className="drawer-toggle"
        onClick={() => setSidebarOpen(true)}
        aria-label="Abrir cenários rápidos"
      >
        Cenários
      </button>

      {sidebarOpen && <button type="button" className="drawer-backdrop" onClick={() => setSidebarOpen(false)} aria-label="Fechar menu" />}

      <aside className={`scenario-drawer ${sidebarOpen ? 'scenario-drawer--open' : ''}`} aria-label="Cenários rápidos">
        <div className="scenario-drawer__header">
          <p className="section-label">Cenários rápidos</p>
          <button type="button" className="drawer-close" onClick={() => setSidebarOpen(false)}>
            Fechar
          </button>
        </div>
        <div className="scenario-list">
          {SCENARIOS.map((scenario) => (
            <button key={scenario.name} className="scenario-card" onClick={() => useScenario(scenario)}>
              <strong>{scenario.name}</strong>
              <span>{scenario.description}</span>
            </button>
          ))}
        </div>
      </aside>

      <main className="main-stack">
        <section className="panel chat-panel chat-panel--focus">
          <div className="chat-topbar">
            <div>
              <p className="section-label">Conversa</p>
              <h2>Simulação clínica</h2>
            </div>
            <div className="chat-topbar__meta">
              <span className={`status-dot status-dot--${apiStatus}`} />
              <span className="pill">{apiStatus === 'online' ? 'Backend online' : apiStatus === 'offline' ? 'Backend offline' : 'A validar'}</span>
              <span className="pill">{scenarioName}</span>
              <span className="pill">{session ? ESTADO_LABELS[session.estado] ?? `Estado ${session.estado}` : 'Pronto para iniciar'}</span>
            </div>
          </div>

          <div className="chat-feed" aria-live="polite">
            {messages.map((message) => (
              <article key={message.id} className={`message-card message-card--${message.role}`}>
                <div className="message-card__meta">
                  <strong>
                    {message.role === 'system' ? 'Sistema' : message.role === 'profissional' ? 'Utilizador' : 'IA'}
                  </strong>
                  <span>{formatDate(message.timestamp)}</span>
                </div>
                <p>{message.text}</p>
              </article>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="composer">
            <textarea
              value={textoDaMensagem}
              onChange={(event) => setTextoDaMensagem(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void handleSendMessage();
                }
              }}
              placeholder={session?.estado === 3 ? 'Sessão concluída. Escolhe um cenário e envia nova mensagem para reiniciar.' : 'Escreve a próxima pergunta clínica...'}
              disabled={sendingMessage || finishingSession}
              rows={4}
            />
            <div className="composer-actions">
              <button className="primary-button" onClick={handleSendMessage} disabled={sendingMessage || finishingSession || !textoDaMensagem.trim()}>
                {sendingMessage || loadingSession ? 'A enviar...' : 'Enviar mensagem'}
              </button>
              <button
                className="secondary-button"
                onClick={handleFinishSession}
                disabled={!session || session.estado === 3 || finishingSession || sendingMessage}
              >
                {finishingSession ? 'A concluir...' : session?.estado === 3 ? 'Sessão concluída' : 'Concluir e gerar feedback'}
              </button>
            </div>
          </div>

          {errorMessage && <div className="error-banner">{errorMessage}</div>}

          {session?.avaliacao && (
            <section className="feedback-panel" aria-label="Feedback da sessão">
              <div className="feedback-panel__header">
                <p className="section-label">Feedback</p>
                <span className="pill">Sessão concluída</span>
              </div>
              <div className="feedback-grid">
                <article className="feedback-card">
                  <span>Rigor científico</span>
                  <strong>{FEEDBACK_PLACEHOLDER}</strong>
                </article>
                <article className="feedback-card">
                  <span>Coerência de sintomas</span>
                  <strong>{FEEDBACK_PLACEHOLDER}</strong>
                </article>
                <article className="feedback-card">
                  <span>Grau de realismo</span>
                  <strong>{FEEDBACK_PLACEHOLDER}</strong>
                </article>
                <article className="feedback-card">
                  <span>Mais-valia pedagógica</span>
                  <strong>{FEEDBACK_PLACEHOLDER}</strong>
                </article>
              </div>
            </section>
          )}
        </section>
      </main>
    </div>
  );
}