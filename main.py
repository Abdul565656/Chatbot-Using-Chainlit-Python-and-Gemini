import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

# Load environment variables
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

@cl.on_chat_start
async def start():
    external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client
    )

    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

    # Initialize session
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    agent: Agent = Agent(
        name="Abdullah's Assistant 🤖",
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

    cl.user_session.set("agent", agent)

    await cl.Message(content="""🌍 Welcome! I’m your Translator Agent.
Send any text in any language — I’ll translate it to the language you need.""").send()


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Soch raha hoon... 🧠")
    await msg.send()

    agent: Agent = cast(Agent, cl.user_session.get("agent"))
    config: RunConfig = cast(RunConfig, cl.user_session.get("config"))
    history = cl.user_session.get("chat_history") or []

    history.append({"role": "user", "content": message.content})

    try:
        print("\n[CALLING_AGENT_WITH_CONTEXT]\n", history, "\n")
        result = Runner.run_sync(
            starting_agent=agent,
            input=history,
            run_config=config
        )

        response_content = result.final_output

        msg.content = response_content
        await msg.update()

        cl.user_session.set("chat_history", result.to_input_list())

        print(f"User: {message.content}")
        print(f"Assistant: {response_content}")

    except Exception as e:
        msg.content = f"⚠️ Error: {str(e)}"
        await msg.update()
        print(f"Error: {str(e)}")
