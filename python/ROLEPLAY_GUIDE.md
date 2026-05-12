# 🎯 Roleplay Session Implementation - Quick Start Guide

## ✅ Implementado

A AI agora:

1. **Escolhe aleatoriamente um `.md` da pasta `knowledge`** em cada nova sessão de treino
2. **Extrai metadata** do documento clínico (Nome do Paciente, Idade, Género, Queixa Atual)
3. **Loga detalhadamente** na consola qual ficheiro foi escolhido
4. **Retorna informação completa** sobre o caso clínico via API

## 🚀 Como Testar

### Opção 1: Script de Teste Local
```bash
cd python
python test_roleplay.py
```

Verás na consola:
```
======================================================================
🔵 ROLEPLAY SESSION INITIATED
======================================================================
Session ID: teste-001
Clinical Case File: register_5.md
Full Path: C:\...\docs\knowledge\register_5.md
👤 Patient Name: João Silva
📅 Age: 45
⚧ Gender: Male
🏥 Chief Complaint: Dor persistente no peito há 2 semanas
======================================================================
```

### Opção 2: Via API REST

**Iniciar um novo roleplay:**
```bash
curl -X POST "http://localhost:5555/api/ai/session/minha-sessao/start-roleplay"
```

**Resposta:**
```json
{
  "status": "assigned",
  "sessao_id": "minha-sessao",
  "source": "C:\\...\\register_5.md",
  "file_name": "register_5.md",
  "case_metadata": {
    "name": "João Silva",
    "age": "45",
    "gender": "Male",
    "complaint": "Dor persistente no peito há 2 semanas"
  },
  "persona_preview": "..."
}
```

**Gerar resposta (usa automaticamente o caso escolhido):**
```bash
curl -X POST "http://localhost:5555/api/ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "sessao_id": "minha-sessao",
    "user_message": "Olá, qual é o motivo da consulta?",
    "max_tokens": 160
  }'
```

## 📊 O Que Mudou

### Antes
```
❌ Resposta genérica sem contexto do .md específico
❌ Sem logging do ficheiro escolhido
❌ Sem metadata disponível
```

### Agora
```
✅ Resposta baseada 100% no conteúdo do .md escolhido
✅ Logging detalhado na consola mostra exatamente qual caso
✅ Metadata completa retornada na API
✅ Cada refresh/nova sessão escolhe um .md diferente aleatoriamente
```

## 🔧 Configuração

O ficheiro `.env` já está configurado corretamente:

```env
KNOWLEDGE_MAX_CHARS=300000     # Permite usar conteúdo completo do .md
KNOWLEDGE_TOP_K=1              # Busca o contexto mais relevante
USE_KNOWLEDGE=true             # Ativa sistema de conhecimento
```

## 📝 Estrutura de um .md Clinical Case

O sistema detecta automaticamente:

```markdown
Name: João Silva
Age: 45
Gender: Male
Profession: Engenheiro
Current Complaint: Dor persistente no peito

[resto do conteúdo do caso clínico...]
```

## 🎮 Fluxo de Uso

1. **Frontend faz refresh** → Nova sessão
2. **Backend recebe requisição** → Chama `start_roleplay_session`
3. **AI escolhe .md aleatoriamente** → Loga na consola qual foi
4. **Gerador de resposta usa esse .md** → Resposta específica do caso
5. **API retorna metadata** → Frontend sabe qual paciente está a simular

## 🐛 Troubleshooting

**Problema:** Não vejo logging na consola
- **Solução:** Certifica-te que `ENVIRONMENT=development` em `.env`
- Reinicia o serviço Python

**Problema:** Resposta ainda genérica
- **Solução:** Verifica se `KNOWLEDGE_MAX_CHARS` está em 300000
- Certifica-te que os ficheiros `.md` têm conteúdo suficiente (>1KB)

**Problema:** Mesmo .md é escolhido sempre
- **Solução:** Normal se houver poucos ficheiros `.md` na pasta
- Adiciona mais casos clínicos em `docs/knowledge/*.md`

## 📞 Próximos Passos (Opcional)

- [ ] Adicionar filtro por tipo de caso (Type: Promotion/Treatment)
- [ ] Implementar favoritos/casos mais usados
- [ ] Dashboard mostrando distribuição de casos
- [ ] Export de estatísticas por tipo de caso

---

**Status:** ✅ Funcional e pronto para usar!

