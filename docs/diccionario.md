# Diccionario de Datos — Bot de Gestión de Vacaciones

---

## Entidad: empleados.csv

Tabla principal del sistema. Cada fila representa un empleado registrado.

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| dni | Entero | Documento Nacional de Identidad del empleado. Clave primaria. | 12345678 |
| nombre | Texto | Nombre completo del empleado | Juan Perez |
| dias_disponibles | Entero | Saldo de días de vacaciones que le quedan al empleado | 15 |
| dias_tomados | Entero | Total de días de vacaciones ya utilizados en el año | 5 |
| solicitud_pendiente | Booleano | Indica si el empleado tiene una solicitud en curso | False |

---
## Entidad: solicitudes.csv
Historial de solitudes realizadas mediante el chatbot. Cada fila representa una solicitud registrada.

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| dni | Entero | DNI del empleado que realiza la solicitud | 12345678
| nombre | Texto | Nombre del empleado solicitante | Juan Perez
| fecha_inicio | Fecha | Fecha en la que comienzan las vacaciones solicitadas. Formato DD/MM/AAAA | 10/07/2026
| fecha_fin | Fecha | Fecha calculada automaticamente en la que finalizan las vacaciones | 14/07/2026
| dias_solicitados | Entero | Cantidad de dias de vacaciones solicitados por el empleado | 5
| estado | Texto | Resultado de la solicitud | Aprobada
---

## Estados de la máquina de estados

El bot usa un ConversationHandler que mantiene el estado de cada conversación.

| Estado | Valor | Descripción |
|---|---|---|
| ESPERANDO_DNI | 1 | El bot aguarda que el usuario ingrese su DNI |
| ESPERANDO_FECHA | 2 | El bot aguarda la fecha de inicio en formato DD/MM/AAAA |
| ESPERANDO_DIAS | 3 | El bot aguarda la cantidad de días solicitados |
| CONFIRMANDO | 4 | El bot aguarda SI o NO para confirmar la solicitud |
| FIN_APROBADA | END | Solicitud registrada exitosamente en el CSV |
| FIN_RECHAZADA | END | Solicitud rechazada por DNI inválido o sin saldo |
| FIN_PENDIENTE | END | Solicitud cancelada por el usuario o por error crítico |

---

## Variables en memoria (context.user_data)

Datos que el bot guarda temporalmente durante la conversación.

| Variable | Tipo | Descripción |
|---|---|---|
| intentos_dni | Entero | Contador de intentos fallidos de DNI. Máximo 3. |
| empleado | Diccionario | Fila completa del empleado una vez validado el DNI |
| fecha_inicio | Texto | Fecha de inicio ingresada por el usuario (DD/MM/AAAA) |
| fecha_fin | Texto | Fecha de finalizacion calculada automaticamente por el bot |
| dias_solicitados | Entero | Cantidad de días solicitados por el empleado |

---

## Reglas de negocio

| Regla | Descripción |
|---|---|
| RN-01 | El DNI ingresado debe contener solo numeros|
| RN-02 | El DNI debe existir en el CSV. Máximo 3 intentos antes del bloqueo. |
| RN-03 | El empleado no puede solicitar vacaciones si dias_disponibles es 0. |
| RN-04 | El empleado no puede tener más de una solicitud pendiente activa. |
| RN-05 | La fecha de inicio debe tener formato DD/MM/AAAA|
| RN-06 | La fecha de inicio debe ser posterior a la fecha actual. |
| RN-07 | Los días solicitados no pueden superar dias_disponibles. |
| RN-08 | La fecha de finalizacion se calcula automaticamente a partir de la fecha de inicio y los dias solicitados|
| RN-09 | dias_disponibles se reduce y solicitud_pendiente pasa a True. |
| RN-10 | Al aprobar la solicitud, se actualiza empleados.csv y se registra la operacion en solicitudes.csv|