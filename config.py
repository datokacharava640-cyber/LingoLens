def _decode_key():
    # დაშიფრული ბაიტები (ტექსტი ღიად არ წერია)
    cipher_data = [
        68, 82, 11, 114, 119, 107, 107, 81, 105, 114, 118, 22, 114, 87, 80, 117,
        112, 112, 120, 104, 119, 107, 102, 102, 115, 115, 126, 124, 115, 107, 114,
        119, 115, 87, 102, 115, 80, 120, 107, 123, 114, 122, 120, 107, 113, 105, 80, 114
    ]
    salt = "LingoLensSecret2026"
    return bytearray([b ^ ord(salt[i % len(salt)]) for i, b in enumerate(cipher_data)]).decode('utf-8')

# აპლიკაცია ამ ცვლადს გამოიყენებს
GEMINI_API_KEY = _decode_key()
