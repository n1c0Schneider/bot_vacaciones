import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ── Carga las variables del archivo .env al entorno del sistema ────────────────
# Esto permite leer el TOKEN sin escribirlo directamente en el codigo.
# Si alguien ve el codigo, no ve el TOKEN. Solo lo tiene quien tiene el .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# ── Ruta al CSV usando la ubicacion relativa al archivo actual ─────────────────
# __file__ es la ruta de main.py. Subimos un nivel con ".." y entramos a datos/
# Asi funciona sin importar desde donde se ejecute el script
RUTA_CSV = os.path.join(os.path.dirname(__file__), "..", "datos", "empleados.csv")
RUTA_SOLICITUDES = os.path.join(os.path.dirname(__file__), "..", "datos", "solicitudes.csv")

# ── Definicion de los estados de la maquina de estados ────────────────────────
# Son simplemente numeros enteros. El ConversationHandler los usa para saber
# en que paso del flujo esta cada usuario en cada momento.
# Cada numero representa una etapa distinta de la conversacion.
ESPERANDO_DNI   = 1   # el bot espera que el usuario ingrese su DNI
ESPERANDO_FECHA = 2   # el bot espera la fecha de inicio de vacaciones
ESPERANDO_DIAS  = 3   # el bot espera la cantidad de dias solicitados
CONFIRMANDO     = 4   # el bot espera un SI o NO para confirmar

# Cantidad maxima de intentos de DNI antes de bloquear la solicitud
MAX_INTENTOS_DNI = 3


# ==============================================================================
# FUNCIONES AUXILIARES
# Estas funciones no manejan mensajes de Telegram directamente.
# Son herramientas que usan las funciones principales para no repetir codigo.
# ==============================================================================

def cargar_empleados():
    """
    Lee el archivo CSV y lo devuelve como un DataFrame de pandas.
    Un DataFrame es como una tabla de Excel en memoria: tiene filas, columnas,
    y se puede filtrar, modificar y guardar facilmente.
    """
    return pd.read_csv(RUTA_CSV)


def guardar_empleados(df):
    """
    Recibe un DataFrame modificado y lo escribe de vuelta al CSV.
    index=False evita que pandas agregue una columna extra con numeros de fila.
    """
    df.to_csv(RUTA_CSV, index=False)


def buscar_empleado(dni: str):
    """
    Busca un empleado por DNI en el CSV.
    Devuelve la fila como un objeto Series si lo encuentra, o None si no existe.

    La logica es:
    1. Cargar todo el CSV como DataFrame
    2. Filtrar las filas donde la columna 'dni' coincide con el DNI buscado
    3. Si el resultado esta vacio, devolver None
    4. Si encontro algo, devolver la primera (y unica) fila
    """
    df = cargar_empleados()
    resultado = df[df["dni"] == int(dni)]
    if resultado.empty:
        return None
    return resultado.iloc[0]  # iloc[0] = primera fila del resultado


def validar_fecha(texto: str):
    """
    Intenta convertir un texto al formato de fecha DD/MM/AAAA.
    Si el formato es correcto devuelve un objeto datetime.
    Si es incorrecto devuelve None.

    strptime significa 'string parse time': convierte texto a fecha.
    Si el texto no coincide con el formato, lanza una excepcion ValueError
    que capturamos con except para devolver None en lugar de romper el programa.
    """
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return None

def calcular_fecha_fin(fecha_inicio_texto: str, dias_solicitados: int):
    """
    Calcula la fecha de finalizacion de las vacaciones.
    Se resta 1 dia porque el primer dia solicitado cuenta como dia de vacaciones.
    Ejemplo: inicio 10/07/2025 + 5 dias = finaliza 14/07/2025.
    """
    fecha_inicio = datetime.strptime(fecha_inicio_texto, "%d/%m/%Y")
    fecha_fin = fecha_inicio + timedelta(days=dias_solicitados - 1)
    return fecha_fin.strftime("%d/%m/%Y")

