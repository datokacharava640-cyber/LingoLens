# modules/wake_word.py

def handle_wake_word(input_text):
    """
    ამოწმებს ტექსტში 'LingoLens'-ის არსებობას
    """
    if not input_text:
        return False, ""
    
    clean_text = input_text.lower().strip()
    if "lingolens" in clean_text:
        return True, "⚡ Wake Word Detected! How can LingoLens help you?"
    
    return False, ""
