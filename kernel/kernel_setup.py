# kernel/kernel_setup.py 

from openai import AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from config.settings import settings

async def create_kernel() -> Kernel:
    kernel = Kernel()

    # OpenRouter Client Configuration
    openrouter_client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Semantic Agent",
        }
    )

    kernel.add_service(
        OpenAIChatCompletion(
            service_id="openrouter-chat",
            ai_model_id="openai/gpt-4o-mini",
            async_client=openrouter_client 
        )
    )

    # --- Import and Add Plugins ---
    from plugins.assessment import AssessmentPlugin
    from plugins.parsing import ParsingPlugin
    from plugins.queue_handler import QueuePlugin 
    from plugins.mapping import MappingPlugin

    kernel.add_plugin(AssessmentPlugin(), "AssessmentTools")
    kernel.add_plugin(ParsingPlugin(), "ParsingTools")
    kernel.add_plugin(QueuePlugin(), "QueueTools")
    kernel.add_plugin(MappingPlugin(), "MappingTools")

    return kernel