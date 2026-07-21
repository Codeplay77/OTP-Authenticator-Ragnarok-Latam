# OTP-Authenticator-Ragnarok-Latam

Um autenticador OTP (One-Time Password) desenvolvido em Python para gerar os códigos utilizados pelo servidor **Ragnarok Online LATAM**.
O aplicativo possui uma interface moderna desenvolvida com **CustomTkinter**, permitindo gerenciar múltiplas contas e copiar rapidamente os códigos OTP.
> Este projeto é independente e não possui qualquer vínculo com a Gravity, WarpPortal BR ou os responsáveis pelo Ragnarok Online LATAM.

---

## Recursos

- Interface moderna em modo escuro
- Gerenciamento de múltiplas contas
- Geração automática de códigos OTP
- Atualização em tempo real (30 segundos)
- Copiar OTP com um clique
- Barra de progresso indicando o tempo restante
- Armazenamento automático das contas em `emails.json`
- Executável standalone utilizando PyInstaller

---

## Requisitos

- Python 3.10+
- Windows 10 ou superior

Instale as dependências:

```bash
pip install customtkinter
```

---

## Executando

```bash
python otp_gui.py
```

---

## Gerando o executável

```bash
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter otp_gui.py
```

ou

```bash
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --collect-all customtkinter ^
    otp_gui.py
```

O executável será criado em:

```
dist/
└── otp_gui.exe
```

---

## Estrutura

```
.
├── otp_gui.py
├── emails.json
├── README.md
└── docs/
    └── screenshot.png
```

---

## Como funciona

Para cada endereço de e-mail cadastrado, o aplicativo:

1. Gera uma chave secreta determinística baseada no SHA-256 do e-mail.
2. Converte essa chave para Base32.
3. Calcula o código TOTP utilizando HMAC-SHA1.
4. Atualiza automaticamente o código a cada 30 segundos.

Os e-mails cadastrados são armazenados em:

```
emails.json
```

localizado na mesma pasta do executável.

---

## Tecnologias

- Python
- CustomTkinter
- Tkinter
- HMAC
- SHA-256
- Base32
- PyInstaller

---

## Aviso

Este projeto foi desenvolvido para auxiliar jogadores do Ragnarok Online LATAM na geração dos códigos OTP compatíveis com o servidor.

Não armazena senhas, tokens ou informações sensíveis além dos e-mails cadastrados localmente.

---

## Licença

MIT License
