#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import secrets


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CallCenterGamer.settings')
    # El proceso del autoreloader hereda el identificador del servidor padre.
    # Una nueva ejecución de runserver genera otro e invalida las sesiones previas.
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        os.environ['DRACO_SERVER_SESSION_ID'] = secrets.token_hex(32)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()






