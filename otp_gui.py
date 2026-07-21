"""
OTP Authenticator - requer: pip install customtkinter

Build (PyInstaller):
    pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter otp_gui.py
"""
import hashlib
import base64
import struct
import hmac
import time
import json
import re
import sys
import os
import tkinter as tk
import customtkinter as ctk


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = get_app_dir()
DB_FILE = os.path.join(APP_DIR, 'emails.json')
PERIOD = 30
DIGITS = 6
WIN_W, WIN_H = 800, 600
CARD_H = 72
RADIUS = 14
LOG_MAX_LINES = 200
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

BG = '#13141c'
BG_CARD = '#1c1e2b'
BG_CARD_HOVER = '#22243a'
BG_LOG = '#181923'
SHADOW = '#0a0a10'
FG = '#f1f1f6'
FG_DIM = '#8b8da3'
FG_DIMMER = '#5f6178'
ACCENT = '#7c5cff'
DANGER = '#ff5c7a'
SUCCESS = '#4ade80'
BORDER = '#2a2c3d'

OTP_FONT = ('JetBrains Mono', 19, 'bold')
LOG_FONT = ('Consolas', 9)

SERVICE_ICONS = {
    'gmail.com': ('G', '#ea4335'),
    'outlook.com': ('O', '#0078d4'),
    'live.com': ('O', '#0078d4'),
    'hotmail.com': ('H', '#0078d4'),
    'yahoo.com': ('Y', '#6001d2'),
    'icloud.com': ('I', '#3693f3'),
    'steampowered.com': ('S', '#1b2838'),
    'steamcommunity.com': ('S', '#1b2838'),
    'discord.com': ('D', '#5865f2'),
    'github.com': ('G', '#333333'),
}
SERVICE_NAMES = {
    'gmail.com': 'Gmail', 'outlook.com': 'Outlook', 'live.com': 'Outlook',
    'hotmail.com': 'Hotmail', 'yahoo.com': 'Yahoo', 'icloud.com': 'iCloud',
    'steampowered.com': 'Steam', 'steamcommunity.com': 'Steam',
    'discord.com': 'Discord', 'github.com': 'GitHub',
}

ctk.set_appearance_mode('dark')


def load_emails():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_emails(emails):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)


def domain_of(email):
    return email.split('@')[-1].lower()


def service_name(email):
    return SERVICE_NAMES.get(domain_of(email), domain_of(email))


def service_icon(email):
    return SERVICE_ICONS.get(domain_of(email), (email[0].upper(), ACCENT))


def generate_secret_key(email):
    sha256_hash = hashlib.sha256(email.lower().encode()).digest()
    return base64.b32encode(sha256_hash).decode()[:16]


