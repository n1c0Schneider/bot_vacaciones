# Bot de Gestión de Vacaciones — TPI Organización Empresarial

Chatbot de Telegram que automatiza el proceso de solicitud de vacaciones,
reemplazando el flujo manual de formularios y planillas físicas.

El sistema permite validar la identidad del empleado mediante DNI, consultar su saldo
de dias disponibles, solicitar fecha de inicio y cantidad de dias, calcular automaticamente
la fecha de finalizacion y registrar la solicitud en archivos CSV como base de datos simulada.

Desarrollado por Nico y Leo — UTN TUP Organización Empresarial 2026.

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
│   ├── empleados.csv    # Base de datos simulada
|   └── solicitudes.csv  # Historial de solicitudes registradas
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

El archivo solicitudes.csv registra las solicitudes aprobadas por el bot.
campos: dni, nombre, fecha_inicio, fecha_fin, dias_solicitados, estado.

---

## Flujo normal de uso
|  1  | El empleado inicia la conversacion con /start.
|  2  | El bot solicita el DNI.
|  3  | El empleado ingresa su DNI usando solo numeros.
|  4  | El bot valida el DNI contra el archivo empleados.csv .
|  5  | Si el empleado existe, no tiene solicitud pendiente y posee saldo disponible, el bot solicita la fecha de inicio.
|  6  | El empleado ingresa la fecha de inicio en formato DD/MM/AAAA.
|  7  | El bot solicita la cantidad de dias de vacaciones.
|  8  | El empleado ingresa la cantidad de dias solicitados.
|  9  | El bot valida que los dias solicitados no superen el saldo disponible.
|  10 | El bot calcula automaticamente la fecha de finalizacion.
|  11 | El bot muestra un resumen de la solicitud.
|  12 | El empleado confirma con SI o cancela con NO.
|  13 | Si confirma, el sistema actualiza empleados.csv y registra la solicitud en solicitudes.csv .

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