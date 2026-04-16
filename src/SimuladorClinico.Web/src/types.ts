export type EstadoSessaoDeSimulacao = 1 | 2 | 3 | 4;
export type RemetenteInteracao = 1 | 2;

export interface IniciarSessaoRequestDto {
  casoId: string;
}

export interface ProcessarNovaMensagemRequestDto {
  textoDaMensagem: string;
}

export interface InteracaoChatDto {
  id: string;
  remetente: RemetenteInteracao;
  textoDaMensagem: string;
  timestamp: string;
}

export interface AvaliacaoDto {
  id: string;
  rigorCientifico: number;
  coerenciaSintomas: number;
  grauDeRealismo: number;
  maisValiaPedagogica: number;
}

export interface SessaoDeSimulacaoDto {
  id: string;
  dataInicio: string;
  dataFim: string | null;
  estado: EstadoSessaoDeSimulacao;
  casoId: string;
  interacoes: InteracaoChatDto[];
  avaliacao: AvaliacaoDto | null;
}

export interface IniciarSessaoResponseDto {
  sessao: SessaoDeSimulacaoDto;
}

export interface ProcessarNovaMensagemResponseDto {
  sessaoId: string;
  mensagemProfissional: InteracaoChatDto;
  respostaIa: InteracaoChatDto | null;
}