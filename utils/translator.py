# 1. მთარგმნელი
  def open_translator(self, instance=None, initial_text=""):
    font = GEORGIAN_FONT_NAME
    box = BoxLayout(
        orientation="vertical",
        padding=dp(10),
        spacing=dp(10),
        size_hint=(1, 1),
    )

    lang_box = BoxLayout(
        orientation="horizontal", spacing=dp(5), size_hint_y=0.1
    )
    lang_names = list(SUPPORTED_LANGUAGES.keys())

    sp_src = Spinner(
        text="ქართული",
        values=lang_names,
        font_name=font,
        option_cls=CustomSpinnerOption,
    )
    sp_target = Spinner(
        text="English",
        values=lang_names,
        font_name=font,
        option_cls=CustomSpinnerOption,
    )

    def swap_languages(instance):
      temp = sp_src.text
      sp_src.text = sp_target.text
      sp_target.text = temp

    btn_swap = Button(text="<=>", size_hint_x=0.2, font_name=font)
    btn_swap.bind(on_press=swap_languages)

    lang_box.add_widget(sp_src)
    lang_box.add_widget(btn_swap)
    lang_box.add_widget(sp_target)

    inp = TextInput(
        text=initial_text,
        hint_text=self.get_text("hint_input"),
        font_name=font,
        multiline=True,
        size_hint_y=0.25,
    )
    out = TextInput(
        hint_text=self.get_text("hint_output"),
        font_name=font,
        readonly=True,
        multiline=True,
        size_hint_y=0.25,
    )
    status_lbl = Label(text="", size_hint_y=0.05, font_name=font)

    btn_trans = Button(
        text=self.get_text("btn_translate"), font_name=font, size_hint_y=0.1
    )

    action_box = BoxLayout(
        orientation="horizontal", spacing=dp(5), size_hint_y=0.1
    )
    btn_copy = Button(
        text=self.get_text("btn_copy"),
        font_name=font,
        on_press=lambda x: self.copy_to_clipboard(out.text),
    )
    btn_share = Button(
        text=self.get_text("btn_share"),
        font_name=font,
        on_press=lambda x: self.share_text(out.text),
    )
    btn_listen = Button(
        text=self.get_text("btn_listen"),
        font_name=font,
        on_press=lambda x: self.safe_speak(
            out.text, SUPPORTED_LANGUAGES.get(sp_target.text, "en")
        ),
    )

    action_box.add_widget(btn_copy)
    action_box.add_widget(btn_share)
    action_box.add_widget(btn_listen)

    def handle_translation(btn_inst):
      text_to_translate = inp.text.strip()
      if not text_to_translate:
        status_lbl.text = "გთხოვთ შეიყვანოთ ტექსტი"
        return

      src_code = SUPPORTED_LANGUAGES.get(sp_src.text, "ka")
      target_code = SUPPORTED_LANGUAGES.get(sp_target.text, "en")
      status_lbl.text = self.get_text("status_processing")
      out.text = ""

      def on_res(res):
        res_text = (
            str(res) if res else self.get_text("error_connection")
        )
        Clock.schedule_once(lambda dt: setattr(out, "text", res_text))
        Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))
        if res:
          self.save_to_history(text_to_translate, res_text)

      try:
        translate_text(
            prompt=(
                f"Translate accurately from {sp_src.text} to"
                f" {sp_target.text}: {text_to_translate}"
            ),
            text=text_to_translate,
            src_lang=src_code,
            target_lang=target_code,
            callback=on_res,
        )
      except Exception as e:
        print("Translation Error:", e)
        Clock.schedule_once(
            lambda dt: setattr(out, "text", self.get_text("error_connection"))
        )
        Clock.schedule_once(lambda dt: setattr(status_lbl, "text", ""))

    btn_trans.bind(on_press=handle_translation)

    box.add_widget(lang_box)
    box.add_widget(inp)
    box.add_widget(btn_trans)
    box.add_widget(status_lbl)
    box.add_widget(out)
    box.add_widget(action_box)

    if instance is not None:
      self.switch_to_view(box)
    return box