def registrar_solicitud(empleado, fecha_inicio, fecha_fin, dias_solicitados, estado):
    """
    Registra la solicitud de vacaciones en un CSV separado.
    Si el archivo no existe, crea el encabezado automaticamente.
    """
    existe_archivo = os.path.exists(RUTA_SOLICITUDES)
    
    nueva_solicitud = pd.DataFrame([{
        "dni": empleado["dni"],
        "nombre": empleado["nombre"],
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias_solicitados": dias_solicitados,
        "estado": estado
    }])
    
    nueva_solicitud.to_csv(
        RUTA_SOLICITUDES,
        mode="a",
        index=False,
        header=not existe_archivo
    )

# ==============================================================================
# MANEJADORES DE MENSAJES (HANDLERS)
# Cada funcion corresponde a un paso del diagrama TO-BE.
# Todas son 'async' porque Telegram trabaja de forma asincronica:
# el bot puede atender a multiples usuarios al mismo tiempo sin bloquearse.
#
# Parametros que reciben todas:
#   update  — contiene el mensaje que mando el usuario
#   context — contiene datos del bot y del usuario (como user_data)
# ==============================================================================

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta cuando el usuario manda /start.
    Resetea el contador de intentos y pide el DNI.
    Devuelve ESPERANDO_DNI para indicarle al ConversationHandler
    que el proximo mensaje del usuario debe ir a la funcion recibir_dni().
    """
    context.user_data["intentos_dni"] = 0
    await update.message.reply_text(
        "Bienvenido al sistema de solicitud de vacaciones.\n\n"
        "Por favor ingresa tu DNI (solo numeros):"
    )
    return ESPERANDO_DNI


async def recibir_dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe el DNI ingresado por el usuario y lo valida.
    Este paso implementa dos gateways del TO-BE:
      - Gateway 1: DNI valido o invalido
      - Gateway 2: tiene saldo o no tiene saldo

    Caminos infelices manejados:
      - DNI con letras o caracteres especiales
      - DNI que no existe en el CSV
      - Mas de 3 intentos fallidos consecutivos
      - Empleado sin saldo de dias disponibles
      - Empleado con solicitud pendiente activa

    Si todo esta bien guarda los datos del empleado en context.user_data
    y avanza al siguiente estado: ESPERANDO_FECHA.
    """
    texto = update.message.text.strip()

    # Validacion: el DNI debe ser solo numeros
    # isdigit() devuelve True si todos los caracteres son digitos
    if not texto.isdigit():
        await update.message.reply_text(
            "El DNI debe contener solo numeros. Intenta de nuevo:"
        )
        return ESPERANDO_DNI  # se queda en el mismo estado, no avanza

    # Busqueda del empleado en el CSV
    empleado = buscar_empleado(texto)

    # Camino infeliz: DNI no encontrado
    if empleado is None:
        context.user_data["intentos_dni"] += 1
        intentos = context.user_data["intentos_dni"]

        # Si supero el maximo de intentos, termina la conversacion
        if intentos >= MAX_INTENTOS_DNI:
            await update.message.reply_text(
                "Demasiados intentos fallidos. Solicitud rechazada.\n"
                "Comunicate con RRHH si crees que es un error.\n\n"
                "Usa /start para intentar de nuevo."
            )
            return ConversationHandler.END  # END cierra la conversacion

        restantes = MAX_INTENTOS_DNI - intentos
        await update.message.reply_text(
            f"DNI no encontrado en el sistema. "
            f"Intentos restantes: {restantes}\n\n"
            "Ingresa tu DNI nuevamente:"
        )
        return ESPERANDO_DNI

    # Camino infeliz: el empleado ya tiene una solicitud en curso
    if str(empleado["solicitud_pendiente"]).strip() == "True":
        await update.message.reply_text(
            f"Hola {empleado['nombre']}, ya tenes una solicitud pendiente de aprobacion.\n"
            "Comunicate con RRHH para conocer el estado.\n\n"
            "Usa /start para hacer una nueva consulta."
        )
        return ConversationHandler.END

    # Camino infeliz: sin saldo de dias disponibles
    if int(empleado["dias_disponibles"]) <= 0:
        await update.message.reply_text(
            f"Hola {empleado['nombre']}, no tenes dias de vacaciones disponibles.\n"
            f"Dias tomados este año: {empleado['dias_tomados']}\n\n"
            "Comunicate con RRHH para mas informacion."
        )
        return ConversationHandler.END

    # Camino feliz: empleado valido con saldo disponible
    # Guardamos los datos del empleado para usarlos en los pasos siguientes
    context.user_data["empleado"] = empleado.to_dict()

    await update.message.reply_text(
        f"Hola {empleado['nombre']}!\n"
        f"Dias disponibles: {empleado['dias_disponibles']}\n\n"
        "Ingresa la fecha de inicio de tus vacaciones (formato DD/MM/AAAA):"
    )
    return ESPERANDO_FECHA  # avanza al siguiente estado


