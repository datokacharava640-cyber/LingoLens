# chat_service.py

# აქ ვინახავთ დიალოგის ისტორიას (მეხსიერებაში)
chat_history = []

def process_chat_message(user_message: str) -> dict:
    try:
        # შევინახოთ მომხმარებლის შეტყობინება ისტორიაში
        chat_history.append({"role": "user", "text": user_message})
        
        # მარტივი პასუხის გენერაცია (აქ შეგიძლია მიაბა OpenAI, Gemini ან სხვა AI მოდელი)
        bot_response = f"LingoLens ასისტენტი: მივიღე შენი შეტყობინება -> '{user_message}'. რით დაგეხმარო კიდევ?"
        
        # შევინახოთ ბოტის პასუხიც ისტორიაში
        chat_history.append({"role": "bot", "text": bot_response})
        
        return {
            "success": True,
            "response": bot_response,
            "history": chat_history
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
