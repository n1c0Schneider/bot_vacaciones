# Bot de Gestión de Vacaciones — TPI Organización Empresarial

Chatbot de Telegram que automatiza el proceso de solicitud de vacaciones,
reemplazando el flujo manual de formularios y planillas físicas.

Desarrollado por Nico y Leo — UTN TUP Organización Empresarial 2025.

---

## Requisitos

- Python 3.10 o superior
- Cuenta de Telegram
- Token de bot generado con @BotFather

---

## Instalación

### 1. Clonar el repositorio

git clone https://github.com/n1c0Schneider/bot_vacaciones.git
cd bot_vacaciones

### 2. Crear y activar el entorno virtual

Windows:
python -m venv venv
venv\Scripts\activate

Linux/Mac:
python3 -m venv venv
source venv/bin/activate

### 3. Instalar dependencias

pip install -r requirements.txt

### 4. Configurar el TOKEN

Crear un archivo .env en la raiz del proyecto con el siguiente contenido:

TELEGRAM_TOKEN= token

El token lo genera @BotFather en Telegram al crear un nuevo bot.
NUNCA subir el archivo .env al repositorio.

### 5. Ejecutar el bot

python bot/main.py

Si ves "Bot corriendo..." en la terminal, el bot está activo.

---

## Uso

Abrí Telegram, buscá tu bot por username y mandá /start.
El bot te guía paso a paso por el proceso de solicitud.

Comandos disponibles:
- /start — inicia una nueva solicitud de vacaciones
- /cancelar — cancela la operación en cualquier momento

---

## Estructura del proyecto

bot_vacaciones/
├── bot/
│   └── main.py          # Código principal del bot
├── datos/
│   └── empleados.csv    # Base de datos simulada
├── docs/
│   ├── AS-IS.jpg        # Diagrama proceso manual
│   └── TO-BE.jpg        # Diagrama proceso automatizado
├── .env                 # TOKEN del bot (no se sube al repo)
├── .gitignore
├── README.md
└── requirements.txt

---

## Base de datos simulada

El archivo datos/empleados.csv contiene los empleados registrados con los
siguientes campos: DNI, nombre, dias_disponibles, dias_tomados, solicitud_pendiente.

Para agregar empleados simplemente editá el CSV con cualquier editor de texto
o Excel respetando el formato existente.

---

## Flujo del bot

1. El empleado inicia la conversación con /start
2. El bot solicita el DNI
3. Se valida el DNI contra el CSV
4. Se verifica el saldo de días disponibles
5. Se solicita fecha de inicio y cantidad de días
6. Se valida disponibilidad y formato
7. El empleado confirma la solicitud
8. El sistema registra y actualiza el CSV

---

## Errores manejados

- DNI con letras o caracteres inválidos
- DNI no registrado en el sistema (máximo 3 intentos)
- Empleado sin saldo de días disponibles
- Empleado con solicitud pendiente activa
- Formato de fecha incorrecto
- Fecha en el pasado
- Cantidad de días mayor al saldo disponible
- Respuesta inválida en la confirmación