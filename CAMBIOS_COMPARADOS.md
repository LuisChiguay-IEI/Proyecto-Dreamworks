# Cambios respecto del proyecto original del profesor

Comparación de CallCenterGame Primavera 2026r(1).zip con la versión aportada
CallCenterGame1_Corregido (2).zip. Se revisó el código de ambos ZIP; no es una prueba
manual de la aplicación en tu computador ni confirma disponibilidad de la API.

## Evoluciones previas del profesor (no son las tres innovaciones propias)

| Mejora | Antes | Ahora | Dónde verla | Archivos principales |
| --- | --- | --- | --- | --- |
| Categoría persistida | La categoría se calculaba con IA en vistas y no se guardaba en Preguntas. | Campo categoria guardado en BD, seleccionado por el usuario o administrador. | Nueva consulta, historial, Modificar consulta y filtros del panel. | online/models.py, online/forms.py, online/templates/inicio.html, administracion/templates/indexAdmin.html |
| Estado de atención | No existía estado; algunas estadísticas confundían tener mensajes con estar resuelta. | Abierto, en proceso, resuelto y cerrado. Resolver/cerrar registra fecha_resolucion; reabrir la limpia. | Panel de consultas y Modificar consulta, con cuenta administrador. | online/models.py, online/forms.py, administracion/views.py |
| Prioridad | No existía campo de prioridad. | Baja, media y alta; se guarda y se puede filtrar. | Nueva consulta, historial y panel de consultas. | online/models.py, online/forms.py, administracion/views.py |

Estos campos se incorporan mediante online/migrations/0004_preguntas_categoria_preguntas_estado_and_more.py.
Categoría, estado y prioridad son cambios nuevos; fecha_resolucion complementa el estado.

## Errores corregidos y mejoras adicionales

| Problema identificado en el original | Cambio comprobado en el código actual | Dónde comprobarlo en la página |
| --- | --- | --- |
| indexAdmin.html redirigía al personal a /Administracion/, la misma ruta que lo mostraba. | Se reemplazó por un panel de consultas y se quitaron redirecciones JavaScript. | Iniciar sesión como técnico o administrador: aparece el panel sin recarga circular. |
| La pantalla del cliente tenía buscar_ayuda, pero Inicio no procesaba esa consulta. | Se conectó el formulario con AsistenteIA mediante POST, consentimiento y CSRF. | Mis consultas > Asistente virtual. Requiere API configurada para respuesta real. |
| Integración original con OpenAI y excepciones internas dentro del mensaje al usuario. | Adaptación a Gemini, timeout de 20 segundos y error genérico; logging solo del tipo de excepción. | Asistente virtual; ante fallo se muestra aviso sin detalles internos. |
| Tiempo promedio escrito como '2.5 días'. | Promedio calculado desde la creación hasta la primera respuesta de técnico o administrador. | Estadísticas, con cuenta administrador. |
| Porcentaje de resueltas basado en tener cualquier respuesta. | Se calcula con estado resuelto/cerrado; la falta de atención técnica se calcula aparte. | Panel y Estadísticas. |
| Paneles recorrían consultas y usuarios haciendo repetidas llamadas IA. | Métricas y categorías desde BD, en administracion/services.py; sin llamadas IA al abrir esos paneles. | Panel de consultas, Usuarios y Estadísticas. |
| No había validación del dígito verificador del RUT en RegisterForm. | RUT normalizado, validación de dígito verificador y duplicados en servidor. Si está vacío sigue siendo opcional. | Registrarse: probar un RUT con dígito incorrecto. |
| Correo duplicado comprobado con coincidencia exacta. | Comparación sin distinguir mayúsculas/minúsculas; se incorporan validadores de contraseña de Django. | Registrarse. La unicidad del nombre de usuario ya existía. |
| Formularios incluían autor, pregunta y fechas como campos ocultos. Las vistas ya reasignaban esos datos. | Se retiraron esos campos del formulario y se mantuvo la asignación en el servidor. | Crear consulta o responder: el usuario solo completa los datos editables. |
| Respuesta con maxlength solo en HTML y sin límite equivalente en servidor. | Validadores en servidor: pregunta 5000 caracteres, respuesta 2000 y consulta al asistente 1000. | Formularios de consultas, respuestas y asistente. |
| El administrador podía quitarse permisos o desactivar su cuenta. | Se impide autodesactivación/autodegradación y se agrega protección de última cuenta admin activa. | Usuarios: intentar guardar la propia cuenta sin admin o activo. |
| Listas completas sin paginación. | Historial de 15 consultas por página y panel/usuarios de 20 por página. | Historial, panel y Usuarios, cuando se supera ese número. |
| Páginas hijas repetían estructura HTML y había plantillas duplicadas no usadas. | Cabecera compartida, plantillas normalizadas y CSS común adaptable. | Navegación general, registro, acceso, conversación y panel. |
| Configuración exigía variables MySQL aunque en la versión de trabajo ya se usaba SQLite. | Se mantiene SQLite y se retira la exigencia incoherente de variables MySQL. El original del profesor usaba MySQL. | Configuración; no es un control visible en la página. |
| Dependencias sin versiones fijas y script de inicio sin migraciones. | requirements.txt con versiones fijadas; .bat crea entorno, instala, migra e inicia. | Terminal al iniciar el proyecto. |

## Funciones originales que se conservaron

- Registro, inicio/cierre de sesión y contraseñas guardadas con hash ya existían.
- Roles cliente, técnico y administrador, con campos admin/tecnico/activo, ya existían.
- Preguntas, respuestas, sus relaciones y gestión básica de usuarios ya existían.
- Restricción de conversaciones ajenas y reasignación de autor/pregunta en servidor ya existían.
- Logout y eliminaciones mediante POST, y bloqueo de autoeliminación, ya existían.
- Había pruebas de autorización; se amplió la cobertura con online/test_mejoras.py.

No deben presentarse esas funciones conservadas como si fueran implementadas desde cero.

## Cómo demostrar las tres mejoras

1. Registrarse o ingresar como cliente y crear una consulta con categoría Hardware y prioridad Alta.
2. Comprobar ambos valores y el estado Abierto en el historial.
3. Ingresar como administrador y filtrar el panel por categoría y prioridad.
4. Abrir Modificar consulta y pasar el estado a En proceso, luego Resuelto.
5. Comprobar el nuevo estado en el panel y en el historial del cliente.
6. Revisar Estadísticas. Para medir tiempo de atención debe existir una respuesta de técnico/admin.
7. Opcional: consultar al asistente con la clave configurada. Un mensaje de indisponibilidad no es evidencia de una respuesta real de IA.

## Alcance pendiente

No se añadieron adjuntos, notificaciones, asignación de técnicos, encuestas, cola de IA
ni auditoría persistida en BD. Los eventos administrativos se registran mediante logging.
El asistente sigue siendo síncrono y el límite por usuario usa caché local.
Esta versión no certifica seguridad de producción ni éxito de Gemini con tu cuenta.


## Actualización: tres innovaciones propias

Se implementaron plataforma de juego, notas internas y respuesta marcada como solución. Ver INNOVACIONES.md. La tabla anterior describe correcciones y evoluciones previas; no debe usarse como la selección definitiva de innovaciones de la evaluación.
