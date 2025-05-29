# main.py
import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
# This import will now work if agents.py is in the same directory
from agents import Agent, Runner, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, RunResult
# Load environment variables
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file or environment.")

@cl.on_chat_start
async def start():
    # Initialize our (mocked sync-acting) AsyncOpenAI client
    external_client = AsyncOpenAI(
        api_key=gemini_api_key, # Your API key
        base_url="https://generativelanguage.googleapis.com/v1beta/", # Corrected base for Gemini API direct
                                                                  # If using an OpenAI proxy layer for Gemini, it would be different
                                                                  # e.g., "https://generativelanguage.googleapis.com/v1beta/openai/" if that's your proxy
    )
    # The provided agents.py uses base_url like "https://generativelanguage.googleapis.com/v1beta/openai/"
    # and then appends "chat/completions". Ensure your base_url is set accordingly.
    # If your `agents.py` `AsyncOpenAI` expects the full path to the "openai" compatible part:
    # base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    # Let's stick to the one in your original code for the client:
    external_client_openai_proxy = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


    model = OpenAIChatCompletionsModel(
        model="gemini-1.5-flash-latest", # Use a valid Gemini model name available at your endpoint
        openai_client=external_client_openai_proxy
    )

    config = RunConfig(
        model=model,
        model_provider=external_client_openai_proxy, # Pass the client
        tracing_disabled=True
    )

    # Initialize session
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    agent_instance: Agent = Agent( # Renamed to avoid conflict with imported Agent class
        name="Abdullah's Translator Assistant 🤖",
        instructions=(
            """You are a translation assistant. Translate any input text to Spanish"""
        ),
        model=model
    )

    cl.user_session.set("agent", agent_instance)

    await cl.Message(content="""🌍 Welcome! I’m your Translator Agent.
Send any text in any language — I’ll translate it to the language you need.""").send()


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Soch raha hoon... 🧠")
    await msg.send()

    active_agent: Agent = cast(Agent, cl.user_session.get("agent")) # Use the instance from session
    run_config_instance: RunConfig = cast(RunConfig, cl.user_session.get("config")) # Use the instance
    history: List[Dict[str,str]] = cl.user_session.get("chat_history") or []

    # Add current user message to history
    # The history for the model should be a list of {"role": "user/assistant", "content": "..."}
    history.append({"role": "user", "content": message.content})

    try:
        print(f"\n[CALLING_AGENT_WITH_CONTEXT] History length: {len(history)}\nLast message: {history[-1]}\n")
        
        # Runner.run_sync is called, which uses the synchronous methods in our mock agents.py
        result: RunResult = Runner.run_sync(
            starting_agent=active_agent,
            input=history, # Pass the current history including the new user message
            run_config=run_config_instance
        )

        response_content = result.final_output

        msg.content = response_content
        await msg.update()

        # Update chat_history in session with the history that now includes the assistant's response
        cl.user_session.set("chat_history", result.to_input_list())

        print(f"User: {message.content}")
        print(f"Assistant: {response_content}")

    except Exception as e:
        error_message = f"⚠️ Error during agent processing: {str(e)}"
        msg.content = error_message
        await msg.update()
        print(error_message)
        # Optionally, re-raise or log more detailed traceback for debugging
        import traceback
        traceback.print_exc()