# 🧠 Mental Health Data Integration Guide

## ✅ Implementado

A AI agora:

1. **Carrega dados de `mental_health_data.py`** em vez de ficheiros `.md` individuais
2. **Escolhe aleatoriamente um ID de case** em cada nova sessão de treino
3. **Extrai metadata automaticamente** (Nome, Idade, Género, Profissão, Queixa, Tipo de Caso)
4. **Loga detalhadamente** na consola qual caso foi escolhido
5. **Retorna informação completa** via API sobre o paciente simulado

## 👥 Estrutura dos Dados

Cada caso clínico tem os seguintes campos:

```python
{
    'ID': 1,
    'Name': 'Ana',
    'Age': 28,
    'Gender': 'female',
    'Profession / Occupation': 'project manager',
    'Current Complains': 'constant worry, difficulty sleeping...',
    'Duration of the complaints (months)': 8,
    'Nature of complaints': 'worries focus primarily on work performance...',
    'Descripton of the case': 'Ana, 28, project manager. For the past...',
    'More clinical information': 'Worries focus primarily on work...',
    'Sleep Hygiene': 'non-restorative, with difficulty falling asleep',
    'Nutrition Habits': '3 a 4 cups of coffe a day',
    'Regular Physical Activity': 'no',
    'Current medication': 'no',
    'Current or past therapy': 'no',
    'Family history': 'anxiety',
    'Type': 'promotion',
    'Expectable Healthcare Base Plan': 'HEALTHCARE PLAN --- ...',
}
```

## 🚀 Como Usar

### Opção 1: Script de Teste Local
```bash
cd python
python test_roleplay.py
```

**Output esperado na consola:**
```
======================================================================
🔵 ROLEPLAY SESSION INITIATED
======================================================================
Session ID: teste-001
Case ID: 1
👤 Patient Name: Ana
📅 Age: 28
⚧ Gender: female
💼 Profession: project manager
⏱️  Duration: 8 months
🏥 Chief Complaint: constant worry, difficulty sleeping, muscle...
📋 Case Type: promotion
======================================================================
```

### Opção 2: Via API REST

**Iniciar um novo roleplay (escolhe ID aleatório):**
```bash
curl -X POST "http://localhost:5555/api/ai/session/minha-sessao/start-roleplay"
```

**Resposta:**
```json
{
  "status": "assigned",
  "sessao_id": "minha-sessao",
  "case_id": 1,
  "name": "Ana",
  "age": 28,
  "gender": "female",
  "profession": "project manager",
  "complaint": "constant worry, difficulty sleeping...",
  "case_type": "promotion",
  "duration_months": 8,
  "case_data": { ... }  // Todos os dados do caso
}
```

**Gerar resposta (usa automaticamente o caso escolhido):**
```bash
curl -X POST "http://localhost:5555/api/ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "sessao_id": "minha-sessao",
    "user_message": "Qual é o motivo da sua consulta?"
  }'
```

O AI responderá como o paciente Ana com os seus sintomas específicos!

## 📊 O Que Mudou

### Antes (ficheiros .md)
```
❌ Múltiplos ficheiros .md dispersos
❌ Parsing de texto necessário
❌ Sem estrutura garantida
❌ Difícil manter dados consistentes
```

### Agora (mental_health_data.py)
```
✅ Dados centralizados em 1 ficheiro Python
✅ Estrutura de dicionários (sem parsing!)
✅ Tipagem e validação possível
✅ Fácil de versionar e manter
✅ Meta dados extraídos automaticamente
```

## 📈 Como Adicionar Mais Casos

1. Abre `docs/knowledge/mental_health_data.py`
2. Acha o fim da lista de `mental_health_data`
3. Adiciona um novo dicionário com os mesmos campos:

```python
{
    'ID': 41,  # Novo ID (incremental)
    'Name': 'Novo Paciente',
    'Age': 35,
    'Gender': 'male',
    'Profession / Occupation': 'Engineer',
    'Current Complains': 'Descrição do que se queixa...',
    'Duration of the complaints (months)': 3,
    # ... resto dos campos
}
```

4. Reinicia o serviço Python
5. O novo caso entra automaticamente no pool de seleção!

## 🔍 Verificar Quantos Casos Estão Carregados

**Na consola Python:**
```python
from doc.knowledge.mental_health_data import mental_health_data
print(f"Total de casos: {len(mental_health_data)}")
print(f"IDs disponíveis: {[case['ID'] for case in mental_health_data]}")
```

**Via API:**
```bash
curl "http://localhost:5555/api/ai/knowledge/load"
```

Mostrará:
```json
{
  "status": "loaded",
  "cases_loaded": 40,
  "case_ids": [1, 2, 3, ..., 40],
  "source": "mental_health_data.py"
}
```

## 💡 Comportamento de Roleplay

```
[1] Frontend/Cliente faz requisição
      ↓
[2] Backend recebe: POST /api/ai/session/{id}/start-roleplay
      ↓
[3] AI escolhe ID aleatório e loga na consola
      ↓
[4] API retorna metadata completo do caso
      ↓
[5] Próximas  gerações de resposta usam esse caso específico
      ↓
[6] Ao fazer refresh, novo caso é escolhido aleatoriamente
```

## 🎮 Exemplo Prático Completo

**Em Python, simular um treino:**

```python
import asyncio
from ai_service import AIService

async def simular_consultorio():
    ai = AIService()
    await ai.initialize()
    
    # Iniciar novo treino com caso aleatório
    sessao = "meu-treino-001"
    inicio = await ai.start_roleplay_session(sessao)
    print(f"🧑‍⚕️ Treinando com: {inicio['name']}, {inicio['age']}a, {inicio['profession']}")
    
    # Conversar com o "paciente"
    respostas = [
        "Olá, qual é o motivo da sua consulta?",
        "Há quanto tempo tem estes sintomas?",
        "Como é que isto afeta o seu dia a dia?",
    ]
    
    for pergunta in respostas:
        resp = await ai.generate_response(sessao, pergunta)
        print(f"\n👨‍⚕️ Médico: {pergunta}")
        print(f"🧑 Paciente: {resp['response']}")
        
asyncio.run(simular_consultorio())
```

## 📞 Troubleshooting

**Problema:** Recebo erro "No clinical cases loaded"
- **Solução:** Certifica-te que `mental_health_data.py` existe em `docs/knowledge/`
- Verifica que a lista `mental_health_data` não está vazia

**Problema:** Sempre fico com o mesmo caso
- **Solução:** Normal se houver poucos casos (< 5)
- Adiciona mais casos em `mental_health_data.py`

**Problema:** Resposta não corresponde aos dados do caso
- **Solução:** Certifique-se de chamar `start-roleplay` ANTES de gerar resposta
- Ou passa `force_new_persona: true` em `/api/ai/generate`

---

**Status:** ✅ **Totalmente Integrado e Funcional!**

Agora cada treino clínico tem dados reais e estruturados, e cada sessão simula um paciente específico.

