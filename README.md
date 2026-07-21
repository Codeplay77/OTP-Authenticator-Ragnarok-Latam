# OTP Authenticator Ragnarok Latam

Autenticador OTP (One-Time Password) para Ragnarok Latam.

## Recursos

- Interface moderna e responsiva com CustomTkinter
- Geração de códigos TOTP para cada conta
- Barra de progresso visual com contagem regressiva
- Log de atividades em tempo real
- Design escuro com tema profissional

## Instalação

### Pré-requisitos

- Python 3.9+
- Pip

### Passos

```bash
# Clone o repositório
git clone https://github.com/Codeplay77/OTP-Authenticator-Ragnarok-Latam.git

# Navegue até o diretório
cd OTP-Authenticator-Ragnarok-Latam

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
python otp_gui.py
```

## Compilação (PyInstaller)

### Requisitos

- Python 3.11
- PyInstaller

### Windows x64

```bash
python -m PyInstaller --icon=favicon.ico --noconfirm --onefile --windowed --collect-all customtkinter otp_gui.py
```

### Windows x86 (32-bit)

```bash
python -m PyInstaller --icon=favicon.ico --noconfirm --onefile --windowed --collect-all customtkinter otp_gui.py
```

## Uso

1. Cole o código OTP no campo de texto
2. Clique em "Adicionar" ou pressione Enter
3. O código OTP será gerado automaticamente a cada 30 segundos
4. Clique no código para copiá-lo para a área de transferência

## Tecnologias

- Python 3.11
- CustomTkinter (interface gráfica)
- TOTP (RFC 6238)
- PyInstaller (compilação)

## Licença

Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
