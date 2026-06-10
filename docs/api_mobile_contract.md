# Contrato API movil - Cartillas Operaciones Mina

Este documento describe el contrato minimo para que Flutter y la web Exploramin consuman el backend Mina Carolina. No incluye tokens, passwords ni credenciales.

## Flujo movil recomendado

1. `POST /api/auth/login/`
2. `GET /api/mobile/bootstrap/`
3. Crear o actualizar la cartilla en Drift/SQLite con `clientRecordId`.
4. `POST /api/sync/cartillas-operacion-mina/`
5. `POST /api/attachments/cartillas/{cartillaId}/`
6. `GET /api/mina/cartillas/by-client-record/{clientRecordId}/`
7. `POST /api/mina/cartillas/{cartillaId}/submit/` cuando el usuario cierre captura.
8. `GET /api/mina/cartillas/{cartillaId}/render-data/` para pintar detalle renderizable.

## Endpoints principales

| Metodo | Endpoint | Uso |
| --- | --- | --- |
| POST | `/api/auth/login/` | Login JWT. |
| POST | `/api/auth/refresh/` | Refrescar access token. |
| GET | `/api/auth/me/` | Usuario actual, roles y datos base. |
| GET | `/api/mobile/bootstrap/` | Catalogos, tipos de cartilla y permisos. |
| POST | `/api/sync/cartillas-operacion-mina/` | Upsert offline-first de cartilla. |
| POST | `/api/attachments/cartillas/{cartillaId}/` | Subir foto, firma, evidencia o documento. |
| GET | `/api/attachments/cartillas/{cartillaId}/` | Listar adjuntos activos. |
| DELETE | `/api/attachments/{attachmentId}/` | Soft delete de adjunto. |
| GET | `/api/mina/cartillas/` | Listado con filtros y acciones disponibles. |
| GET | `/api/mina/cartillas/{cartillaId}/` | Detalle tecnico completo. |
| GET | `/api/mina/cartillas/{cartillaId}/summary/` | Resumen compacto. |
| GET | `/api/mina/cartillas/{cartillaId}/render-data/` | Payload listo para pintar cartilla. |
| GET | `/api/mina/cartillas/by-client-record/{clientRecordId}/` | Buscar una cartilla sincronizada. |
| POST | `/api/mina/cartillas/{cartillaId}/submit/` | Enviar cartilla. |
| POST | `/api/mina/cartillas/{cartillaId}/observe/` | Observar cartilla. Requiere `comment`. |
| POST | `/api/mina/cartillas/{cartillaId}/approve/` | Aprobar cartilla. |
| POST | `/api/mina/cartillas/{cartillaId}/reject/` | Rechazar cartilla. Requiere `comment`. |
| POST | `/api/mina/cartillas/{cartillaId}/close/` | Cerrar cartilla aprobada. |

## Payload sync

`POST /api/sync/cartillas-operacion-mina/`

```json
{
  "clientRecordId": "device-uuid-or-ulid",
  "cartillaType": "mina_operacion_diaria",
  "payloadVersion": 1,
  "fechaOperacion": "2026-05-20",
  "turnoId": 1,
  "guardiaId": 1,
  "areaId": 1,
  "zonaId": null,
  "nivelId": null,
  "ingenieroMineroId": null,
  "supervisorId": null,
  "climaId": 1,
  "estado": "borrador",
  "lat": null,
  "lon": null,
  "dataJson": {
    "datosGenerales": {
      "ubicacionTexto": "Galeria principal",
      "observacionTurno": "Operacion normal"
    },
    "perforacionVoladura": [],
    "extraccionAcarreo": [],
    "personal": [
      {
        "rowKey": "personal-1",
        "trabajadorId": 1,
        "cargoId": null,
        "empresaId": null,
        "horaIngreso": "07:00",
        "horaSalida": "19:00",
        "epp": true,
        "observaciones": ""
      }
    ],
    "equipos": [],
    "avances": [],
    "accionesCorrectivas": [],
    "observaciones": [],
    "firmas": []
  }
}
```

## Response sync

```json
{
  "clientRecordId": "device-uuid-or-ulid",
  "serverCartillaId": 123,
  "syncStatus": "synced",
  "estadoWorkflow": "borrador",
  "created": true,
  "updatedAt": "2026-05-20T12:00:00Z",
  "warnings": []
}
```

## Payload attachments

`POST /api/attachments/cartillas/{cartillaId}/` usa `multipart/form-data`.