def generate_totp(secret, digits=DIGITS, period=PERIOD, timestamp=None):
    key = base64.b32decode(secret.upper() + '=' * ((8 - len(secret) % 8) % 8))
    counter = int((timestamp if timestamp is not None else time.time()) // period)
    msg = struct.pack('>Q', counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack('>I', h[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def lerp_hex(c1, c2, t):
    c1, c2 = c1.lstrip('#'), c2.lstrip('#')
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f'#{r:02x}{g:02x}{b:02x}'


class Row:
    """Card de linha: sombra + card arredondado, hover sem flicker, progresso e log."""

    def __init__(self, parent, app, email):
        self.app = app
        self.email = email
        self._hover_job = None
        self._hovered = False

        self.wrap = ctk.CTkFrame(parent, fg_color='transparent', height=CARD_H + 4)
        self.wrap.pack(fill='x', pady=(0, 10))
        self.wrap.pack_propagate(False)

        self.shadow = ctk.CTkFrame(self.wrap, width=10, height=CARD_H,
                                    corner_radius=RADIUS, fg_color=SHADOW)
        self.shadow.place(x=4, y=4)

        self.card = ctk.CTkFrame(self.wrap, width=10, height=CARD_H, corner_radius=RADIUS,
                                  fg_color=BG_CARD, border_width=1, border_color=BORDER)
        self.card.place(x=0, y=0)
        self.wrap.bind('<Configure>', self._on_resize)

        letter, color = service_icon(email)
        icon = ctk.CTkLabel(self.card, text=letter, width=42, height=42, corner_radius=21,
                             fg_color=color, text_color='#ffffff',
                             font=('Segoe UI Semibold', 15))
        icon.place(x=14, rely=0.5, anchor='w')

        text_x = 68
        lbl_email = ctk.CTkLabel(self.card, text=email, text_color=FG, fg_color='transparent',
                                  font=('Segoe UI Semibold', 11), anchor='w')
        lbl_email.place(x=text_x, rely=0.32, anchor='w')
        lbl_service = ctk.CTkLabel(self.card, text=service_name(email), text_color=FG_DIM,
                                    fg_color='transparent', font=('Segoe UI', 9), anchor='w')
        lbl_service.place(x=text_x, rely=0.62, anchor='w')

        self.kebab = ctk.CTkLabel(self.card, text='\u22ee', text_color=FG_DIM, fg_color='transparent',
                                   font=('Segoe UI', 14), cursor='hand2')
        self.kebab.place(relx=1.0, x=-14, rely=0.5, anchor='e')
        self.kebab.bind('<Button-1>', self.on_remove)

        self.expira_lbl = ctk.CTkLabel(self.card, text=f'{PERIOD}s', text_color=FG_DIMMER,
                                        fg_color='transparent', font=('Segoe UI', 9))
        self.expira_lbl.place(relx=1.0, x=-44, rely=0.66, anchor='e')

        self.otp_lbl = ctk.CTkLabel(self.card, text='------', text_color=FG, fg_color='transparent',
                                     font=OTP_FONT, cursor='hand2')
        self.otp_lbl.place(relx=1.0, x=-44, rely=0.32, anchor='e')

        self.progress = ctk.CTkProgressBar(self.card, width=150, height=5, corner_radius=3,
                                            fg_color=BORDER, progress_color=ACCENT)
        self.progress.place(relx=1.0, x=-44, rely=0.62, anchor='e')
        self.progress.set(1.0)

        clickable = (self.card, self.otp_lbl, self.progress)
        for w in clickable:
            w.bind('<Button-1>', self.on_copy)

        hover_targets = (self.card, icon, lbl_email, lbl_service, self.kebab,
                          self.expira_lbl, self.otp_lbl, self.progress)
        for w in hover_targets:
            w.bind('<Enter>', self.on_enter)
            w.bind('<Leave>', self.on_leave)

    def _on_resize(self, event):
        w = event.width - 4
        if w > 0:
            self.shadow.configure(width=w)
            self.card.configure(width=w)

    # ---------- hover sem flicker (debounce por posição do ponteiro) ----------
    def on_enter(self, _e=None):
        if not self._hovered:
            self._hovered = True
            self._animate_hover(BG_CARD, BG_CARD_HOVER)

    def on_leave(self, _e=None):
        self.card.after(40, self._check_leave)

    def _check_leave(self):
        if not self.card.winfo_exists():
            return
        x, y = self.card.winfo_pointerxy()
        widget = self.card.winfo_containing(x, y)
        if not self._is_descendant(widget):
            self._hovered = False
            self._animate_hover(BG_CARD_HOVER, BG_CARD)

    def _is_descendant(self, widget):
        while widget is not None:
            if widget == self.card:
                return True
            widget = widget.master
        return False

    def _animate_hover(self, c_from, c_to, step=0):
        if self._hover_job:
            self.card.after_cancel(self._hover_job)
            self._hover_job = None
        if not self.card.winfo_exists():
            return
        steps = 6
        self.card.configure(fg_color=lerp_hex(c_from, c_to, step / steps))
        if step < steps:
            self._hover_job = self.card.after(12, lambda: self._animate_hover(c_from, c_to, step + 1))

    # ---------- ações ----------
    def on_remove(self, _event=None):
        self.app.remove_email(self.email)

    def on_copy(self, event):
        otp = self.otp_lbl.cget('text')
        self.app.clipboard_clear()
        self.app.clipboard_append(otp)
        self.app.update_idletasks()
        self._ripple()
        self.app.show_toast(event.x_root, event.y_root, f'Copiado: {otp}')
        self.app.log(f'Copiado {otp} ({self.email})', SUCCESS)

    def _ripple(self, step=0):
        if not self.card.winfo_exists():
            return
        steps = 5
        if step == 0:
            self.card.configure(border_color=ACCENT)
        if step >= steps:
            self.card.configure(border_color=BORDER)
            return
        self.card.after(40, lambda: self._ripple(step + 1))

    def update_otp(self, now):
        secret = generate_secret_key(self.email)
        otp = generate_totp(secret, timestamp=now)
        remaining = PERIOD - int(now) % PERIOD
        frac = remaining / PERIOD
        self.otp_lbl.configure(text=otp)
        self.expira_lbl.configure(text=f'{remaining}s')
        self.progress.set(frac)
        self.progress.configure(progress_color=ACCENT if frac > 0.2 else DANGER)

    def destroy(self):
        self.wrap.destroy()


class OTPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.geometry(f'{WIN_W}x{WIN_H}+{(self.winfo_screenwidth() - WIN_W) // 2}'
                       f'+{(self.winfo_screenheight() - WIN_H) // 2}')
        self.configure(fg_color=BG)

        self.emails = load_emails()
        self.rows = {}
        self._toast = None
        self._drag = (0, 0)

        self._build_titlebar()
        self._build_header()
        self._build_form()
        self._build_log()
        self._build_list()

        self.refresh_list()
        self.log('Aplicativo iniciado')
        self.tick()

    # ---------- titlebar custom ----------
    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=BG, height=32, corner_radius=0)
        bar.pack(fill='x')
        bar.pack_propagate(False)

        close_btn = ctk.CTkButton(bar, text='\u2715', width=46, height=32, corner_radius=0,
                                   fg_color='transparent', hover_color=DANGER,
                                   text_color=FG_DIM, font=('Segoe UI', 11),
                                   command=self.destroy)
        close_btn.pack(side='right')

        bar.bind('<Button-1>', self._drag_start)
        bar.bind('<B1-Motion>', self._drag_move)

    def _drag_start(self, event):
        self._drag = (event.x, event.y)

    def _drag_move(self, event):
        x = self.winfo_pointerx() - self._drag[0]
        y = self.winfo_pointery() - self._drag[1]
        self.geometry(f'+{x}+{y}')

    # ---------- header ----------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.pack(fill='x', padx=28, pady=(14, 10))
        ctk.CTkLabel(header, text='OTP Authenticator', text_color=FG, fg_color='transparent',
                      font=('Segoe UI Semibold', 20), anchor='w').pack(fill='x')
        ctk.CTkLabel(header, text='Gerencie seus códigos de autenticação com segurança',
                      text_color=FG_DIM, fg_color='transparent',
                      font=('Segoe UI', 10), anchor='w').pack(fill='x')

    # ---------- form ----------
    def _build_form(self):
        form = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        form.pack(fill='x', padx=28, pady=(0, 16))
        form.columnconfigure(0, weight=1)

        self.email_var = tk.StringVar()
        entry = ctk.CTkEntry(form, textvariable=self.email_var, height=40, corner_radius=12,
                              fg_color=BG_CARD, border_color=BORDER, border_width=1,
                              text_color=FG, placeholder_text='Cole o código ou nome do serviço',
                              font=('Segoe UI', 11))
        entry.grid(row=0, column=0, sticky='ew')
        entry.bind('<Return>', lambda e: self.add_email())
        self._entry = entry

        add_btn = ctk.CTkButton(form, text='+  Adicionar', height=40, width=130, corner_radius=12,
                                 fg_color=ACCENT, hover_color='#6a4ce0', text_color='#ffffff',
                                 font=('Segoe UI Semibold', 11), command=self.add_email)
        add_btn.grid(row=0, column=1, padx=(10, 0))

    # ---------- lista ----------
    def _build_list(self):
        hdr = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        hdr.pack(fill='x', padx=28)
        ctk.CTkLabel(hdr, text='SERVIÇO / E-MAIL', text_color=FG_DIMMER, fg_color='transparent',
                      font=('Segoe UI', 8, 'bold')).pack(anchor='w')

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        self.list_frame.pack(fill='both', expand=True, padx=24, pady=(8, 8))

    # ---------- barra de log ----------
    def _build_log(self):
        # empacotado antes da lista mas fixado no rodapé via pack(side='bottom')
        wrap = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        wrap.pack(side='bottom', fill='x', padx=28, pady=(0, 12))

        ctk.CTkLabel(wrap, text='ATIVIDADE', text_color=FG_DIMMER, fg_color='transparent',
                      font=('Segoe UI', 8, 'bold'), anchor='w').pack(fill='x', pady=(0, 4))

        self.log_box = ctk.CTkTextbox(wrap, height=76, corner_radius=10, fg_color=BG_LOG,
                                       text_color=FG_DIM, font=LOG_FONT, border_width=1,
                                       border_color=BORDER, activate_scrollbars=True)
        self.log_box.pack(fill='x')
        self.log_box.configure(state='disabled')

    def log(self, message, color=None):
        ts = time.strftime('%H:%M:%S')
        line = f'[{ts}] {message}\n'
        self.log_box.configure(state='normal')
        self.log_box.insert('end', line)
        # limita histórico exibido
        total_lines = int(self.log_box.index('end-1c').split('.')[0])
        if total_lines > LOG_MAX_LINES:
            self.log_box.delete('1.0', f'{total_lines - LOG_MAX_LINES}.0')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    # ---------- toast (balão sem botão) ----------
    def show_toast(self, x_root, y_root, text):
        if self._toast is not None:
            self._toast.destroy()
            self._toast = None

        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        try:
            toast.attributes('-alpha', 0.0)
        except tk.TclError:
            pass

        ctk.CTkLabel(toast, text=text, fg_color=ACCENT, text_color='#ffffff',
                      corner_radius=10, font=('Segoe UI Semibold', 9), padx=12, pady=6).pack()

        toast.update_idletasks()
        w, h = toast.winfo_width(), toast.winfo_height()
        toast.geometry(f'+{x_root - w // 2}+{y_root - h - 14}')

        self._toast = toast
        self._fade(toast, 0.0, 0.15, 0.95)
        self.after(1400, lambda: self._fade(toast, 0.95, -0.15, 0.0, on_done=self._clear_toast))

    def _clear_toast(self, toast):
        if self._toast is toast:
            self._toast = None
        if toast.winfo_exists():
            toast.destroy()

    def _fade(self, toast, alpha, step, target, on_done=None):
        if not toast.winfo_exists():
            return
        alpha += step
        done = (step > 0 and alpha >= target) or (step < 0 and alpha <= target)
        alpha = target if done else alpha
        try:
            toast.attributes('-alpha', max(alpha, 0.0))
        except tk.TclError:
            return
        if done:
            if on_done:
                on_done(toast)
            return
        self.after(15, lambda: self._fade(toast, alpha, step, target, on_done))

    # ---------- crud ----------
    def add_email(self):
        email = self.email_var.get().strip().lower()
        if not email or not EMAIL_RE.match(email):
            self.show_toast(self.winfo_rootx() + WIN_W // 2, self.winfo_rooty() + 200, 'Email inválido')
            self.log(f'Tentativa inválida: "{email}"', DANGER)
            return
        if any(e['email'] == email for e in self.emails):
            self.show_toast(self.winfo_rootx() + WIN_W // 2, self.winfo_rooty() + 200, 'Email já cadastrado')
            self.log(f'Já cadastrado: {email}', DANGER)
            return
        self.emails.append({'email': email})
        save_emails(self.emails)
        self.email_var.set('')
        self._entry.focus_set()
        self.refresh_list()
        self.log(f'Adicionado: {email}', SUCCESS)

    def remove_email(self, email):
        self.emails = [e for e in self.emails if e['email'] != email]
        save_emails(self.emails)
        self.refresh_list()
        self.log(f'Removido: {email}', DANGER)

    def refresh_list(self):
        for row in self.rows.values():
            row.destroy()
        self.rows = {}
        for e in self.emails:
            row = Row(self.list_frame, self, e['email'])
            self.rows[e['email']] = row

    def tick(self):
        now = time.time()
        for row in self.rows.values():
            row.update_otp(now)
        self.after(1000, self.tick)


if __name__ == '__main__':
    OTPApp().mainloop()