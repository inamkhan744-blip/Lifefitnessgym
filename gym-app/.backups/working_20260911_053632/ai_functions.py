import openai
import os

# ---------------------------------------------------------------------------
# Helper to call the LLM (OpenAI GPT‑4/3.5). Adjust the model and temperature as needed.
# ---------------------------------------------------------------------------
def get_ai_response(prompt: str, gym_id=None, role=None, username=None) -> str:
    """Generate a response from the LLM based on the user prompt.

    The function adds a small context about the gym environment so the model can
    give more relevant answers (e.g., member data, schedule info). You can extend
    this context further based on your database schema.
    """
    # Basic system prompt – you can enrich it with dynamic data later.
    system_prompt = (
        "You are a helpful AI assistant for a gym management system. "
        "Answer questions concisely and provide actionable suggestions. "
        "If you need to reference member data, schedules, or inventory, "
        "ask the user for more details."
    )

    # Combine system prompt with user prompt
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Sorry, I couldn't process the request. Error: {e}"
    return answer
