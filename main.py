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
    print("--- @cl.on_chat_start: SIMPLIFIED start() function entered ---")
    try:
        cl.user_session.set("greeting", "Hello from simplified start!")
        await cl.Message(content="Simplified application started!").send()
        print("--- @cl.on_chat_start: SIMPLIFIED start() function finished successfully. ---")
    except Exception as e:
        print(f"--- @cl.on_chat_start: EXCEPTION IN SIMPLIFIED START: {str(e)} ---")
        import traceback
        traceback.print_exc()
        await cl.Message(content=f"Error during simplified startup: {str(e)}").send()
        raise

# @cl.on_message
# async def main(message: cl.Message):
#     print("--- @cl.on_message: main() function entered ---")
#     msg = cl.Message(content="Soch raha hoon... 🧠")
#     await msg.send()

#     active_agent: Agent = cast(Agent, cl.user_session.get("agent"))
#     run_config_instance: RunConfig = cast(RunConfig, cl.user_session.get("config"))
#     history: List[Dict[str,str]] = cl.user_session.get("chat_history") or []

#     history.append({"role": "user", "content": message.content})

#     try:
#         print(f"\n--- @cl.on_message: [CALLING_AGENT_WITH_CONTEXT] History length: {len(history)}\nLast message: {history[-1]}\n")
        
#         result: RunResult = Runner.run_sync(
#             starting_agent=active_agent,
#             input=history,
#             run_config=run_config_instance
#         )
#         print("--- @cl.on_message: Runner.run_sync completed ---")

#         response_content = result.final_output

#         msg.content = response_content
#         await msg.update()

#         cl.user_session.set("chat_history", result.to_input_list())

#         print(f"--- @cl.on_message: User: {message.content} ---")
#         print(f"--- @cl.on_message: Assistant: {response_content} ---")
#         print("--- @cl.on_message: main() function finished. ---")

#     except Exception as e:
#         error_message = f"⚠️ Error during agent processing in @cl.on_message: {str(e)}"
#         print(f"--- @cl.on_message: EXCEPTION: {error_message} ---")
#         import traceback
#         traceback.print_exc()
#         msg.content = error_message
#         await msg.update()

print("--- main.py: Script finished defining functions ---")