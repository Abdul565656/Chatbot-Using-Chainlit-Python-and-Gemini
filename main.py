# main.py
import os
from dotenv import load_dotenv # Keep this import, load_dotenv() itself is fine
from typing import cast, List, Dict # Added List, Dict for clarity
import chainlit as cl
from agents import Agent, Runner, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, RunResult # Ensure RunResult is imported

print("--- main.py: Script started ---")

# Load environment variables (this will now do nothing if .env is not present, which is correct)
load_dotenv()
print("--- main.py: load_dotenv() called ---")

gemini_api_key = os.getenv("GEMINI_API_KEY")
print(f"--- main.py: GEMINI_API_KEY retrieved: {'SET' if gemini_api_key else 'NOT SET'} ---")

if not gemini_api_key:
    print("--- main.py: GEMINI_API_KEY is NOT SET. Raising ValueError. ---")
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your environment variables.")
else:
    print("--- main.py: GEMINI_API_KEY is SET. ---")

@cl.on_chat_start
async def start():
    print("--- @cl.on_chat_start: start() function entered ---")
    try:
        print("--- @cl.on_chat_start: Initializing AsyncOpenAI ---")
        external_client_openai_proxy = AsyncOpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        print("--- @cl.on_chat_start: AsyncOpenAI initialized ---")

        print("--- @cl.on_chat_start: Initializing OpenAIChatCompletionsModel ---")
        model = OpenAIChatCompletionsModel(
            model="gemini-1.5-flash-latest",
            openai_client=external_client_openai_proxy
        )
        print("--- @cl.on_chat_start: OpenAIChatCompletionsModel initialized ---")

        print("--- @cl.on_chat_start: Initializing RunConfig ---")
        config = RunConfig(
            model=model,
            model_provider=external_client_openai_proxy,
            tracing_disabled=True
        )
        print("--- @cl.on_chat_start: RunConfig initialized ---")

        print("--- @cl.on_chat_start: Setting up user session (chat_history, config) ---")
        cl.user_session.set("chat_history", [])
        cl.user_session.set("config", config)
        print("--- @cl.on_chat_start: User session (chat_history, config) set ---")

        print("--- @cl.on_chat_start: Initializing Agent ---")
        agent_instance: Agent = Agent(
            name="Abdullah's Translator Assistant 🤖",
            instructions=(
                """You are a Translator Agent. Your job is to translate any input text from one language to another, with full accuracy, preserving the original meaning, tone, context, and cultural relevance.
                  🧠 Core Responsibilities:
                         Detect the source language automatically (unless specified).
                         Translate into the target language as requested by the user.
                         If the target language is not specified, default to English.
                         Use natural, fluent, and native-sounding language in your translations.
                         Ensure clarity and contextual accuracy — avoid overly literal translations.
                         For technical, poetic, or culturally sensitive texts, make thoughtful adjustments while preserving intent.
                         Do not omit, shorten, or paraphrase unless explicitly asked to.
                         If transliteration (writing one language’s sounds using another language’s script) is requested instead of translation, perform transliteration.
                         If a word or phrase is unclear or ambiguous, make your best guess and indicate uncertainty politely.😊"""
            ),
            model=model
        )
        print("--- @cl.on_chat_start: Agent initialized ---")

        cl.user_session.set("agent", agent_instance)
        print("--- @cl.on_chat_start: User session (agent) set ---")

        print("--- @cl.on_chat_start: Sending welcome message ---")
        await cl.Message(content="""🌍 Welcome! I’m your Translator Agent.
    Send any text in any language — I’ll translate it to the language you need.""").send()
        print("--- @cl.on_chat_start: Welcome message sent. start() function finished. ---")

    except Exception as e:
        print(f"--- @cl.on_chat_start: EXCEPTION OCCURRED: {str(e)} ---")
        import traceback
        traceback.print_exc() # This will print the full traceback to the logs
        # Optionally, send an error message to the UI if it gets that far
        await cl.Message(content=f"Error during startup: {str(e)}").send()
        raise # Re-raise the exception to ensure it's logged as a crash if severe

@cl.on_message
async def main(message: cl.Message):
    print("--- @cl.on_message: main() function entered ---")
    msg = cl.Message(content="Soch raha hoon... 🧠")
    await msg.send()

    active_agent: Agent = cast(Agent, cl.user_session.get("agent"))
    run_config_instance: RunConfig = cast(RunConfig, cl.user_session.get("config"))
    history: List[Dict[str,str]] = cl.user_session.get("chat_history") or []

    history.append({"role": "user", "content": message.content})

    try:
        print(f"\n--- @cl.on_message: [CALLING_AGENT_WITH_CONTEXT] History length: {len(history)}\nLast message: {history[-1]}\n")
        
        result: RunResult = Runner.run_sync(
            starting_agent=active_agent,
            input=history,
            run_config=run_config_instance
        )
        print("--- @cl.on_message: Runner.run_sync completed ---")

        response_content = result.final_output

        msg.content = response_content
        await msg.update()

        cl.user_session.set("chat_history", result.to_input_list())

        print(f"--- @cl.on_message: User: {message.content} ---")
        print(f"--- @cl.on_message: Assistant: {response_content} ---")
        print("--- @cl.on_message: main() function finished. ---")

    except Exception as e:
        error_message = f"⚠️ Error during agent processing in @cl.on_message: {str(e)}"
        print(f"--- @cl.on_message: EXCEPTION: {error_message} ---")
        import traceback
        traceback.print_exc()
        msg.content = error_message
        await msg.update()

print("--- main.py: Script finished defining functions ---")