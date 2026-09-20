def _decode_key(cipher_data):
    salt = "LingoLensSecret2026"
    return bytearray([b ^ ord(salt[i % len(salt)]) for i, b in enumerate(cipher_data)]).decode('utf-8')

# Vercel-ის ახალი დეკოდირებული მისამართი: https://lingo-lens-pied.vercel.app
API_ENDPOINT = _decode_key([
    68, 82, 11, 114, 119, 107, 107, 81, 105, 114, 118, 22, 114, 87, 80, 117,
    112, 112, 120, 104, 119, 107, 102, 102, 115, 115, 126, 112, 105, 101, 100,
    119, 115, 87, 102, 115, 80, 120, 107, 123, 114, 122, 120, 107, 113, 105, 80, 114
])

# Google Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6KDCvEgGaa-RBFKc1IX6TtvQaQ7aDee7q923av6EOLCbA"
