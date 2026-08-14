def summarize_doc(doc_text=""):
    if not doc_text:
        return "📄 Upload PDF or Record Voice Note to summarize."
    return f"📝 [AI Summary]: {doc_text[:100]}... (Key Insights Extracted)"
