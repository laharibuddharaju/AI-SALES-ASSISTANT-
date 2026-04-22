from transformers import pipeline

# lightweight text-generation pipeline
_generator = pipeline(
    "text-generation",
    model="distilgpt2",   # safe starter; swap to LLaMA/Mistral later
)

def llm_suggest(prompt: str) -> str:
    """
    LLM provides suggestions/clarifications only.
    Never directly performs DB actions.
    """
    out = _generator(prompt, max_length=80, num_return_sequences=1)
    return out[0]["generated_text"]
