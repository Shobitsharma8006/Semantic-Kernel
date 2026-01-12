# kernel/kernel_setup.py 

from openai import AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from config.settings import settings

async def create_kernel() -> Kernel:
    kernel = Kernel()

    # OpenRouter requires an 'HTTP-Referer' and 'X-Title' for many models
    # to avoid the "User not found" 401 error.
# kernel/kernel_setup.py

    openrouter_client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Semantic Agent",
        }
    )

    # Use the custom client when adding the service
    kernel.add_service(
        OpenAIChatCompletion(
            service_id="openrouter-chat",
            ai_model_id="openai/gpt-4o-mini",
            async_client=openrouter_client 
        )
    )

    from plugins.assessment import AssessmentPlugin
    kernel.add_plugin(AssessmentPlugin(), "AssessmentTools")

    return kernel