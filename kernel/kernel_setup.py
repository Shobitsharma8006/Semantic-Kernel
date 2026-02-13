# kernel/kernel_setup.py
 
from semantic_kernel import Kernel

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion # Import change

from config.settings import settings
 
async def create_kernel() -> Kernel:

    kernel = Kernel()
 
    # Azure OpenAI Service Configuration

    # Ab AsyncOpenAI client ki zarurat nahi hai, Semantic Kernel ise khud handle karta hai

    # kernel.add_service(

    #     AzureChatCompletion(

    #         service_id="azure-chat",

    #         deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,

    #         endpoint=settings.AZURE_OPENAI_ENDPOINT,

    #         api_key=settings.AZURE_OPENAI_API_KEY,

    #     )

    # )
    chat_service = AzureChatCompletion(
        service_id="azure-chat",
        deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )

    kernel.add_service(chat_service)


    # --- Import and Add Plugins ---

    from plugins.assessment import AssessmentPlugin

    from plugins.parsing import ParsingPlugin

    from plugins.queue_handler import QueuePlugin 

    from plugins.mapping import MappingPlugin

    from plugins.monitoring import MonitoringAgentPlugin
 
    kernel.add_plugin(MonitoringAgentPlugin(), "MonitoringAgentTools")

    kernel.add_plugin(AssessmentPlugin(), "AssessmentTools")

    kernel.add_plugin(ParsingPlugin(), "ParsingTools")

    kernel.add_plugin(QueuePlugin(), "QueueTools")

    kernel.add_plugin(MappingPlugin(), "MappingTools")
 
    return kernel
 