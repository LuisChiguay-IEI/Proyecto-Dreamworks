# Tres innovaciones propias de la evaluación

Las correcciones y evoluciones anteriores (categoría, estado y prioridad) se conservan.
Las tres innovaciones elegidas por el equipo son las siguientes.

| Innovación | Cambio de estructura | Formulario/pantalla | Permisos |
| --- | --- | --- | --- |
| Plataforma de juego | Campo plataforma en Preguntas | Crear/modificar consulta, historial, panel y conversación | Cliente selecciona al crear; administrador puede modificar |
| Notas internas | Modelo NotaInterna con pregunta, autor, contenido y fecha | Sección Notas internas al abrir una conversación como personal | Solo técnico/administrador; ni los datos ni el formulario se envían al cliente |
| Respuesta como solución | Campo es_solucion en Respuesta y restricción única condicional | Botones y destacado verde en la conversación | Solo dueño de la consulta puede elegir, cambiar o quitar la marca |

## Decisiones de funcionamiento

- Sin especificar es el valor inicial de plataforma para consultas ya existentes. No se asigna una consola inventada a datos antiguos.
- Las notas no son respuestas públicas. No se envían al cliente ni al asistente Gemini.
- Cada nota guarda la sesión real como autor y la consulta de la URL; campos enviados por el navegador no pueden cambiar esas relaciones.
- Se validan hasta 2000 caracteres por nota. Los mensajes HTML se escapan al mostrarse.
- El dueño puede escoger cualquiera de las respuestas de su consulta. Administradores y técnicos no pueden elegir por él, salvo si ellos mismos son los dueños de esa consulta.
- Solo hay una solución seleccionada por consulta. La base de datos también impide dos respuestas marcadas simultáneamente.
- Elegir otra desmarca la anterior. Quitar la marca no elimina la respuesta.
- El estado del ticket y su fecha de resolución se siguen gestionando desde Modificar consulta; no cambian automáticamente al elegir una respuesta.
- Las acciones de notas y solución requieren sesión, POST y token CSRF.

## Evidencias para el informe

Las capturas anteriores de modelos, formularios y migraciones deben actualizarse para
incluir estas innovaciones. No hay que borrar las migraciones anteriores.

1. Modelo modificado: capturar plataforma en Preguntas, es_solucion/Meta en Respuesta y NotaInterna. Pueden ser tres imágenes legibles.
2. Migración creada: capturar 0005_notainterna_preguntas_plataforma_and_more.py, incluyendo creación de NotaInterna, los dos campos y la restricción.
3. Migración aplicada: ejecutar `python manage.py showmigrations online` y mostrar 0005 con [X].
4. Formulario actualizado: capturar PreguntasForm (plataforma), NotaInternaForm (contenido) y la acción MarcarSolucion en views.py. La selección de solución usa un botón POST, no un campo editable en RespuestaForm.
5. Plataforma en pantalla: crear consulta como cliente eligiendo PlayStation, guardar y capturar el valor en el historial o conversación.
6. Notas internas: abrir esa consulta como técnico/admin, escribir una nota y guardar. Capturar la nota con su autor y fecha. Luego entrar como dueño cliente a la misma consulta y capturar que no aparece esa sección.
7. Solución: responder como técnico. Entrar como dueño y pulsar Marcar como solución. Capturar el destacado verde. Para comprobar exclusividad, crear otra respuesta y marcarla; solo la última debe quedar destacada.

## Dónde está el código

- online/models.py: modelos y restricción de solución única.
- online/forms.py: plataforma en PreguntasForm y nuevo NotaInternaForm.
- online/views.py: AgregarNotaInterna, MarcarSolucion y contexto privado del personal.
- CallCenterGamer/urls.py: rutas POST para notas y solución.
- online/templates/Respuestas.html: conversación, notas y botones de solución.
- online/templates/inicio.html: formulario e historial con plataforma.
- administracion/templates/indexAdmin.html: consultas con plataforma.
- online/static/app.css: destacado de solución y sección de notas.
- online/test_innovaciones.py: pruebas funcionales y de permisos.

## Ejecutar en Windows

Descomprimir en una carpeta nueva y abrir donde está manage.py. Ejecutar Start Servidor Web.bat.
Si ya existe un entorno configurado:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

No incluimos .venv ni cachés en el ZIP para mantenerlo liviano.
La configuración de Gemini se conserva; estas innovaciones no dependen de que Gemini esté disponible.
