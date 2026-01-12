# kernel/kernel_setup.py 

import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from config.settings import settings

async def create_kernel() -> Kernel:
    kernel = Kernel()

    os.environ["OPENAI_API_BASE"] = settings.OPENROUTER_BASE_URL

    kernel.add_service(
        OpenAIChatCompletion(
            service_id="openrouter-chat",
            api_key=settings.OPENROUTER_API_KEY,
            ai_model_id="openai/gpt-4o-mini"  # or your preferred model
        )
    )

    from plugins.assessment import AssessmentPlugin
    kernel.add_plugin(AssessmentPlugin(), "AssessmentTools")

    return kernel