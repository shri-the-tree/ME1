import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL_NAME, MAX_HISTORY_LENGTH
from prompt_engineering import SYSTEM_PROMPT
from vector_store import MarineEdgeVectorStore

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Initialize chat session
chat = model.start_chat(history=[])

# Initialize vector store
vector_store = MarineEdgeVectorStore(pdf_directory="./pdfs")
vector_store.create_or_load_vector_store()


def get_relevant_context(query, k=3):
    """Retrieve relevant information from the vector store"""
    results = vector_store.query_vector_store(query, k=k)

    # Format the retrieved content
    context_texts = []
    for doc, score in results:
        if score < 1.5:  # Filter by relevance score
            context_texts.append(f"--- Relevant Information (score: {score:.2f}) ---\n{doc.page_content}")

    return "\n\n".join(context_texts)


def get_bot_response(user_input):
    """Get response from the bot using Gemini API with vector store augmentation."""
    try:
        # Get relevant context from vector store
        relevant_context = get_relevant_context(user_input)

        # Create enhanced prompt with context
        if relevant_context:
            enhanced_input = f"""
{SYSTEM_PROMPT}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{relevant_context}

USER QUERY: {user_input}

Please provide a helpful response based on the above context.
"""
        else:
            enhanced_input = user_input

        # Generate response
        response = chat.send_message(enhanced_input)

        return response.text

    except Exception as e:
        print(f"Error: {str(e)}")
        return "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question."


def main():
    """Simple command-line interface for testing."""
    print("Marine Edge Assistant (Type 'exit' to quit)")
    print("-" * 50)
    print("Initializing vector database... Please wait.")

    # Send initial system prompt to set the context
    try:
        chat.send_message(SYSTEM_PROMPT)
        print("Bot initialized successfully!")
    except Exception as e:
        print(f"Warning: Could not set initial system prompt: {str(e)}")
        print("Continuing without initial system prompt...")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Thank you for using Marine Edge Assistant!")
            break

        bot_response = get_bot_response(user_input)
        print(f"\nMarine Edge Assistant: {bot_response}")


if __name__ == "__main__":
    main()