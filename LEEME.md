# DRACOGAMER CallCenter · Perfiles e interfaz

Extrae el ZIP completo y abre en VS Code la carpeta que contiene manage.py.
En Terminal > Nueva terminal, ejecuta cada comando por separado:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Abre http://127.0.0.1:8000/ y usa tu cuenta existente o Probar como invitado.
No se necesitan cuentas nuevas para conservar el trabajo anterior. La primera instalación necesita Internet para descargar librerías.
Si ya tienes entorno virtual en esta carpeta, puedes omitir el primer comando.
Ejecuta migrate también cuando uses tu propia base de datos: esta versión incorpora la migración 0006.


Ver CAMBIOS_PERFILES.md para reglas, límites y archivos que deben integrar.
Al compartir el proyecto, excluye .venv, __pycache__, .env y .git. Conserva db.sqlite3, las migraciones, las plantillas y los archivos estáticos.

Diseño y recursos: ver DISENO_DRACOGAMER.md.
