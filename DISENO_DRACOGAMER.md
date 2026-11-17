# DRACOGAMER CallCenter

Diseño inspirado en los tres archivos de referencia proporcionados: ambiente de fantasía con dragones, fondos café/negro, marcos dorados, brillos cálidos, hojas flotantes y brasas discretas. No incorpora carruseles, productos, ventas ni campos propios de una tienda.

El logo es la imagen original de la referencia, sin regenerarlo ni retocarlo. El marco circular y el resplandor se aplican con CSS. Se incluye el archivo descargado para no depender de enlaces externos.

- Logo original: https://i.pinimg.com/736x/f4/d4/7a/f4d47adb844404ac35bea7800e7344d3.jpg
- Fondo de referencia: https://i.pinimg.com/736x/44/22/09/442209d160acb8d66ba0763f059ec20f.jpg
- Textura: https://www.transparenttextures.com/patterns/black-scales.png
- Tipografías de la referencia: Cinzel (títulos) e Inter (texto). Incluidas localmente desde Google Fonts.

Cliente e invitado comparten el ambiente oscuro y cálido. Administrador mantiene morado brillante y técnico azul; ambos incluyen detalles dracónicos y un fondo tenue que permite leer los datos.

El botón Pausar ambiente, en el pie de página, detiene las hojas y brasas. La preferencia se conserva en el navegador. Si el sistema prefiere movimiento reducido, las animaciones decorativas se desactivan automáticamente.

Los fondos decorativos no reciben clics ni aparecen como contenido para lectores de pantalla. Los formularios conservan sus etiquetas y foco visible. El detalle de consultas conserva apertura, ampliación, cierre y Escape.

## Integración
Esta entrega parte del ZIP Perfiles e Interfaz, con sus cuatro perfiles, límites y migración 0006. Los modelos, vistas, formularios, rutas, configuración, base de datos e ia_utils.py se conservan sin cambios respecto de esa versión. No hay migraciones adicionales por la estética. El nombre interno del paquete Django sigue siendo CallCenterGamer para no romper importaciones.

Cambios visuales: plantillas, online/static/app.css, online/static/app.js, online/static/draco.css y recursos en online/static/draco/.

Verificación: 61 pruebas funcionales correctas y revisión en navegador de cuatro roles, portada, acceso, detalles ampliables, menú administrativo y ancho móvil de 390 px. Se comprobó la pausa y persistencia del ambiente. Las vistas previas usan una base de datos separada; no se entregan usuarios de demostración.

Para ejecutar, sigue LEEME.md. La conexión real de IA continúa a cargo del compañero, sin cambios en esta entrega.

## Acceso con arte ASCII
Inicio de sesión, registro y acceso de invitados usan los dos dragones proporcionados como texto Unicode, con una fuente local monoespaciada y brillo dorado. El ajuste conserva espacios y líneas y adapta el tamaño a la pantalla. Los dibujos son decorativos y no interceptan los controles. La portada conserva su fondo ilustrado. No requiere migraciones.

La portada también utiliza los dos dragones ASCII como fondo, conservando el logo. El botón «Empezar con mi consulta» abre el inicio de sesión y desde allí se ofrece el registro.
