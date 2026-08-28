"""Verify conversation store persistence: different conversation IDs, independent histories."""
import asyncio
from app.services.conversation_store import InMemoryConversationStore


async def main():
    store = InMemoryConversationStore()

    # Chat A
    conv_a = await store.create_conversation()
    await store.append(conv_a, "user", "hello from chat A")
    await store.append(conv_a, "assistant", "reply to chat A")

    # Chat B
    conv_b = await store.create_conversation()
    await store.append(conv_b, "user", "hello from chat B")
    await store.append(conv_b, "assistant", "reply to chat B")

    history_a = await store.get_history(conv_a)
    history_b = await store.get_history(conv_b)

    print(f"Conversation A id: {conv_a}")
    print(f"Conversation B id: {conv_b}")
    print(f"IDs different: {conv_a != conv_b}")
    print(f"Conversation A history ({len(history_a)} msgs): {history_a}")
    print(f"Conversation B history ({len(history_b)} msgs): {history_b}")
    print(f"Conversation A restored: {len(history_a) == 2}")
    print(f"Conversation B restored: {len(history_b) == 2}")
    print(f"Histories are independent: {history_a != history_b}")

    # New chat starts empty
    conv_c = await store.create_conversation()
    history_c = await store.get_history(conv_c)
    print(f"New conversation C id: {conv_c}")
    print(f"New conversation C history (should be empty): {history_c}")
    print(f"New conversation C is empty: {len(history_c) == 0}")


asyncio.run(main())