async def recibir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe y valida la fecha de inicio ingresada por el usuario.

    Caminos infelices manejados:
      - Formato de fecha incorrecto (no es DD/MM/AAAA)
      - Fecha en el pasado

    Si la fecha es valida la guarda en context.user_data y avanza a ESPERANDO_DIAS.
    """
    texto = update.message.text.strip()
    fecha = validar_fecha(texto)

    # Camino infeliz: formato de fecha incorrecto
    if fecha is None:
        await update.message.reply_text(
            "Formato de fecha invalido. Usa DD/MM/AAAA.\n"
            "Ejemplo: 15/07/2025\n\n"
            "Ingresa la fecha de inicio:"
        )
        return ESPERANDO_FECHA  # se queda en el mismo estado

    # Camino infeliz: fecha anterior a hoy
    if fecha < datetime.now():
        await update.message.reply_text(
            "La fecha de inicio no puede ser en el pasado.\n\n"
            "Ingresa una fecha futura:"
        )
        return ESPERANDO_FECHA

    # Camino feliz: fecha valida
    context.user_data["fecha_inicio"] = texto
    empleado = context.user_data["empleado"]

    await update.message.reply_text(
        f"Fecha de inicio: {texto}\n"
        f"Dias disponibles: {empleado['dias_disponibles']}\n\n"
        "Cuantos dias de vacaciones queres tomar?"
    )
    return ESPERANDO_DIAS


async def recibir_dias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe y valida la cantidad de dias solicitados.

    Caminos infelices manejados:
      - El valor ingresado no es un numero entero positivo
      - La cantidad supera el saldo disponible del empleado

    Si es valido guarda los dias y avanza a CONFIRMANDO mostrando un resumen.
    """
    texto = update.message.text.strip()

    # Camino infeliz: no es un numero entero positivo
    # isdigit() verifica que sea numero, int(texto) > 0 verifica que no sea cero
    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text(
            "Ingresa un numero entero mayor a cero.\n\n"
            "Cuantos dias queres tomar?"
        )
        return ESPERANDO_DIAS

    dias_solicitados = int(texto)
    empleado = context.user_data["empleado"]
    dias_disponibles = int(empleado["dias_disponibles"])

    # Camino infeliz: solicita mas dias de los que tiene disponibles
    if dias_solicitados > dias_disponibles:
        await update.message.reply_text(
            f"No tenes suficiente saldo.\n"
            f"Solicitaste {dias_solicitados} dias pero solo tenes {dias_disponibles}.\n\n"
            "Ingresa una cantidad menor:"
        )
        return ESPERANDO_DIAS

    # Camino feliz: cantidad valida
    context.user_data["dias_solicitados"] = dias_solicitados
    """
        Calculamos la fecha de finalizacion en base a la fecha de inicio
        y la cantidad de dias solicitados. Se guarda en user_data para usarla 
        luego en la confirmacion final y en el registro CSV.
    """
    fecha_fin = calcular_fecha_fin(context.user_data["fecha_inicio"], dias_solicitados)
    context.user_data["fecha_fin"] = fecha_fin

    # Mostramos el resumen antes de confirmar
    await update.message.reply_text(
        "Resumen de tu solicitud:\n"
        f"   Empleado: {empleado['nombre']}\n"
        f"   Fecha de inicio: {context.user_data['fecha_inicio']}\n"
        f"   Fecha de finalizacion: {context.user_data['fecha_fin']}\n"
        f"   Dias solicitados: {dias_solicitados}\n\n"
        "Confirmas la solicitud? Responde SI o NO:"
    )
    return CONFIRMANDO


