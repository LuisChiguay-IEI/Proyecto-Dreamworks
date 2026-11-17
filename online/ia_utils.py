"""Cliente de IA local: llamadas explícitas usando Ollama (compatible con OpenAI)."""
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class AsistenteIA:
    def __init__(self):
        # Ollama no usa API Key real, pero el SDK exige un string no vacío.
        self.api_key = getattr(settings, 'OLLAMA_API_KEY', 'ollama-local')

    def _client(self):
        # Apuntamos a la URL local por defecto de Ollama
        return OpenAI(
            api_key=self.api_key, 
            base_url='http://localhost:11434/v1', 
            timeout=120.0, # Margen amplio para que el modelo cargue en RAM
            max_retries=0
        )

    def generar_respuesta_automatica(self, pregunta, historial_contexto=''):
        if not self.api_key:
            return 'La IA no está configurada. Puedes crear una consulta para recibir atención del equipo técnico.'
        
        try:
            response = self._client().chat.completions.create(
                model=getattr(settings, 'OLLAMA_MODEL', 'llama3.2'),
                messages=[
                    {'role': 'system', 'content': 'Eres un asistente de asistente de un catálogo de películas de DreamWorks y soporte de la plataforma. No solicites contraseñas ni datos personales. Responde de forma concisa.'},
                    {'role': 'user', 'content': pregunta[:1000]}
                ],
                max_tokens=1000,
            )
            return (response.choices[0].message.content or '').strip() or 'No se obtuvo una sugerencia. Intenta más tarde.'
            
        except Exception as exc:
            print(f"\n🚨 ERROR DE IA LOCAL (Ollama): {type(exc).__name__} - {str(exc)}\n")
            logger.warning('Asistente no disponible: %s', type(exc).__name__)
            return 'El asistente de IA no está disponible en este momento. Intenta más tarde o crea una consulta.'