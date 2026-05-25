import string
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

import cfg_writer
import config_manager
import xhair_parser

APP_TITLE = "CS2 Crosshair Manager"

COLORS = {
    "window": "#202020",
    "panel": "#2b2b2b",
    "panel_alt": "#303030",
    "panel_edge": "#444444",
    "text": "#eeeeee",
    "muted": "#aaaaaa",
    "accent": "#3a7d44",
    "accent_hover": "#438f4e",
    "danger": "#7a3333",
    "danger_hover": "#884040",
    "control": "#3a3a3a",
    "control_hover": "#484848",
    "selected": "#3f4a3f",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def _button(parent, text, command=None, *, width=None):
    fg = COLORS["control"]
    hover = COLORS["control_hover"]
    text_color = COLORS["text"]

    kwargs = {}
    if width is not None:
        kwargs["width"] = width

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        height=25,
        corner_radius=0,
        border_width=1,
        border_color=COLORS["panel_edge"],
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        font=("Arial", 11),
        **kwargs,
    )


def _label(parent, text, *, muted=False, bold=False, size=12, **kwargs):
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=COLORS["muted"] if muted else COLORS["text"],
        font=("Arial", size, "bold" if bold else "normal"),
        **kwargs,
    )


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("860x535")
        self.minsize(780, 500)
        self.configure(fg_color=COLORS["window"])

        try:
            self._config = config_manager.load()
        except config_manager.ConfigError as exc:
            messagebox.showwarning("Config Reset", str(exc))
            self._config = config_manager.default_config()

        self._current_letter = None
        self._current_cvars = {}
        self._current_share_code = ""
        self._list_buttons = {}
        self._cycle_dialog = None
        self._cycle_button = None
        self._cycle_bind_value = self._config.get("cycle_bind", "")
        self._bind_listening = False

        self._build_ui()
        self._refresh_list()
        self._auto_detect_path()
        self._select_first_saved()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()
        self._build_bottom_bar()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=COLORS["panel"])
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(2, weight=1)
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_propagate(False)

        header = ctk.CTkFrame(sb, fg_color="transparent")
        header.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        _label(header, "Crosshair list", bold=True, size=14).grid(row=0, column=0, sticky="w")
        _button(sb, "Add", self._on_add_new).grid(
            row=1, column=0, padx=8, pady=(0, 6), sticky="ew"
        )

        self._list_frame = ctk.CTkScrollableFrame(
            sb,
            corner_radius=0,
            fg_color=COLORS["window"],
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        self._list_frame.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")

    def _build_content(self):
        panel = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["window"])
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, padx=8, pady=(7, 5), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        self._letter_lbl = _label(top, "-", bold=True, size=20, width=30)
        self._letter_lbl.grid(row=0, column=0, rowspan=2, sticky="w")
        _label(top, "Selected:", muted=True, size=11).grid(row=0, column=1, sticky="sw", padx=(8, 0))
        self._title_lbl = _label(top, "No preset selected", bold=True, size=14)
        self._title_lbl.grid(row=1, column=1, sticky="nw", padx=(8, 0))

        work = ctk.CTkFrame(panel, corner_radius=0, fg_color="transparent")
        work.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nsew")
        work.grid_columnconfigure(0, weight=0)
        work.grid_columnconfigure(1, weight=1)
        work.grid_rowconfigure(0, weight=1)

        details_col = ctk.CTkFrame(
            work,
            corner_radius=0,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        details_col.grid(row=0, column=0, padx=(0, 8), sticky="ns")
        details_col.grid_columnconfigure(0, weight=1)

        _label(details_col, "Parsed settings", bold=True, size=13).grid(
            row=0, column=0, padx=8, pady=(7, 5), sticky="w"
        )

        info = ctk.CTkFrame(details_col, fg_color="transparent")
        info.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")
        info.grid_columnconfigure(1, weight=1)
        _label(info, "Name", muted=True).grid(row=0, column=0, padx=(0, 8), sticky="w")
        self._label_entry = ctk.CTkEntry(
            info,
            height=25,
            corner_radius=0,
            border_color=COLORS["panel_edge"],
            fg_color=COLORS["control"],
            text_color=COLORS["text"],
            placeholder_text="Preset name",
        )
        self._label_entry.grid(row=0, column=1, sticky="ew")

        self._summary_box = ctk.CTkTextbox(
            details_col,
            width=220,
            height=190,
            wrap="none",
            corner_radius=0,
            border_width=1,
            border_color=COLORS["panel_edge"],
            fg_color="#1b1b1b",
            text_color=COLORS["text"],
            font=("Consolas", 10),
        )
        self._summary_box.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="ew")
        self._summary_box.configure(state="disabled")

        self._hide_targetid = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            details_col,
            text="Hide target ID",
            variable=self._hide_targetid,
            command=self._on_targetid_toggle,
            corner_radius=0,
            fg_color=COLORS["control"],
            hover_color=COLORS["control_hover"],
            text_color=COLORS["text"],
        ).grid(row=3, column=0, padx=8, pady=(0, 6), sticky="w")

        cmd_head = ctk.CTkFrame(details_col, fg_color="transparent")
        cmd_head.grid(row=4, column=0, padx=8, pady=(0, 4), sticky="ew")
        cmd_head.grid_columnconfigure(0, weight=1)
        _label(cmd_head, "Command", bold=True, size=12).grid(row=0, column=0, sticky="w")
        _button(cmd_head, "Copy", self._on_copy_command, width=58).grid(row=0, column=1, sticky="e")

        self._command_box = ctk.CTkTextbox(
            details_col,
            width=220,
            height=100,
            wrap="word",
            corner_radius=0,
            border_width=1,
            border_color=COLORS["panel_edge"],
            fg_color="#1b1b1b",
            text_color=COLORS["text"],
            font=("Consolas", 10),
        )
        self._command_box.grid(row=5, column=0, padx=8, pady=(0, 8), sticky="ew")
        self._command_box.configure(state="disabled")

        import_col = ctk.CTkFrame(
            work,
            corner_radius=0,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        import_col.grid(row=0, column=1, sticky="nsew")
        import_col.grid_columnconfigure(0, weight=1)
        import_col.grid_rowconfigure(1, weight=1)

        _label(import_col, 'Paste find cl_crosshair output or share code', bold=True, size=13).grid(
            row=0, column=0, padx=8, pady=(7, 5), sticky="w"
        )
        self._paste_box = ctk.CTkTextbox(
            import_col,
            wrap="none",
            corner_radius=0,
            border_width=1,
            border_color=COLORS["panel_edge"],
            fg_color="#1b1b1b",
            text_color=COLORS["text"],
            font=("Consolas", 10),
        )
        self._paste_box.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="nsew")
        self._paste_box.bind("<Control-a>", self._select_all_textbox)
        self._paste_box.bind("<Control-A>", self._select_all_textbox)

        btn_row = ctk.CTkFrame(import_col, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="ew")
        btn_row.grid_columnconfigure(3, weight=1)
        _button(btn_row, "Import", self._on_import, width=95).grid(row=0, column=0, padx=(0, 8))
        _button(btn_row, "Save", self._on_save, width=105).grid(row=0, column=1, padx=(0, 8))
        _button(btn_row, "Delete", self._on_delete, width=85).grid(row=0, column=2)

    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, height=42, corner_radius=0, fg_color=COLORS["panel_alt"])
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        _label(bar, "Cfg path", muted=True).grid(row=0, column=0, padx=(14, 7), pady=8, sticky="w")
        self._path_lbl = _label(bar, "Not set", muted=True, anchor="w")
        self._path_lbl.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        _button(bar, "Browse", self._on_change_path, width=84).grid(row=0, column=2, padx=6, pady=8)

        _label(bar, "Cycle Bind", muted=True).grid(row=0, column=3, padx=(14, 6), pady=8)
        self._bind_button = _button(bar, self._bind_button_text(), self._start_bind_capture, width=86)
        self._bind_button.grid(row=0, column=4, padx=4, pady=8)

        self._cycle_button = _button(bar, "Cycle Presets", self._on_manage_cycle, width=112)
        self._cycle_button.grid(row=0, column=5, padx=6, pady=8)
        _button(bar, "Save All", self._on_write, width=92).grid(
            row=0, column=6, padx=(6, 14), pady=8
        )

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._list_buttons.clear()

        crosshairs = self._config.get("crosshairs", {})
        if not crosshairs:
            _label(self._list_frame, "No presets", muted=True).pack(padx=10, pady=12, anchor="w")
            return

        for letter in sorted(crosshairs.keys()):
            label = crosshairs[letter].get("label", letter.upper())
            selected = letter == self._current_letter
            btn = ctk.CTkButton(
                self._list_frame,
                text=f"{letter.upper()}  {label}",
                anchor="w",
                height=24,
                corner_radius=0,
                border_width=1,
                border_color=COLORS["panel_edge"],
                fg_color=COLORS["selected"] if selected else COLORS["control"],
                hover_color=COLORS["control_hover"],
                text_color=COLORS["text"],
                font=("Arial", 10),
                command=lambda l=letter: self._on_select(l),
            )
            btn.pack(padx=6, pady=3, fill="x")
            self._list_buttons[letter] = btn

    def _update_path_label(self):
        path = self._config.get("cs2_cfg_path", "")
        if path:
            display = ("..." + path[-62:]) if len(path) > 65 else path
            self._path_lbl.configure(text=display, text_color=COLORS["text"])
        else:
            self._path_lbl.configure(text="Not set", text_color=COLORS["muted"])

    def _set_current_title(self):
        if not self._current_letter:
            self._letter_lbl.configure(text="-")
            self._title_lbl.configure(text="No preset selected")
            return
        label = self._label_entry.get().strip() or self._current_letter.upper()
        self._letter_lbl.configure(text=self._current_letter.upper())
        self._title_lbl.configure(text=label)

    def _select_all_textbox(self, event):
        event.widget.tag_add("sel", "1.0", "end-1c")
        event.widget.mark_set("insert", "1.0")
        event.widget.see("insert")
        return "break"

    def _command_text(self):
        if self._current_cvars:
            return cfg_writer.command_string(self._current_cvars)
        if self._current_share_code:
            return cfg_writer.command_string(share_code=self._current_share_code)
        return ""

    def _summary_text(self):
        c = self._current_cvars
        if not c:
            return "No crosshair imported."
        color_idx = c.get("cl_crosshaircolor", "-")
        if color_idx == 5:
            color = f"custom {c.get('cl_crosshaircolor_r', '-')}/{c.get('cl_crosshaircolor_g', '-')}/{c.get('cl_crosshaircolor_b', '-')}"
        else:
            color = str(color_idx)
        rows = [
            ("Style", c.get("cl_crosshairstyle", "-")),
            ("Size", c.get("cl_crosshairsize", "-")),
            ("Gap", c.get("cl_crosshairgap", "-")),
            ("Thickness", c.get("cl_crosshairthickness", "-")),
            ("Color", color),
            ("Alpha", c.get("cl_crosshairalpha", "-")),
            ("Dot", "on" if c.get("cl_crosshairdot") else "off"),
            ("Outline", f"on, {c.get('cl_crosshair_outlinethickness', '-')}" if c.get("cl_crosshair_drawoutline") else "off"),
            ("T style", "on" if c.get("cl_crosshair_t") else "off"),
            ("Target ID", "hidden" if c.get("hud_showtargetid") == 0 else "unchanged"),
        ]
        if self._current_share_code:
            rows.insert(0, ("Source", "share code"))
        else:
            rows.insert(0, ("Source", "console cvars"))
        return chr(10).join(f"{name:<10} {value}" for name, value in rows)

    def _refresh_details(self):
        self._summary_box.configure(state="normal")
        self._summary_box.delete("1.0", "end")
        self._summary_box.insert("1.0", self._summary_text())
        self._summary_box.configure(state="disabled")

        self._command_box.configure(state="normal")
        self._command_box.delete("1.0", "end")
        command = self._command_text()
        if command:
            self._command_box.insert("1.0", command)
        self._command_box.configure(state="disabled")

    def _on_copy_command(self):
        command = self._command_text()
        if not command:
            messagebox.showwarning("No Command", "Import or select a crosshair first.")
            return
        self.clipboard_clear()
        self.clipboard_append(command)

    def _on_select(self, letter):
        self._current_letter = letter
        data = self._config["crosshairs"][letter]
        self._current_cvars = dict(data.get("cvars", {}))
        self._current_share_code = data.get("share_code", "")

        self._label_entry.delete(0, "end")
        self._label_entry.insert(0, data.get("label", ""))
        self._hide_targetid.set("hud_showtargetid" in self._current_cvars)
        self._set_current_title()
        self._refresh_list()
        self._refresh_details()

    def _on_add_new(self):
        taken = set(self._config.get("crosshairs", {}).keys())
        next_letter = next((l for l in string.ascii_lowercase if l not in taken), None)
        if next_letter is None:
            messagebox.showinfo("Full", "All 26 letter slots are used.")
            return

        self._current_letter = next_letter
        self._current_cvars = {}
        self._current_share_code = ""
        self._label_entry.delete(0, "end")
        self._paste_box.delete("1.0", "end")
        self._hide_targetid.set(False)
        self._set_current_title()
        self._refresh_list()
        self._refresh_details()

    def _on_import(self):
        text = self._paste_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", 'Paste the output of "find cl_crosshair" first.')
            return

        share_code = xhair_parser.find_share_code(text)
        if share_code:
            try:
                cvars = xhair_parser.decode_share_code(share_code)
            except Exception as exc:
                messagebox.showerror("Share Code Failed", str(exc))
                return
        else:
            cvars = xhair_parser.parse(text)
        if not xhair_parser.is_valid(cvars):
            messagebox.showerror(
                "Parse Failed",
                'Paste a CS2 share code or the full output of "find cl_crosshair" from the CS2 console.',
            )
            return

        cvars.pop("hud_showtargetid", None)
        if self._hide_targetid.get():
            cvars["hud_showtargetid"] = 0

        self._current_share_code = share_code
        self._current_cvars = cvars
        self._refresh_details()

    def _on_targetid_toggle(self):
        if self._current_cvars:
            if self._hide_targetid.get():
                self._current_cvars["hud_showtargetid"] = 0
            else:
                self._current_cvars.pop("hud_showtargetid", None)
        self._refresh_details()

    def _on_save(self):
        if not self._current_letter:
            messagebox.showwarning("Nothing Selected", "Select a preset or click '+ Add' first.")
            return
        if not self._current_cvars and not self._current_share_code:
            messagebox.showwarning("No Data", "Import a crosshair first.")
            return

        label = self._label_entry.get().strip() or self._current_letter.upper()
        data = {"label": label}
        if self._current_share_code:
            data["share_code"] = self._current_share_code
        if self._current_cvars:
            data["cvars"] = dict(self._current_cvars)
        self._config.setdefault("crosshairs", {})[self._current_letter] = data
        config_manager.save(self._config)
        self._set_current_title()
        self._refresh_list()

        if self._config.get("cs2_cfg_path"):
            try:
                out = cfg_writer.write(self._config)
                messagebox.showinfo(
                    "Saved",
                    f"Crosshair {self._current_letter.upper()} saved and written to:\n{out}\n\nReload in CS2 with: exec crosshairs\nThen type in console: cross{self._current_letter}\n\nIf your autoexec has exec crosshairs, exec autoexec also works.",
                )
            except Exception as exc:
                messagebox.showerror("Write Failed", str(exc))
        else:
            messagebox.showinfo(
                "Saved",
                f"Crosshair {self._current_letter.upper()} saved. Set cfg path to auto-write.",
            )


    def _on_delete(self):
        letter = self._current_letter
        if not letter or letter not in self._config.get("crosshairs", {}):
            messagebox.showwarning("Nothing Selected", "Select a saved crosshair to delete.")
            return
        if not messagebox.askyesno("Delete", f"Delete crosshair {letter.upper()}?"):
            return

        del self._config["crosshairs"][letter]
        cycle = self._config.get("cycle_letters", [])
        if letter in cycle:
            cycle.remove(letter)

        self._current_letter = None
        self._current_cvars = {}
        self._current_share_code = ""
        self._label_entry.delete(0, "end")
        self._hide_targetid.set(False)
        config_manager.save(self._config)
        self._set_current_title()
        self._refresh_list()
        self._refresh_details()


    def _bind_button_text(self):
        return self._cycle_bind_value.upper() if self._cycle_bind_value else "Set Bind"

    def _start_bind_capture(self):
        if self._bind_listening:
            return
        self._bind_listening = True
        self._bind_button.configure(text="Press key...", fg_color=COLORS["accent"])
        self.focus_force()
        self.after(80, self._bind_capture_on)

    def _bind_capture_on(self):
        self.bind_all("<KeyPress>", self._capture_key_bind, add="+")
        self.bind_all("<ButtonPress>", self._capture_mouse_bind, add="+")
        self.bind_all("<MouseWheel>", self._capture_wheel_bind, add="+")

    def _bind_capture_off(self):
        self.unbind_all("<KeyPress>")
        self.unbind_all("<ButtonPress>")
        self.unbind_all("<MouseWheel>")
        self._bind_listening = False
        self._bind_button.configure(
            text=self._bind_button_text(),
            fg_color=COLORS["control"],
        )

    def _set_cycle_bind(self, value):
        self._cycle_bind_value = value
        self._config["cycle_bind"] = value
        config_manager.save(self._config)

    def _capture_key_bind(self, event):
        key = self._event_to_bind_name(event)
        if key == "escape":
            self._bind_capture_off()
            return "break"
        if key in {"backspace", "delete"}:
            self._set_cycle_bind("")
            self._bind_capture_off()
            return "break"
        if key:
            self._set_cycle_bind(key)
            self._bind_capture_off()
        return "break"

    def _capture_mouse_bind(self, event):
        mapping = {1: "mouse1", 2: "mouse3", 3: "mouse2", 4: "mwheelup", 5: "mwheeldown"}
        button = mapping.get(getattr(event, "num", None))
        if button:
            self._set_cycle_bind(button)
            self._bind_capture_off()
        return "break"

    def _capture_wheel_bind(self, event):
        self._set_cycle_bind("mwheelup" if event.delta > 0 else "mwheeldown")
        self._bind_capture_off()
        return "break"

    def _event_to_bind_name(self, event):
        keysym = str(event.keysym or "").lower()
        char = str(event.char or "").lower()
        special = {
            " ": "space",
            "space": "space",
            "return": "enter",
            "escape": "escape",
            "backspace": "backspace",
            "delete": "delete",
            "tab": "tab",
            "shift_l": "shift",
            "shift_r": "shift",
            "control_l": "ctrl",
            "control_r": "ctrl",
            "alt_l": "alt",
            "alt_r": "alt",
            "super_l": "win",
            "super_r": "win",
            "caps_lock": "capslock",
            "prior": "pgup",
            "next": "pgdn",
            "insert": "ins",
            "home": "home",
            "end": "end",
            "up": "uparrow",
            "down": "downarrow",
            "left": "leftarrow",
            "right": "rightarrow",
        }
        if keysym in special:
            return special[keysym]
        if keysym.startswith("f") and keysym[1:].isdigit():
            return keysym
        if char and char in string.ascii_lowercase + string.digits:
            return char
        if len(keysym) == 1 and keysym in string.ascii_lowercase + string.digits:
            return keysym
        return ""

    def _on_change_path(self):
        path = filedialog.askdirectory(title="Select CS2 cfg folder")
        if path:
            self._config["cs2_cfg_path"] = path
            config_manager.save(self._config)
            self._update_path_label()

    def _on_write(self):
        self._config["cycle_bind"] = self._cycle_bind_value.strip()
        self._ensure_cycle_defaults()
        config_manager.save(self._config)

        if not self._config.get("cs2_cfg_path"):
            messagebox.showerror("No Path Set", "Set your CS2 cfg folder path first.")
            return
        if not self._config.get("crosshairs"):
            messagebox.showwarning("Empty Library", "Save at least one crosshair before writing.")
            return

        try:
            out = cfg_writer.write(self._config)
            messagebox.showinfo(
                "Saved + Written",
                f"All presets saved and written to:\n{out}\n\nReload in CS2 with: exec crosshairs\n\nIf your autoexec has exec crosshairs, exec autoexec also works.",
            )
        except Exception as exc:
            messagebox.showerror("Write Failed", str(exc))

    def _ensure_cycle_defaults(self):
        crosshairs = self._config.get("crosshairs", {})
        current = [letter for letter in self._config.get("cycle_letters", []) if letter in crosshairs]
        if not current:
            self._config["cycle_letters"] = sorted(crosshairs.keys())
        else:
            self._config["cycle_letters"] = current

    def _select_first_saved(self):
        crosshairs = self._config.get("crosshairs", {})
        if crosshairs and self._current_letter is None:
            self._on_select(sorted(crosshairs.keys())[0])

    def _on_manage_cycle(self):
        if self._cycle_dialog is not None:
            try:
                if self._cycle_dialog.winfo_exists():
                    self._cycle_dialog.focus_force()
                    self._cycle_dialog.lift()
                    return
            except tk.TclError:
                self._cycle_dialog = None

        self._ensure_cycle_defaults()
        if self._cycle_button is not None:
            self._cycle_button.configure(state="disabled")

        self._cycle_dialog = CycleDialog(
            self,
            self._config,
            callback=self._save_cycle,
            on_close=self._clear_cycle_dialog,
        )

    def _clear_cycle_dialog(self):
        self._cycle_dialog = None
        if self._cycle_button is not None:
            self._cycle_button.configure(state="normal")

    def _save_cycle(self, letters):
        self._config["cycle_letters"] = letters
        config_manager.save(self._config)

    def _auto_detect_path(self):
        if not self._config.get("cs2_cfg_path"):
            detected = config_manager.detect_cs2_path()
            if detected:
                self._config["cs2_cfg_path"] = detected
                config_manager.save(self._config)
        self._update_path_label()


class CycleDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, callback, on_close):
        super().__init__(parent)

        self.title("Cycle Presets")
        self.geometry("320x380")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["window"])
        self.transient(parent)
        self.focus_force()

        self._callback = callback
        self._on_close = on_close
        self._vars = {}
        self.protocol("WM_DELETE_WINDOW", self._close)

        _label(self, "Cycle presets", bold=True, size=14).pack(padx=12, pady=(12, 2), anchor="w")
        _label(self, "Checked presets rotate with the cycle bind.", muted=True).pack(padx=12, pady=(0, 8), anchor="w")

        scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["panel_edge"],
        )
        scroll.pack(padx=12, pady=4, fill="both", expand=True)

        crosshairs = config.get("crosshairs", {})
        cycle = [letter for letter in config.get("cycle_letters", []) if letter in crosshairs]
        if not cycle:
            cycle = sorted(crosshairs.keys())
        if not crosshairs:
            _label(scroll, "No presets", muted=True).pack(padx=10, pady=12, anchor="w")
        for letter in sorted(crosshairs.keys()):
            label = crosshairs[letter].get("label", letter.upper())
            var = tk.BooleanVar(value=letter in cycle)
            self._vars[letter] = var
            ctk.CTkCheckBox(
                scroll,
                text=f"{letter.upper()}  {label}",
                variable=var,
                corner_radius=0,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["text"],
            ).pack(padx=10, pady=5, anchor="w")

        _button(self, "Save", self._on_save, width=80).pack(pady=10)

    def _on_save(self):
        selected = [letter for letter, var in sorted(self._vars.items()) if var.get()]
        self._callback(selected)
        self._close()

    def _close(self):
        self.destroy()
        self._on_close()


if __name__ == "__main__":
    app = App()
    app.mainloop()
