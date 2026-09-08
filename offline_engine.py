import os
import json

try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

class OfflineTranslatorEngine:
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        self.session = None
        self.vocab = {}
        self.is_loaded = False
        self._init_engine()

    def _init_engine(self):
        if not HAS_ONNX:
            print("[OfflineEngine] ONNX Runtime არ არის დაინსტალირებული.")
            return

        model_path = os.path.join(self.model_dir, "translation_model.onnx")
        vocab_path = os.path.join(self.model_dir, "vocab.json")

        if os.path.exists(model_path) and os.path.exists(vocab_path):
            try:
                # CPU ექსპლუატაცია მობილურსა და დესკტოპზე
                self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                with open(vocab_path, "r", encoding="utf-8") as f:
                    self.vocab = json.load(f)
                self.is_loaded = True
                print("[OfflineEngine] ლოკალური ONNX მოდელი წარმატებით ჩაიტვირთა.")
            except Exception as e:
                print(f"[OfflineEngine] მოდელის ჩატვირთვის შეცდომა: {e}")

    def translate_offline(self, text, src_lang, tgt_lang):
        """
        ლოკალური მოდელით თარგმნა ინტერნეტის გარეშე
        """
        if not self.is_loaded:
            return None

        try:
            # 1. Simple Tokenization (ტოკენიზაცია)
            tokens = text.lower().split()
            input_ids = [self.vocab.get(tok, 1) for tok in tokens]  # 1 = Unknown token

            # 2. ONNX Inference Engine
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: [input_ids]})

            # 3. Output Decoding
            translated_tokens = outputs[0][0]
            inv_vocab = {v: k for k, v in self.vocab.items()}
            translated_text = " ".join([inv_vocab.get(idx, "") for idx in translated_tokens if idx in inv_vocab])

            return translated_text.strip()
        except Exception as e:
            print(f"[OfflineEngine] Inference Error: {e}")
            return None
