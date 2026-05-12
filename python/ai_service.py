# -*- coding: utf-8 -*-
"""
AI Service - direct Ollama orchestration (knowledge-only)
"""

import glob
import math
import logging
import os
import re
import random
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

logger = logging.getLogger(__name__)

# Import knowledge data from Python module
# Load mental_health_data and replace nan (Not Available) with None
mental_health_data = []
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "docs" / "knowledge"))
    # Read the file and replace 'nan' with 'None' before executing
    with open(Path(__file__).parent.parent / "docs" / "knowledge" / "mental_health_data.py", "r") as f:
        content = f.read()
    # Replace standalone 'nan' with 'None' (handles: nan, followed by comma or closing bracket)
    content = content.replace(": nan,", ": None,").replace(": nan\n", ": None\n")
    # Execute in a clean namespace
    namespace = {}
    exec(content, namespace)
    mental_health_data = namespace.get("mental_health_data", [])
    logger.info(f" Loaded {len(mental_health_data)} clinical cases from mental_health_data.py")
except Exception as e:
    logger.warning(f" Could not load mental_health_data: {e}")
    mental_health_data = []


class AIService:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        self.knowledge_path = os.getenv("KNOWLEDGE_PATH", "docs/knowledge")
        self.use_knowledge = os.getenv("USE_KNOWLEDGE", "true").lower() == "true"
        self.knowledge_max_chars = int(os.getenv("KNOWLEDGE_MAX_CHARS", "1200"))
        self.knowledge_top_k = int(os.getenv("KNOWLEDGE_TOP_K", "1"))
        self.persona_file = os.getenv("PERSONA_FILE", "paciente_base.md")
        self.response_cache: Dict[str, Dict] = {}  # Simple cache for responses
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour

        # **NOVO: Sistema de memória de conversa**
        self.conversations: Dict[str, List[Dict]] = {}  # {sessao_id: [{"role": "user/patient", "content": "..."}, ...]}
        self.session_timestamps: Dict[str, datetime] = {}  # {sessao_id: last_message_time}
        self.max_conversation_age = int(os.getenv("MAX_CONVERSATION_AGE", "86400"))  # 24 horas
        self.max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))  # Últimas 20 mensagens
        
        # (removido: antigo sistema de doença por sessão)
        # **NOVO: Persona/record atribuída por sessão (roleplay) **
        # Cada sessão pode receber aleatoriamente um dos registos (documents) para roleplay
        self.session_personas: Dict[str, str] = {}  # {sessao_id: persona_text}
        self.session_cases: Dict[str, Dict] = {}  # {sessao_id: case_data from mental_health_data}

        # Store available case IDs from mental_health_data
        self.available_case_ids: List[int] = [case.get("ID") for case in mental_health_data if case.get("ID") is not None]
        if self.available_case_ids:
            logger.info(f" Available case IDs from mental_health_data.py: {sorted(self.available_case_ids)}")

        self.system_prompt = os.getenv(
            "SYSTEM_PROMPT",
            "Responda apenas com base na PERSONA e nos documentos carregados. "
            "Fale sempre como UM ÚNICO PACIENTE em primeira pessoa. "
            "Nunca diga que é médico, nunca dê aconselhamento clínico, e nunca mencione fontes externas. "
            "Se a informação não existir, diga que não sabe com base nos documentos."
        )
        self.fallback_persona = (
            "Você é um único paciente de simulação clínica. "
            "Fale em primeira pessoa, com respostas curtas e naturais. "
            "Use apenas as informações fornecidas em PERSONA e KNOWLEDGE. "
            "Nunca fale como médico, nunca dê conselhos clínicos e nunca faça disclaimers. "
            "Se algo não estiver nos documentos, diga: 'Não sei com base nos documentos carregados.'"
        )
        self.persona_text = self.fallback_persona
        self.base_dir = Path(__file__).resolve().parent
        self.doctor_like_phrases = [
            "não sou um médico",
            "nao sou um medico",
            "não posso confirmar",
            "nao posso confirmar",
            "consulte um médico",
            "consulte um medico",
            "devemos consultar",
            "deve consultar",
            "consultar imediatamente",
            "procurar atendimento",
            "recomendo",
            "diagnóstico",
            "diagnostico",
            "tratamento",
        ]

    async def initialize(self):
        """Initialize AI Service."""
        await self.check_ollama_health()
        if self.use_knowledge:
            await self.load_knowledge_base()

    async def shutdown(self):
        """Clean up resources."""
        logger.info("AI Service shutting down")

    def _cleanup_old_sessions(self):
        """Remove old conversation sessions older than MAX_CONVERSATION_AGE."""
        now = datetime.now()
        expired_sessions = []
        
        for sessao_id, timestamp in self.session_timestamps.items():
            if (now - timestamp).total_seconds() > self.max_conversation_age:
                expired_sessions.append(sessao_id)
        
        for sessao_id in expired_sessions:
            del self.conversations[sessao_id]
            del self.session_timestamps[sessao_id]
            if sessao_id in self.session_personas:
                del self.session_personas[sessao_id]
            if sessao_id in self.session_cases:
                del self.session_cases[sessao_id]
            logger.info(f"Cleaned up old conversation session: {sessao_id}")
    
    # (removido: antigo sistema de doença por sessão) - roleplay agora usa apenas documentos .md

    def _case_value(self, case_data: Dict, *keys: str, default: str = "Não informado") -> str:
        """Return the first non-empty field value found for the provided keys."""
        for key in keys:
            value = case_data.get(key)
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                continue
            text = str(value).strip()
            if text and text.lower() != "nan":
                return text
        return default

    def _build_case_persona_prompt(self, case_data: Dict) -> str:
        """Build the strict system prompt for a single isolated clinical case."""
        name = self._case_value(case_data, 'Name', 'Nome')
        history_part = " e ".join(
            part for part in [
                self._case_value(case_data, "Description of the case", "Descripton of the case", default=""),
                self._case_value(case_data, "More clinical information", default=""),
            ]
            if part and part != "Não informado"
        )
        if not history_part:
            history_part = "Não informado"

        duration = self._case_value(
            case_data,
            "Duration of the complaints (months)",
            "Duration of complaints (months)",
            "Duration",
            default=""
        )

        duration_line = f"Duração das queixas: {duration} meses." if duration else "Duração das queixas: Não informado."

        return "\n".join([
            f"Você é {name}, um paciente real. O seu único objetivo é agir e responder EXATAMENTE como a pessoa descrita abaixo.",
            "",
            "### O SEU PERFIL (PERSONA):",
            f"Nome: {name}",
            f"Idade: {self._case_value(case_data, 'Age', 'Idade')}",
            f"Profissão: {self._case_value(case_data, 'Profession / Occupation', 'Profession', 'Profissão', 'Occupation')}",
            f"Situação Familiar/Histórico: {self._case_value(case_data, 'Family history', 'Family History', 'História familiar', 'Family')}",
            "",
            "### O SEU ESTADO CLÍNICO:",
            f"Queixas Atuais: {self._case_value(case_data, 'Current Complains', 'Current Complaints', 'Queixas atuais')}",
            f"História da Doença Atual (Como começou): {history_part}",
            duration_line,
            f"Padrão de Sono: {self._case_value(case_data, 'Sleep Hygiene', 'Sleep hygiene')}",
            f"Hábitos e Nutrição: {self._case_value(case_data, 'Nutrition Habits', 'Eating Habits', 'Habits and nutrition')}",
            f"Atividade Física: {self._case_value(case_data, 'Regular Physical Activity', 'Physical Activity')}",
            "",
            "### REGRAS OBRIGATÓRIAS (PUNIÇÃO EM CASO DE FALHA):",
            "1. VOCÊ É O PACIENTE. Responda SEMPRE na primeira pessoa do singular (\"Eu sinto...\", \"Eu tenho...\").",
            "2. NUNCA revele que é uma Inteligência Artificial, simulador, assistente, modelo, base de dados ou ficheiro.",
            "3. NUNCA INVENTE SINTOMAS, NOMES OU HISTÓRIAS que não estejam no seu perfil acima.",
            "4. Se o médico (utilizador) perguntar sobre um sintoma que NÃO está na sua lista de queixas, você DEVE dizer que NÃO tem isso.",
            "5. Seja natural, humano e direto. Não vomite toda a informação de uma vez. Responda apenas ao que lhe foi perguntado.",
            "6. Não tente ser prestativo nem resolver o problema. O médico é quem tem de descobrir o que você tem através de perguntas.",
            "7. NUNCA mencione base de dados, ficheiros, JSON, backend, outros pacientes, histórias alternativas ou qualquer coisa fora deste perfil.",
            "8. Se algo não estiver no seu perfil acima, diga apenas que não sabe ou que não tem essa informação.",
            "9. Se o nome ou o motivo da consulta não existirem no caso, nunca invente: diga que não sabe.",
        ])

    def _build_case_chat_messages(self, sessao_id: str, user_message: str) -> List[Dict[str, str]]:
        """Build Ollama chat messages for the session using only the assigned case."""
        case_data = self.session_cases.get(sessao_id)
        if not case_data:
            return []

        messages: List[Dict[str, str]] = [{
            "role": "system",
            "content": self._build_case_persona_prompt(case_data),
        }]

        for msg in self.conversations.get(sessao_id, []):
            messages.append({
                "role": "assistant" if msg["role"] == "patient" else "user",
                "content": msg["content"],
            })

        messages.append({"role": "user", "content": user_message})
        return messages

    async def start_roleplay_session(self, sessao_id: str, force_new: bool = False) -> Dict:
        """Atribui aleatoriamente um único case da mental_health_data como persona para uma sessão.

        Deve ser chamado antes de iniciar um treino/roleplay. Retorna informações sobre o case escolhido.
        """
        if not force_new and sessao_id in self.session_cases and self.session_cases[sessao_id]:
            case_data = self.session_cases[sessao_id]
            case_id = case_data.get("ID")
            logger.info(f" Reusing existing clinical case for session {sessao_id}: Case ID {case_id}")
            return {
                "status": "assigned",
                "sessao_id": sessao_id,
                "case_id": case_id,
                "name": case_data.get("Name", ""),
                "age": case_data.get("Age", ""),
                "gender": case_data.get("Gender", ""),
                "profession": case_data.get("Profession / Occupation", ""),
                "complaint": case_data.get("Current Complains", "") or case_data.get("Nature of complaints", ""),
                "case_type": case_data.get("Type", "N/A"),
                "duration_months": case_data.get("Duration of the complaints (months)", None),
                "case_data": case_data,
                "reused": True,
            }

        if not mental_health_data:
            logger.warning("Nenhum case disponível em mental_health_data; não é possível iniciar roleplay")
            return {"status": "error", "message": "No clinical cases loaded"}

        # Choose one random case object and ignore the rest of the dataset
        random_index = random.randrange(len(mental_health_data))
        case_data = dict(mental_health_data[random_index])
        case_id = case_data.get("ID")

        # Store case data for this session
        self.session_cases[sessao_id] = case_data

        # Create persona text from case data
        name = self._case_value(case_data, "Name", "Nome")
        age = self._case_value(case_data, "Age", "Idade")
        gender = self._case_value(case_data, "Gender", "Sexo")
        complaint = self._case_value(case_data, "Current Complains", "Current Complaints", "Queixas atuais")
        profession = self._case_value(case_data, "Profession / Occupation", "Profession", "Profissão", "Occupation")
        duration_value = self._case_value(case_data, "Duration of the complaints (months)", "Duration of complaints (months)", "Duration", default="")

        persona_text = self._build_case_persona_prompt(case_data)
        self.session_personas[sessao_id] = persona_text

        # **LOG DETALHADO PARA CONSOLA**
        logger.info("=" * 70)
        logger.info(f" ROLEPLAY SESSION INITIATED")
        logger.info("=" * 70)
        logger.info(f"Session ID: {sessao_id}")
        logger.info(f"Selected list index: {random_index}")
        logger.info(f"Case ID: {case_id}")
        active_patient_message = f" SYSTEM ASSUMING PATIENT ID: {case_id} | Session: {sessao_id}"
        logger.warning(active_patient_message)
        print(active_patient_message, flush=True)
        logger.info(f" Active case being simulated now: ID {case_id}")
        logger.info(f" Patient Name: {name}")
        logger.info(f" Age: {age}")
        logger.info(f" Gender: {gender}")
        logger.info(f" Profession: {profession}")
        logger.info(f"  Duration: {duration_value or 'N/A'} months")
        logger.info(f" Chief Complaint: {complaint[:100]}...")
        logger.info(f" Case Type: {case_data.get('Type', 'N/A')}")
        logger.info("=" * 70)

        return {
            "status": "assigned",
            "sessao_id": sessao_id,
            "selected_index": random_index,
            "case_id": case_id,
            "name": name,
            "age": age,
            "gender": gender,
            "profession": profession,
            "complaint": complaint,
            "case_type": case_data.get("Type", "N/A"),
            "duration_months": case_data.get("Duration of the complaints (months)", None),
            "case_data": case_data  # Return full case data
        }

    def get_session_persona(self, sessao_id: str) -> Dict:
        """Retorna a persona/registo atribuída a uma sessão (se existir)."""
        if sessao_id not in self.session_personas:
            return {"sessao_id": sessao_id, "persona_assigned": False}
        case_data = self.session_cases.get(sessao_id, {})
        return {
            "sessao_id": sessao_id,
            "persona_assigned": True,
            "persona": self.session_personas[sessao_id],
            "case_id": case_data.get("ID"),
        }

    def _get_session_case(self, sessao_id: str) -> Optional[Dict]:
        """Return the clinical case assigned to the session, if any."""
        return self.session_cases.get(sessao_id)

    def _normalize_text(self, text: str) -> str:
        """Lowercase, remove accents and collapse whitespace for robust matching."""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = " ".join(normalized.lower().split())
        return normalized

    def _contains_any(self, text: str, phrases: List[str]) -> bool:
        normalized_text = self._normalize_text(text)
        return any(self._normalize_text(phrase) in normalized_text for phrase in phrases)

    def _normalized_words(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", self._normalize_text(text))

    def _detect_message_language(self, text: str) -> str:
        """Detect whether the user is writing in Portuguese or English.

        Returns:
            'pt' for Portuguese (default) or 'en' for English.
        """
        normalized = self._normalize_text(text or "")
        words = set(self._normalized_words(text or ""))

        pt_score = 0
        en_score = 0

        # Strong Portuguese signals: presence of non-ASCII characters is a good indicator
        if any(ord(ch) > 127 for ch in (text or "")):
            pt_score += 3

        # Common short phrases and stopwords
        portuguese_signals = [
            "ola", "bom dia", "boa tarde", "boa noite", "como estas", "como te chamas",
            "qual e", "qual é", "nao", "não", "tenho", "estou", "podes", "pode", "sinto",
            "motivo da consulta", "higiene do sono", "historial", "historial familiar",
            "profissao", "profissão", "medicacao", "medicação", "falta de ar", "dor no peito",
        ]
        english_signals = [
            "hello", "hi", "how are you", "what is", "what's", "your name", "do you have",
            "i have", "i am", "my name", "reason for the consultation", "sleep hygiene",
            "family history", "medication", "shortness of breath", "chest pain", "occupation",
        ]

        for phrase in portuguese_signals:
            if phrase in normalized:
                pt_score += 2
        for phrase in english_signals:
            if phrase in normalized:
                en_score += 2

        portuguese_words = {
            "como", "que", "qual", "quais", "porque", "porque", "quando", "onde", "estás", "estas",
            "estou", "tenho", "não", "nao", "sim", "motivo", "consulta", "idos", "anos", "dor",
            "sono", "família", "familia", "medicação", "medicacao", "higiene", "profissão", "profissao",
        }
        english_words = {
            "how", "what", "which", "why", "when", "where", "are", "am", "have", "do", "does",
            "hello", "hi", "reason", "consultation", "sleep", "family", "history", "medication",
            "occupation", "name", "pain", "patient", "today",
        }

        pt_score += sum(1 for word in words if word in portuguese_words)
        en_score += sum(1 for word in words if word in english_words)

        if en_score > pt_score:
            return "en"
        return "pt"

    def _localize_response(self, text: str, target_language: str) -> str:
        """Best-effort deterministic localization for short patient replies.

        This is intentionally glossary-based so the response still works even if
        the translation model is unavailable or returns a mixed-language answer.
        """
        if not text or target_language not in {"pt", "en"}:
            return text

        replacements = {
            "pt": [
                ("intrusive and persistent thoughts about contamination and germs", "pensamentos intrusivos e persistentes sobre contaminação e germes"),
                ("intrusive and persistent thoughts", "pensamentos intrusivos e persistentes"),
                ("intrusive thoughts", "pensamentos intrusivos"),
                ("persistent thoughts", "pensamentos persistentes"),
                ("contamination and germs", "contaminação e germes"),
                ("contamination", "contaminação"),
                ("germs", "germes"),
                ("demotivated at work", "desmotivado no trabalho"),
                ("frustrated", "frustrado"),
                ("ineffective", "ineficaz"),
                ("his energy is low", "a energia está baixa"),
                ("her energy is low", "a energia está baixa"),
                ("energy is low", "a energia está baixa"),
                ("and he isolates himself from friends", "e isola-se dos amigos"),
                ("he isolates himself from friends", "isola-se dos amigos"),
                ("she isolates herself from friends", "isola-se dos amigos"),
                ("chronically procrastinates", "procrastino cronicamente"),
                ("having great difficulty starting tasks and maintaining focus on long projects", "tenho grande dificuldade em iniciar tarefas e manter o foco em projetos longos"),
                ("great difficulty starting tasks and maintaining focus on long projects", "grande dificuldade em iniciar tarefas e em manter o foco em projetos longos"),
                ("great difficulty starting tasks", "grande dificuldade em iniciar tarefas"),
                ("maintaining focus", "manter o foco"),
                ("long projects", "projetos longos"),
                ("lack of purpose", "falta de propósito"),
                ("feels exhausted", "sente-se exausto"),
                ("feeling exhausted", "sentindo-se exausto"),
                ("low energy", "baixa energia"),
                ("low mood", "humor em baixo"),
                ("difficulty sleeping", "dificuldade em dormir"),
                ("fragmented sleep", "sono fragmentado"),
                ("wakes up several times during the night", "acorda várias vezes durante a noite"),
                ("shortness of breath", "falta de ar"),
                ("chest pain", "dor no peito"),
                ("family history", "historial familiar"),
                ("sleep hygiene", "higiene do sono"),
                ("eating habits", "hábitos alimentares"),
                ("physical activity", "atividade física"),
                ("regular physical activity", "atividade física regular"),
                ("no medication", "sem medicação"),
                ("no therapy", "sem terapia"),
                ("teacher", "professor"),
                ("nurse", "enfermeiro"),
                ("student", "estudante"),
                ("doctor", "médico"),
                ("anxiety", "ansiedade"),
                ("depression", "depressão"),
                ("stress", "stress"),
                ("fatigue", "fadiga"),
                ("irritability", "irritabilidade"),
                ("social isolation", "isolamento social"),
                ("alcohol use", "consumo de álcool"),
                ("weight gain", "aumento de peso"),
                ("loss of appetite", "perda de apetite"),
                ("poor appetite", "apetite fraco"),
                ("Estou aqui por ", "Estou aqui porque "),
            ],
            "en": [
                ("Chamo-me ", "My name is "),
                ("Estou aqui por ", "I'm here because "),
                ("Tenho ", "I am "),
                ("Sou ", "I am "),
                ("A minha higiene de sono é ", "My sleep hygiene is "),
                ("Os meus hábitos alimentares são ", "My eating habits are "),
                ("A minha atividade física regular é ", "My regular physical activity is "),
                ("O meu historial familiar é ", "My family history is "),
                ("Não tomo medicação.", "I do not take medication."),
                ("Não fiz terapia anterior.", "I have not had previous therapy."),
                ("O meu ID é ", "My ID is "),
                ("O tipo do caso é ", "The case type is "),
                ("Isto já dura há ", "This has been going on for "),
                ("Não sei com base nos dados deste caso.", "I do not know based on the data from this case."),
            ],
        }

        localized = text
        for source, target in sorted(replacements[target_language], key=lambda item: len(item[0]), reverse=True):
            localized = re.sub(re.escape(source), target, localized, flags=re.IGNORECASE)

        return localized

    def _needs_translation(self, text: str, target_language: str) -> bool:
        """Heuristic to decide whether LLM translation is needed."""
        if not text or target_language not in {"pt", "en"}:
            return False

        normalized = self._normalize_text(text)
        words = set(re.findall(r"\b[a-zA-Z']+\b", normalized))

        english_markers = {
            "and", "the", "with", "about", "thoughts", "persistent", "intrusive", "contamination",
            "germs", "work", "frustrated", "ineffective", "energy", "isolates", "friends"
        }
        portuguese_markers = {
            "e", "com", "sobre", "pensamentos", "persistentes", "intrusivos", "contaminacao",
            "germes", "trabalho", "frustrado", "ineficaz", "energia", "amigos", "porque", "estou"
        }

        if target_language == "pt":
            return any(w in words for w in english_markers)
        return any(w in words for w in portuguese_markers)

    async def _translate_to_user_language(self, text: str, target_language: str) -> str:
        """Hybrid finalization: deterministic localization + LLM translation when needed."""
        if not text or target_language not in {"pt", "en"}:
            return text

        localized = self._localize_response(text, target_language)
        if not self._needs_translation(localized, target_language):
            return localized

        translated = await self._translate_response(localized, target_language)
        if translated:
            return translated
        return localized

    async def _translate_response(self, text: str, target_language: str) -> str:
        """Translate a final response to the user's language.

        The clinical meaning must stay unchanged and no new information should be added.
        If translation fails, the original text is returned.
        """
        if not text or target_language not in {"pt", "en"}:
            return text

        if target_language == "pt":
            language_instruction = "Portuguese from Portugal (pt-PT)"
        else:
            language_instruction = "English"

        prompt = (
            f"You are a strict medical translator. Translate ALL content into {language_instruction}. "
            f"Preserve exact clinical meaning, first person, tone, and brevity. "
            f"Do not leave mixed language terms when a normal translation exists. "
            f"Do not add explanations, disclaimers, or new medical information. "
            f"Keep IDs, numbers, medication names, and proper nouns unchanged when appropriate. "
            f"Return only the translated text.\n\n"
            f"TEXT:\n{text}\n\n"
            f"TRANSLATION:"
        )

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_k": 5,
                "top_p": 0.2,
                "num_ctx": 768,
                "num_predict": 180,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.ollama_host}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            translated = (data.get("response") or "").strip()
            if translated:
                return translated
        except Exception as exc:
            logger.warning(f"Language translation attempt 1 failed: {exc}")

        # Retry with shorter output/time budget to avoid blocking the request.
        short_payload = {
            **payload,
            "options": {
                **payload["options"],
                "num_predict": 96,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(f"{self.ollama_host}/api/generate", json=short_payload)
                response.raise_for_status()
                data = response.json()
            translated = (data.get("response") or "").strip()
            if translated:
                return translated
        except Exception as exc:
            logger.warning(f"Language translation attempt 2 failed: {exc}")

        return text

    def _log_active_patient(self, sessao_id: str) -> Optional[int]:
        """Log the active patient ID for the given session and return it."""
        case_data = self._get_session_case(sessao_id)
        case_id = case_data.get("ID") if case_data else None
        message = f"[PATIENT] SYSTEM ASSUMING PATIENT ID: {case_id} | Session: {sessao_id}"
        logger.warning(message)
        print(message, flush=True)
        return case_id

    def _looks_like_identity_question(self, text: str) -> bool:
        lowered = self._normalize_text(text)
        triggers = [
            # Name and identity
            "como te chamas", "qual é o teu nome", "qual e o teu nome", "teu nome", "nome tens",
            "what is your name", "whats your name", "your name",
            # Age
            "que idade tens", "qual é a tua idade", "qual e a tua idade", "idade tens",
            "how old are you", "your age",
            # Reason for consultation
            "motivo da consulta", "por que estás aqui", "porque estás aqui", "porque esta aqui",
            "qual o motivo", "motivo", "reason for consultation", "why are you here",
            # Profession
            "profissão", "profissao", "trabalho", "ocupação", "ocupacao",
            "occupation", "profession", "job", "work",
            # Duration / time
            "ha quanto tempo", "quanto tempo", "duração", "duracao", "quando começou", "quando comecou",
            "how long", "how long have you", "since when", "duration",
            # Sleep
            "higiene de sono", "higiene do sono", "sono", "dorm",
            "sleep", "sleep hygiene", "sleep pattern",
            # Nutrition
            "hábitos alimentares", "habitos alimentares", "dieta", "alimentação",
            "eating habits", "nutrition", "diet",
            # Activity
            "atividade física", "atividade fisica", "exercicio", "exercise",
            "physical activity", "exercise", "active",
            # Family
            "família", "familia", "historial", "family history", "family",
            # Medication
            "medicação", "medicacao", "remedio", "remédio", "tomas alguma", "medication", "medicine", "tablets", "pills",
            # Therapy
            "terapia", "terap", "psicolog", "counseling", "therapy", "counselor",
            # Type and ID
            "tipo do caso", "tipo de caso", "case type", "type", "id", "identific", "case id",
            # Description
            "como começou", "como comecou", "descricao do caso", "descrição do caso", "historia", "história",
            "description", "how it started", "what happened",
            # Healthcare plan
            "plano de cuidados", "plano", "cuidados", "healthcare", "plan",
        ]
        return any(self._normalize_text(t) in lowered for t in triggers)

    def _case_text_blob(self, case: Dict) -> str:
        """Build a lowercase text blob with only the selected case content."""
        parts = []
        for key in [
            "Name", "Nome", "Age", "Idade", "Gender", "Sexo", "Profession / Occupation", "Profession", "Profissão", "Occupation",
            "Family history", "Family History", "História familiar", "Family",
            "Current Complains", "Current Complaints", "Queixas atuais",
            "Description of the case", "Descripton of the case", "More clinical information",
            "Sleep Hygiene", "Sleep hygiene", "Nutrition Habits", "Eating Habits", "Regular Physical Activity",
            "Duration of the complaints (months)", "Duration of complaints (months)", "Duration"
        ]:
            value = case.get(key)
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                continue
            text = str(value).strip()
            if text and text.lower() != "nan":
                parts.append(text.lower())
        return " ".join(parts)

    def _response_violates_case(self, sessao_id: str, response_text: str) -> bool:
        """Detect obvious meta/invented responses that are not grounded in the selected case."""
        case = self._get_session_case(sessao_id)
        if not case:
            return True

        response_norm = self._normalize_text(response_text)
        case_norm = self._normalize_text(self._case_text_blob(case))

        forbidden_terms = [
            "paciente realista",
            "nao tenho um nome particular",
            "não tenho um nome particular",
            "simulador",
            "inteligencia artificial",
            "inteligência artificial",
            "modelo",
            "dicas para melhorar",
            "saude mental",
            "saúde mental",
            "base de dados",
            "outras pessoas",
        ]

        if any(self._normalize_text(term) in response_norm for term in forbidden_terms):
            return True

        # If the response introduces a name that is not the selected case name, treat it as a violation.
        case_name = self._normalize_text(str(case.get("Name") or case.get("Nome") or ""))
        if case_name and case_name not in response_norm and any(term in response_norm for term in ["chamo-me", "me chamo", "me chamo"]):
            return True

        # If the response mentions symptoms/terms outside the selected case, be conservative.
        if any(term in response_norm for term in ["ansiedade", "depress", "falta de ar", "dor no peito", "dor nas costas", "febre", "tosse"]):
            if not any(term in case_norm for term in ["ansiedade", "depress", "falta de ar", "dor no peito", "dor nas costas", "febre", "tosse"]):
                return True

        return False

    def _answer_from_case(self, sessao_id: str, user_message: str) -> Optional[str]:
        """Deterministically answer basic identity questions from the assigned case."""
        case = self._get_session_case(sessao_id)
        if not case:
            return None

        text = self._normalize_text(user_message)
        case_blob = self._case_text_blob(case)
        name = self._case_value(case, "Name", "Nome", default="")
        age = self._case_value(case, "Age", "Idade", default="")
        gender = self._case_value(case, "Gender", "Sexo", default="")
        profession = self._case_value(case, "Profession / Occupation", "Profession", "Profissão", "Occupation", default="")
        complaint = self._case_value(case, "Current Complains", "Current Complaints", "Queixas atuais", default="")
        nature = self._case_value(case, "Nature of complaints", default="")
        duration = self._case_value(case, "Duration of the complaints (months)", "Duration of complaints (months)", "Duration", default="")
        sleep_hygiene = self._case_value(case, "Sleep Hygiene", "Sleep hygiene", default="")
        nutrition = self._case_value(case, "Nutrition Habits", "Eating Habits", default="")
        activity = self._case_value(case, "Regular Physical Activity", "Physical Activity", default="")
        family_history = self._case_value(case, "Family history", "Family History", default="")
        current_medication = self._case_value(case, "Current medication", "Current Medication", default="")
        past_therapy = self._case_value(case, "Current or past therapy", "Current or Previous Therapy", "Current or previous therapy", default="")
        case_type = self._case_value(case, "Type", default="")
        case_id = self._case_value(case, "ID", default="")
        description = self._case_value(case, "Descripton of the case", "Description of the case", default="")
        more_info = self._case_value(case, "More clinical information", default="")
        healthcare_plan = self._case_value(case, "Expectable Healthcare Base Plan", default="")

        # If the question is about a symptom not in the selected case, deny it explicitly.
        symptom_triggers = [
            ("dor no peito", ["dor no peito", "chest pain", "peito"]),
            ("febre", ["febre", "fever"]),
            ("tosse", ["tosse", "cough"]),
            ("falta de ar", ["falta de ar", "shortness of breath", "dispneia", "dificuldade em respirar"]),
            ("dor nas costas", ["dor nas costas", "back pain"]),
        ]
        if any(term in text for _, terms in symptom_triggers for term in terms):
            for canonical, terms in symptom_triggers:
                if any(term in text for term in terms):
                    if not any(term in case_blob for term in terms):
                        return f"Não tenho {canonical}."

        requested_name = self._contains_any(text, ["nome", "chamas", "teu nome"])
        requested_reason = self._contains_any(text, ["motivo", "consulta", "aqui"])
        requested_age = self._contains_any(text, ["idade", "anos"])
        requested_profession = self._contains_any(text, ["profiss", "trabalho", "ocup"])
        requested_gender = self._contains_any(text, ["género", "genero", "sexo"])
        requested_sleep = self._contains_any(text, ["higiene de sono", "higiene do sono", "sono", "dorm", "sleep"])
        requested_nutrition = self._contains_any(text, ["alimenta", "nutri", "dieta", "eat"])
        requested_activity = self._contains_any(text, ["atividade fisica", "atividade", "exercicio", "exercise", "fisica"])
        requested_family = self._contains_any(text, ["famil", "historico familiar", "historia familiar"])
        requested_duration = self._contains_any(text, ["ha quanto tempo", "quanto tempo", "duracao", "duracao das queixas", "tempo ha"])
        requested_medication = self._contains_any(text, ["medic", "medicação", "medicacao", "remedio", "remédio", "tomas alguma"])
        requested_therapy = self._contains_any(text, ["terap", "psicolog", "aconselh", "counsel", "tratamento anterior"])
        text_words = set(self._normalized_words(text))
        requested_case_id = "id" in text_words or self._contains_any(text, ["identific", "numero do caso", "número do caso", "codigo do caso", "código do caso"])
        requested_case_type = self._contains_any(text, ["tipo do caso", "tipo de caso", "case type"]) or "tipo" in text_words
        requested_description = (
            self._contains_any(text, ["como começou", "como comecou", "como comeou", "descreve o caso", "descricao do caso", "descrição do caso", "historia do caso", "história do caso", "case description", "description of the case", "inicio do caso", "início do caso"])
            or re.search(r"\bcomo\s+come\w*ou\b", self._normalize_text(text)) is not None
        )
        requested_more_info = self._contains_any(text, ["mais informacoes", "mais informação", "mais informacao", "informacoes clinicas adicionais", "informações clínicas adicionais", "informacao clinica adicional", "informacao clinica", "informação clínica", "more clinical information", "adicionais", "clinicas adicionais"])
        requested_plan = self._contains_any(text, ["plano de cuidados", "plano", "cuidados", "intervenc", "monitor", "follow-up", "follow up", "roadmap"])

        parts = []
        if requested_name:
            if name:
                parts.append(f"Chamo-me {name}.")
            else:
                parts.append("Não sei o meu nome neste caso.")
        if requested_age:
            if age not in (None, ""):
                parts.append(f"Tenho {age} anos.")
            else:
                parts.append("Não sei a minha idade neste caso.")
        if requested_reason:
            if complaint:
                parts.append(f"Estou aqui por {complaint}.")
            else:
                parts.append("Não sei o motivo da consulta.")
        if requested_profession:
            if profession:
                parts.append(f"Sou {profession}.")
            else:
                parts.append("Não sei a minha profissão neste caso.")
        if requested_gender:
            if gender:
                parts.append(f"Sou {gender}.")
            else:
                parts.append("Não sei o meu género neste caso.")
        if requested_sleep:
            if sleep_hygiene:
                parts.append(f"A minha higiene de sono é {sleep_hygiene}.")
            else:
                parts.append("Não sei como é a minha higiene de sono neste caso.")
        if requested_nutrition:
            if nutrition:
                parts.append(f"Os meus hábitos alimentares são {nutrition}.")
            else:
                parts.append("Não sei quais são os meus hábitos alimentares neste caso.")
        if requested_activity:
            if activity:
                parts.append(f"A minha atividade física regular é {activity}.")
            else:
                parts.append("Não sei qual é a minha atividade física neste caso.")
        if requested_family:
            if family_history:
                parts.append(f"O meu historial familiar é {family_history}.")
            else:
                parts.append("Não sei qual é o meu historial familiar neste caso.")
        if requested_medication:
            if current_medication:
                med = current_medication.strip().lower()
                if med in {"no", "não", "nao", "none", "n/a", "na", "false", "0"}:
                    parts.append("Não tomo medicação.")
                else:
                    parts.append(f"Tomo {current_medication}.")
            else:
                parts.append("Não sei qual é a minha medicação neste caso.")
        if requested_therapy:
            if past_therapy:
                therapy = past_therapy.strip().lower()
                if therapy in {"no", "não", "nao", "none", "n/a", "na", "false", "0"}:
                    parts.append("Não fiz terapia anterior.")
                else:
                    parts.append(f"Já fiz {past_therapy}.")
            else:
                parts.append("Não sei qual é a minha terapia anterior neste caso.")
        if requested_duration and duration not in (None, ""):
            parts.append(f"Isto já dura há {duration} meses.")
        if requested_case_id:
            if case_id not in (None, ""):
                parts.append(f"O meu ID é {case_id}.")
            else:
                parts.append("Não sei qual é o meu ID neste caso.")
        if requested_case_type:
            if case_type:
                parts.append(f"O tipo do caso é {case_type}.")
            else:
                parts.append("Não sei qual é o tipo do caso neste caso.")
        if requested_description:
            if description:
                parts.append(description)
            else:
                parts.append("Não sei a descrição do caso neste caso.")
        if requested_more_info:
            if more_info:
                parts.append(more_info)
            else:
                parts.append("Não sei a informação clínica adicional neste caso.")
        if requested_plan:
            if healthcare_plan:
                parts.append(healthcare_plan)
            else:
                parts.append("Não sei qual é o plano de cuidados neste caso.")

        if not parts:
            return None

        response = " ".join(parts)
        logger.info(f" Deterministic answer selected for session {sessao_id}: {response}")
        return response

    def _get_disease_description(self, disease: str) -> str:
        """Retorna uma descrição breve da doença para incluir na persona."""
        descriptions = {
            "asma": "paciente com asma, tenho dificuldade em respirar, especialmente com esforço",
            "diabetes": "paciente com diabetes tipo 2, tenho alteração nos níveis de glicose"
        }
        return descriptions.get(disease, "paciente com uma doença crónica")

    def _add_message_to_history(self, sessao_id: str, role: str, content: str):
        """Add a message to the conversation history for a session."""
        if sessao_id not in self.conversations:
            self.conversations[sessao_id] = []

        self.conversations[sessao_id].append({
            "role": role,  # "user" or "patient"
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # Update session timestamp
        self.session_timestamps[sessao_id] = datetime.now()

        # Keep only last N messages to avoid infinite growth
        if len(self.conversations[sessao_id]) > self.max_history_messages:
            self.conversations[sessao_id] = self.conversations[sessao_id][-self.max_history_messages:]

        logger.debug(f"Added message to session {sessao_id}: {role} - {content[:50]}...")

    def _get_conversation_history(self, sessao_id: str) -> str:
        """Get formatted conversation history for a session."""
        if sessao_id not in self.conversations or not self.conversations[sessao_id]:
            return ""

        history_lines = []
        for msg in self.conversations[sessao_id]:
            role_label = "MÉDICO/ESTUDANTE" if msg["role"] == "user" else "PACIENTE"
            history_lines.append(f"{role_label}: {msg['content']}")

        return "\n".join(history_lines)

    def _get_conversation_summary(self, sessao_id: str) -> str:
        """Get a brief summary of what was said in the conversation so far."""
        if sessao_id not in self.conversations or not self.conversations[sessao_id]:
            return ""

        # Just give the context of recent messages
        recent_messages = self.conversations[sessao_id][-4:]  # Last 4 messages
        summary_lines = []
        for msg in recent_messages:
            summary_lines.append(f"- {msg['content']}")

        if summary_lines:
            return "CONTEXTO DA CONVERSA ANTERIOR:\n" + "\n".join(summary_lines)
        return ""

    async def check_ollama_health(self) -> bool:
        """Check Ollama server health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_host}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def load_knowledge_base(self) -> Dict:
        """Load clinical cases from mental_health_data.py (replaces .md file loading)."""
        try:
            if not mental_health_data:
                logger.warning("No clinical cases found in mental_health_data.py")
                return {"status": "no_data", "cases_loaded": 0}

            # Initialize available case IDs
            self.available_case_ids = [case.get("ID") for case in mental_health_data if case.get("ID") is not None]

            logger.info(f" Knowledge base loaded: {len(mental_health_data)} clinical cases")
            logger.info(f" Case IDs available: {sorted(self.available_case_ids)}")

            return {
                "status": "loaded",
                "cases_loaded": len(mental_health_data),
                "case_ids": sorted(self.available_case_ids),
                "source": "mental_health_data.py"
            }

        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            return {"status": "error", "error": str(e)}


    async def retrieve_relevant_context(self, query: str, sessao_id: str, k: int = 1) -> str:
        """Legacy helper kept for compatibility; now returns only the assigned case context."""
        try:
            # Get case data for this session
            case_data = self.session_cases.get(sessao_id)
            if not case_data:
                return ""

            # Combine relevant fields from case data
            context_parts = []

            # Add main description
            if case_data.get("Descripton of the case"):
                context_parts.append(case_data["Descripton of the case"])

            # Add more clinical information
            if case_data.get("More clinical information"):
                context_parts.append(case_data["More clinical information"])

            # Add healthcare plan (it contains treatment information)
            if case_data.get("Expectable Healthcare Base Plan"):
                context_parts.append(case_data["Expectable Healthcare Base Plan"])

            context = "\n\n".join(context_parts)
            return context[:self.knowledge_max_chars]

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return ""

    async def _rewrite_as_patient_from_case(self, case_data: Dict, original_text: str, user_message: str) -> str:
        """Rewrite a bad model answer so it fits the selected patient case exactly."""
        prompt = (
            f"{self._build_case_persona_prompt(case_data)}\n\n"
            f"### TAREFA ADICIONAL:\n"
            f"Reescreve a RESPOSTA ORIGINAL abaixo para ficar 100% consistente com o perfil acima.\n"
            f"- Mantém primeira pessoa.\n"
            f"- Não inventes nada fora do perfil.\n"
            f"- Responde apenas ao que foi perguntado.\n"
            f"- Não menciones IA, simulador, base de dados, ficheiros ou outros pacientes.\n\n"
            f"### PERGUNTA DO UTILIZADOR:\n{user_message}\n\n"
            f"### RESPOSTA ORIGINAL:\n{original_text}\n\n"
            f"### RESPOSTA REESCRITA:\n"
        )

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_k": 5,
                "top_p": 0.2,
                "num_ctx": 1024,
                "num_predict": 120,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.ollama_host}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        return (data.get("response") or "").strip()

    def _looks_like_doctor_response(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in self.doctor_like_phrases)

    async def _rewrite_as_patient(self, original_text: str, user_message: str, knowledge: str) -> str:
        prompt = (
            f"PERSONA:\n{self.persona_text}\n\n"
            f"REESCREVE A RESPOSTA COMO UM PACIENTE.\n"
            f"- Mantém primeira pessoa.\n"
            f"- Remove qualquer tom de médico, aconselhamento ou diagnóstico.\n"
            f"- Usa apenas informação já presente na resposta original e no conhecimento.\n"
            f"- Resposta curta, natural e direta.\n\n"
            f"KNOWLEDGE:\n{knowledge}\n\n"
            f"USER:\n{user_message}\n\n"
            f"RESPOSTA ORIGINAL:\n{original_text}\n\n"
            f"ASSISTANT:"
        )

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_k": 10,
                "top_p": 0.5,
                "num_ctx": 768,
                "num_predict": 96,
            },
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(f"{self.ollama_host}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        return (data.get("response") or "").strip()

    def _fallback_patient_reply(self, user_message: str, case_data: Optional[Dict] = None) -> str:
        """Final safe fallback when the model fails to answer properly."""
        return "Não sei com base nos dados deste caso."

    async def generate_response(
        self,
        sessao_id: str,
        user_message: str,
        context: Optional[str] = None,
        max_tokens: int = 160,
        disease: Optional[str] = None,
    ) -> Dict[str, object]:
        """Generate a concise AI response using only the single session case and conversation history."""
        try:
            # Clean old sessions periodically
            self._cleanup_old_sessions()

            # Ensure session has a clinical case assigned
            if sessao_id not in self.session_cases:
                assigned = await self.start_roleplay_session(sessao_id)
                if assigned.get("status") == "error":
                    raise RuntimeError(assigned.get("message", "No clinical case assigned"))

            case_data = self.session_cases.get(sessao_id)
            if not case_data:
                raise RuntimeError(f"No clinical case available for session {sessao_id}")

            active_case_id = case_data.get("ID")
            self._log_active_patient(sessao_id)
            logger.info(f" Session {sessao_id} currently simulating case ID: {active_case_id}")

            # Deterministic answer for identity/basic case questions
            if self._looks_like_identity_question(user_message):
                direct_answer = self._answer_from_case(sessao_id, user_message)
                if not direct_answer:
                    direct_answer = "Não sei com base nos dados deste caso."

                # Only translate if necessary (skip HTTP call for Portuguese responses when user speaks Portuguese)
                target_language = self._detect_message_language(user_message)
                logger.info(f" Detected language for identity question: {target_language}")
                
                if target_language in {"pt", "en"}:
                    direct_answer = await self._translate_to_user_language(direct_answer, target_language)
                else:
                    # Fallback to Portuguese if language detection fails
                    logger.warning(f"Unknown language detected: {target_language}, using Portuguese")
                    direct_answer = self._localize_response(direct_answer, "pt")

                self._add_message_to_history(sessao_id, "user", user_message)
                self._add_message_to_history(sessao_id, "patient", direct_answer)
                logger.info(f" Deterministic case answer used for session {sessao_id} (case ID {self.session_cases.get(sessao_id, {}).get('ID')})")
                result = {
                    "response": direct_answer,
                    "tokens_used": len(user_message.split()) + len(direct_answer.split()),
                    "model": self.ollama_model,
                    "context_found": True,
                    "case_id": active_case_id,
                    "deterministic": True,
                }
                self.response_cache[f"{sessao_id}:{active_case_id}:{user_message.lower().strip()}"] = {
                    "response": result,
                    "timestamp": datetime.now()
                }
                return result

            # Check cache first (per-session cache)
            cache_key = f"{sessao_id}:{active_case_id}:{user_message.lower().strip()}"
            if cache_key in self.response_cache:
                cached = self.response_cache[cache_key]
                if datetime.now() - cached['timestamp'] < timedelta(seconds=self.cache_ttl):
                    logger.info(f"Cache hit for: {user_message[:50]}")
                    # But still add to history even if cached
                    self._add_message_to_history(sessao_id, "user", user_message)
                    response_text = cached['response']['response']
                    self._add_message_to_history(sessao_id, "patient", response_text)
                    return cached['response']
                else:
                    del self.response_cache[cache_key]

            direct_answer = self._answer_from_case(sessao_id, user_message)
            if direct_answer:
                response_text = direct_answer
            else:
                response_text = self._fallback_patient_reply(user_message, case_data)

            target_language = self._detect_message_language(user_message)
            logger.info(f" Detected language for general question: {target_language}")
            
            if target_language in {"pt", "en"}:
                response_text = await self._translate_to_user_language(response_text, target_language)
            else:
                # Fallback to Portuguese if language detection fails
                logger.warning(f"Unknown language detected: {target_language}, using Portuguese")
                response_text = self._localize_response(response_text, "pt")

            # Add patient response to history
            self._add_message_to_history(sessao_id, "user", user_message)
            self._add_message_to_history(sessao_id, "patient", response_text)

            tokens_used = len(user_message.split()) + len(response_text.split())
            result = {
                "response": response_text,
                "tokens_used": tokens_used,
                "model": self.ollama_model,
                "context_found": True,
                "case_id": active_case_id,
            }
            
            # Cache the response
            self.response_cache[cache_key] = {
                'response': result,
                'timestamp': datetime.now()
            }
            
            return result

        except Exception as e:
            logger.exception(f"Error generating response for session {sessao_id}: {e}")
            fallback_language = self._detect_message_language(user_message)
            fallback_text = self._fallback_patient_reply(user_message, self.session_cases.get(sessao_id))
            if fallback_language == "en":
                fallback_text = self._localize_response(fallback_text, "en")
            else:
                fallback_text = self._localize_response(fallback_text, "pt")

            try:
                self._add_message_to_history(sessao_id, "user", user_message)
                self._add_message_to_history(sessao_id, "patient", fallback_text)
            except Exception:
                pass

            return {
                "response": fallback_text,
                "tokens_used": len(user_message.split()) + len(fallback_text.split()),
                "model": self.ollama_model,
                "context_found": False,
                "case_id": self.session_cases.get(sessao_id, {}).get("ID"),
                "error": str(e),
                "fallback": True,
            }

    async def get_available_models(self) -> List[str]:
        """Get available models from Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_host}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", self.ollama_model) for m in data.get("models", [])]
                return [self.ollama_model]
        except Exception as e:
            logger.error(f"Failed to get models from Ollama: {e}")
            return [self.ollama_model]

    def get_session_history(self, sessao_id: str) -> Dict:
        """Get conversation history for a session."""
        if sessao_id not in self.conversations:
            return {
                "sessao_id": sessao_id,
                "messages": [],
                "message_count": 0,
                "status": "no_history"
            }

        return {
            "sessao_id": sessao_id,
            "messages": self.conversations[sessao_id],
            "message_count": len(self.conversations[sessao_id]),
            "status": "active"
        }

    def clear_session_history(self, sessao_id: str) -> Dict:
        """Clear conversation history for a session."""
        removed_anything = False
        if sessao_id in self.conversations:
            del self.conversations[sessao_id]
            del self.session_timestamps[sessao_id]
            removed_anything = True

        if sessao_id in self.session_personas:
            del self.session_personas[sessao_id]
            removed_anything = True

        if sessao_id in self.session_cases:
            del self.session_cases[sessao_id]
            removed_anything = True

        if removed_anything:
            logger.info(f"Cleared history for session: {sessao_id}")
            return {"status": "cleared", "sessao_id": sessao_id}

        return {"status": "not_found", "sessao_id": sessao_id}
    
    def set_session_disease(self, sessao_id: str, disease: str) -> Dict:
        """Atribui uma nova doença a uma sessão."""
        # Deprecated: per-session disease system removed. Keep method for backward compatibility.
        return {
            "status": "error",
            "message": "Deprecated: per-session disease system removed. Use roleplay documents (.md) in knowledge folder.",
        }

    def get_session_disease(self, sessao_id: str) -> Dict:
        """Obtém a doença atribuída a uma sessão."""
        # Deprecated: per-session disease system removed.
        return {
            "sessao_id": sessao_id,
            "status": "deprecated",
            "message": "Per-session disease system removed. Use roleplay documents (.md) instead.",
        }
    
    def get_available_diseases(self) -> Dict:
        """Retorna lista de doenças disponíveis."""
        # Deprecated
        return {
            "status": "deprecated",
            "message": "Per-session disease system removed. No available diseases.",
        }