async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe la confirmacion final del usuario (SI o NO).

    Si responde SI:
      - Actualiza dias_disponibles restando los dias solicitados
      - Actualiza dias_tomados sumando los dias solicitados
      - Marca solicitud_pendiente como True
      - Guarda todo en el CSV

    Si responde NO cancela la solicitud sin modificar nada.
    Si responde otra cosa le pide que repita.
    """
    respuesta = update.message.text.strip().upper()

    # El usuario cancela voluntariamente
    if respuesta == "NO":
        await update.message.reply_text(
            "Solicitud cancelada. Usa /start para comenzar de nuevo."
        )
        return ConversationHandler.END

    # Respuesta invalida: no es SI ni NO
    if respuesta != "SI":
        await update.message.reply_text(
            "Responde SI para confirmar o NO para cancelar:"
        )
        return CONFIRMANDO  # se queda esperando una respuesta valida

    # Camino feliz: el usuario confirmo con SI
    # Recuperamos todos los datos guardados durante la conversacion
    empleado = context.user_data["empleado"]
    dias_solicitados = context.user_data["dias_solicitados"]

    # Actualizamos el CSV con los nuevos valores
    df = cargar_empleados()
    indice = df[df["dni"] == int(empleado["dni"])].index[0]
    df.at[indice, "dias_disponibles"] = int(empleado["dias_disponibles"]) - dias_solicitados
    df.at[indice, "dias_tomados"]     = int(empleado["dias_tomados"]) + dias_solicitados
    df.at[indice, "solicitud_pendiente"] = True
    guardar_empleados(df)
    """ 
        Ademas de actualizar el saldo del empleado, registramos la solicitud
        en un CSV separado para dejar historial y trazabilidad del proceso.
    """
    registrar_solicitud(
        empleado,
        context.user_data["fecha_inicio"],
        context.user_data["fecha_fin"],
        dias_solicitados,
        "Aprobada"
    )

    await update.message.reply_text(
        "Solicitud registrada con exito!\n\n"
        f"   Empleado: {empleado['nombre']}\n"
        f"   Fecha de inicio: {context.user_data['fecha_inicio']}\n"
        f"   Fecha de finalizacion: {context.user_data['fecha_fin']}\n"
        f"   Dias solicitados: {dias_solicitados}\n"
        f"   Dias restantes: {int(empleado['dias_disponibles']) - dias_solicitados}\n\n"
        "RRHH recibira la notificacion. Usa /start para nueva consulta."
    )
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se ejecuta cuando el usuario manda /cancelar en cualquier momento.
    ConversationHandler.END cierra la conversacion sin importar en que estado estaba.
    """
    await update.message.reply_text(
        "Operacion cancelada. Usa /start para comenzar de nuevo."
    )
    return ConversationHandler.END


# ==============================================================================
# FUNCION PRINCIPAL
# Arma el bot, registra los handlers y lo pone a escuchar mensajes.
# ==============================================================================

def main():
    # Construye la aplicacion con el TOKEN del .env
    aplicacion = Application.builder().token(TOKEN).build()

    # ConversationHandler es el corazon del bot.
    # Conecta cada estado con la funcion que lo maneja.
    manejador_conversacion = ConversationHandler(
        # entry_points: como puede empezar la conversacion (solo con /start)
        entry_points=[CommandHandler("start", inicio)],

        # states: diccionario que mapea cada estado a su funcion manejadora
        # filters.TEXT & ~filters.COMMAND significa: cualquier texto que NO sea un comando
        states={
            ESPERANDO_DNI:   [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_dni)],
            ESPERANDO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_fecha)],
            ESPERANDO_DIAS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_dias)],
            CONFIRMANDO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },

        # fallbacks: comandos que funcionan en cualquier estado
        # /cancelar siempre funciona sin importar en que paso este el usuario
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    aplicacion.add_handler(manejador_conversacion)

    print("Bot corriendo... Ctrl+C para detener.")
    aplicacion.run_polling()  # empieza a escuchar mensajes de Telegram


if __name__ == "__main__":
    # Este bloque asegura que main() solo se ejecute si corres el archivo directamente.
    # Si otro archivo importara este modulo, main() no se ejecutaria automaticamente.
    main()