| Campo | Tipo | Requerido | Nota |
| --- | --- | --- | --- |
| `file` | archivo | Si | jpg, jpeg, png, webp o pdf. |
| `clientAttachmentId` | string | Si | Id local offline del adjunto. |
| `moduleKey` | string | No | Ejemplo: `personal`, `equipos`, `firmas`. |
| `rowKey` | string | No | Relaciona el adjunto con una fila repetible. |
| `slot` | integer | No | Posicion del adjunto en el modulo. |
| `attachmentType` | string | No | `foto`, `firma`, `documento`, `evidencia`. |
| `originalName` | string | No | Nombre original visible. |
| `mimeType` | string | No | MIME enviado por el cliente. |

## Estados workflow

| Estado | Significado |
| --- | --- |
| `borrador` | Captura local o parcial editable. |
| `enviado` | Enviado para revision. |
| `observado` | Devuelto con comentarios; puede reenviarse. |
| `aprobado` | Revisado y aprobado. |
| `cerrado` | Cerrado, no editable. |
| `rechazado` | Rechazado, no editable por flujo normal. |

## Estados sync locales sugeridos en Flutter

| Estado local | Uso |
| --- | --- |
| `local` | Creado en el dispositivo, nunca enviado. |
| `pending` | Tiene cambios pendientes por sincronizar. |
| `syncing` | Envio en progreso. |
| `synced` | Confirmado por servidor. |
| `failed` | Error de sync; guardar mensaje y reintentar. |

## Render-data

`GET /api/mina/cartillas/{cartillaId}/render-data/` devuelve:

```json
{
  "id": 123,
  "clientRecordId": "device-uuid-or-ulid",
  "header": {
    "fechaOperacion": "2026-05-20",
    "tipoCartilla": {"id": 1, "codigo": "mina_operacion_diaria", "nombre": "Operacion Mina"},
    "turno": {"id": 1, "codigo": "DIA", "nombre": "Dia"},
    "guardia": {"id": 1, "codigo": "A", "nombre": "Guardia A"},
    "area": {"id": 1, "codigo": "MINA", "nombre": "Mina"},
    "zona": null,
    "nivel": null,
    "ingenieroMinero": null,
    "supervisor": null,
    "clima": {"id": 1, "codigo": "SOLEADO", "nombre": "Soleado"},
    "estadoWorkflow": "borrador",
    "syncStatus": "synced",
    "submittedAt": null,
    "reviewedAt": null,
    "closedAt": null
  },
  "modules": {
    "datosGenerales": {},
    "perforacionVoladura": [],
    "extraccionAcarreo": [],
    "personal": [],
    "equipos": [],
    "avances": [],
    "accionesCorrectivas": [],
    "observaciones": [],
    "firmas": []
  },
  "attachments": [],
  "workflowLogs": [],
  "availableActions": {
    "canSubmit": true,
    "canObserve": false,
    "canApprove": false,
    "canReject": false,
    "canClose": false,
    "canView": true,
    "canEditDraft": true
  },
  "warnings": []
}
```

## Summary

`GET /api/mina/cartillas/{cartillaId}/summary/` devuelve un payload compacto:

```json
{
  "id": 123,
  "clientRecordId": "device-uuid-or-ulid",
  "fechaOperacion": "2026-05-20",
  "turno": "Dia",
  "guardia": "Guardia A",
  "area": "Mina",
  "estadoWorkflow": "borrador",
  "syncStatus": "synced",
  "counts": {
    "perforacionVoladura": 0,
    "extraccionAcarreo": 0,
    "personal": 1,
    "equipos": 0,
    "avances": 0,
    "accionesCorrectivas": 0,
    "attachments": 0
  },
  "availableActions": {
    "canSubmit": true,
    "canObserve": false,
    "canApprove": false,
    "canReject": false,
    "canClose": false,
    "canView": true,
    "canEditDraft": true
  },
  "updatedAt": "2026-05-20T12:00:00Z"
}
```

## Notas para Flutter

- `clientRecordId` debe ser estable por registro local y no debe reciclarse.
- `rowKey` debe ser estable por fila repetible para que attachments y reintentos se puedan asociar.
- `dataJson` es la fuente de captura flexible; las tablas hijas son la fuente reportable normalizada.
- Para cartillas offline, guardar ultimo `serverCartillaId`, `syncStatus`, `estadoWorkflow`, `updatedAt` y `warnings`.
- No guardar JWT en texto plano; usar almacenamiento seguro del dispositivo.
