from semantic_kernel.functions import kernel_function


class ParsingPlugin:
    
    @kernel_function(
        description="Basic response parsing/cleanup",
        name="clean_response"
    )
    async def clean_response(self, raw_text: str) -> str:
        # Very simple example
        return raw_text.strip().replace("\n\n", "\n")