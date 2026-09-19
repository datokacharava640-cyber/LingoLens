@app.post("/academic-assistant")
@limiter.limit("20/minute")
async def academic_assistant(
    request: Request,
    task_type: str = Form(...),  # 'essay', 'summarize', 'paraphrase'
    text: str = Form(...),
    target_lang: str = Form("ka")
):
    """სტუდენტური და სასკოლო აკადემიური ასისტენტი"""
    if not text.strip():
        return {"result": ""}

    if task_type == "essay":
        prompt = (
            f"You are an academic expert. Help write a well-structured essay/assignment/topic based on: '{text}'. "
            f"Include an Introduction, Main Body Arguments, and Conclusion. "
            f"Write the response in the language corresponding to code '{target_lang}'."
        )
    elif task_type == "summarize":
        prompt = (
            f"Summarize the following text into key concepts, main ideas, and structured bullet points. "
            f"Provide the response in language code '{target_lang}':\n\n{text}"
        )
    elif task_type == "paraphrase":
        prompt = (
            f"Rewrite the following text in a professional, formal, and academic tone in language code '{target_lang}':\n\n{text}"
        )
    else:
        prompt = text

    # 1. OpenAI
    if client:
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            return {"result": res.choices[0].message.content.strip()}
        except Exception as e:
            print(f"[Academic OpenAI Fallback]: {e}")

    # 2. Gemini Fallback
    if gemini_model:
        try:
            res = gemini_model.generate_content(prompt)
            return {"result": res.text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Academic AI service unavailable.")
