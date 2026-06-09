# API Cartillas Operaciones Mina

Backend Django/DRF para Cartillas Operaciones Mina / Mina Carolina.

## Puesta en marcha futura

1. Crear `.env` desde `.env.example`.
2. Configurar la base nueva `CARTILLAS_OPERACIONES_MINA`.
3. Verificar el proyecto:

```bash
.venv/bin/python manage.py check
```

4. Cuando la base este lista, aplicar migraciones:

```bash
.venv/bin/python manage.py migrate
```

5. Sembrar datos iniciales:

```bash
.venv/bin/python manage.py seed_mina_initial_data
```

Para crear admin inicial en el mismo seed:

```bash
.venv/bin/python manage.py seed_mina_initial_data \
  --admin-username admin \
  --admin-password "<password>" \
  --admin-email admin@example.com \
  --admin-dni ""
```

Tambien se puede crear el admin manualmente:

```bash
.venv/bin/python manage.py createsuperuser
```

6. Levantar servidor:

```bash
.venv/bin/python manage.py runserver
```
