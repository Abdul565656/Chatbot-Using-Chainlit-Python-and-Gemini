# agents.py
from typing import List, Dict, Any, Optional
import httpx # Used for making HTTP requests in this mock

# Note: The name "AsyncOpenAI" is used to match your import.
# However, to make it work with a synchronous Runner.run_sync as called in your main.py,
# the methods in this mock are implemented synchronously.
# A true AsyncOpenAI client (like from the 'openai' library) would use async/await.
class AsyncOpenAI:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') + "/" # Ensure trailing slash
        # For synchronous calls in this mock
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            base_url=self.base_url
        )
        print(f"Mock (Sync-acting) AsyncOpenAI initialized for: {self.base_url}")

    def chat_completions_create(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Synchronous mock for creating chat completions.
        This attempts to mimic an OpenAI-compatible API structure.
        """
        print(f"Mock (Sync-acting) AsyncOpenAI: Creating chat completion for model '{model}'")
        
        # Prepare payload for Gemini via OpenAI-compatible endpoint
        # The actual payload structure might vary based on the proxy.
        # Common practice is to pass messages directly.
        payload = {
            "model": model,
            "messages": messages
        }
        print(f"--- Sending to API ---\nModel: {model}\nMessages: {messages}\nPayload: {payload}\n----------------------")
        try:
            # The URL path for chat completions typically is "chat/completions"
            # The self.base_url should already point to ".../v1beta/openai/"
            # So the request path would be "chat/completions"
            response = self.client.post("chat/completions", json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors
            response_data = response.json()
            
            # Add a log to see what the actual API (or mock) returns
            print(f"Mock API Raw Response: {response_data}")

            # Ensure the response structure matches what OpenAIChatCompletionsModel expects
            if "choices" not in response_data or not response_data["choices"]:
                 # If Gemini returns a different structure, adapt here or make a simple mock
                last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no user input")
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": f"Mock translated content for: '{last_user_message}' (model: {model})"
                        }
                    }]
                }
            return response_data

        except httpx.HTTPStatusError as e:
            print(f"HTTP error calling mock API: {e.response.status_code} - {e.response.text}")
            return {"choices": [{"message": {"role": "assistant", "content": f"Error: HTTP {e.response.status_code}"}}]}
        except Exception as e:
            print(f"Error in mock chat_completions_create: {e}")
            return {"choices": [{"message": {"role": "assistant", "content": "Error in mock API call."}}]}

class OpenAIChatCompletionsModel:
    def __init__(self, model: str, openai_client: AsyncOpenAI):
        self.model_name = model
        self.client = openai_client # This is our sync-acting AsyncOpenAI mock
        print(f"Mock OpenAIChatCompletionsModel initialized with model: {self.model_name}")

    def generate_response_sync(self, messages: List[Dict[str, str]]) -> str:
        # Synchronous generation using the sync-acting client
        response_data = self.client.chat_completions_create(
            model=self.model_name,
            messages=messages
        )
        try:
            content = response_data["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing response in mock OpenAIChatCompletionsModel: {e}. Response: {response_data}")
            return "Error: Could not parse mock API response."

class RunConfig:
    def __init__(self, model: OpenAIChatCompletionsModel, model_provider: AsyncOpenAI, tracing_disabled: bool):
        self.model = model # The OpenAIChatCompletionsModel instance
        self.model_provider = model_provider # The AsyncOpenAI client instance
        self.tracing_disabled = tracing_disabled
        print("Mock RunConfig initialized.")

class Agent:
    def __init__(self, name: str, instructions: str, model: OpenAIChatCompletionsModel):
        self.name = name
        self.instructions = instructions
        self.model = model # The model with a sync generate_response_sync
        print(f"Mock Agent '{self.name}' initialized.")

    def process_sync(self, history: List[Dict[str, str]], config: RunConfig) -> str:
        # Synchronous processing
        print(f"Mock Agent '{self.name}' processing input (synchronously).")
        
        # Prepare messages for the model
        # For OpenAI/Gemini-OpenAI-proxy, system instruction can be the first message
        # or a dedicated 'system' role message.
        current_conversation: List[Dict[str, str]] = []
        if self.instructions:
             current_conversation.append({"role": "system", "content": self.instructions})
        current_conversation.extend(history) # Add the rest of the chat history
        
        return self.model.generate_response_sync(messages=current_conversation)

class RunResult: # A simple class to hold results
    def __init__(self, final_output: str, full_history: List[Dict[str, str]]):
        self.final_output = final_output
        self._full_history = full_history # Store the history including the last assistant message
        print(f"Mock RunResult created. Final output: {self.final_output[:60]}...")

    def to_input_list(self) -> List[Dict[str, str]]:
        # This should return the history that can be used as input for the next turn
        return self._full_history

class Runner:
    @staticmethod
    def run_sync(starting_agent: Agent, input: List[Dict[str, str]], run_config: RunConfig) -> RunResult:
        print(f"Mock Runner.run_sync processing {len(input)} history messages.")
        
        # Call the synchronous process method of the agent
        response_content = starting_agent.process_sync(input, run_config)
        
        # Create an updated history list including the agent's response
        updated_history = list(input) # Make a copy to avoid modifying the original list in place
        updated_history.append({"role": "assistant", "content": response_content})
        
        return RunResult(final_output=response_content, full_history=updated_history)