from django.conf import settings
from django.db import models

from core.models import AuditModel


class CartillaOperacionMina(AuditModel):
    ESTADO_BORRADOR = "borrador"
    ESTADO_ENVIADO = "enviado"
    ESTADO_OBSERVADO = "observado"
    ESTADO_APROBADO = "aprobado"
    ESTADO_CERRADO = "cerrado"
    ESTADO_RECHAZADO = "rechazado"

    ESTADO_WORKFLOW_CHOICES = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_ENVIADO, "Enviado"),
        (ESTADO_OBSERVADO, "Observado"),
        (ESTADO_APROBADO, "Aprobado"),
        (ESTADO_CERRADO, "Cerrado"),
        (ESTADO_RECHAZADO, "Rechazado"),
    ]

    SYNC_LOCAL = "local"
    SYNC_PENDING = "pending"
    SYNC_SYNCED = "synced"
    SYNC_FAILED = "failed"

    SYNC_STATUS_CHOICES = [
        (SYNC_LOCAL, "Local"),
        (SYNC_PENDING, "Pendiente"),
        (SYNC_SYNCED, "Sincronizado"),
        (SYNC_FAILED, "Fallido"),
    ]

    client_record_id = models.CharField(max_length=64)
    tipo_cartilla = models.ForeignKey(
        "cartillas.TipoCartilla",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cartillas_operacion_mina",
    )
    fecha_operacion = models.DateField()
    turno = models.ForeignKey(
        "catalogos.Turno",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    guardia = models.ForeignKey(
        "catalogos.Guardia",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    area = models.ForeignKey(
        "catalogos.Area",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    zona = models.ForeignKey(
        "catalogos.Zona",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    nivel = models.ForeignKey(
        "catalogos.Nivel",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    ingeniero_minero = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="cartillas_como_ingeniero",
        blank=True,
        null=True,
    )
    supervisor = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="cartillas_como_supervisor",
        blank=True,
        null=True,
    )
    clima = models.ForeignKey(
        "catalogos.Clima",
        on_delete=models.PROTECT,
        related_name="cartillas_mina",
        blank=True,
        null=True,
    )
    sucursal = models.ForeignKey(
        "catalogos.Sucursal",
        on_delete=models.PROTECT,
        related_name="cartillas_requerimiento_productos",
        blank=True,
        null=True,
    )
    responsable_requerimiento = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="cartillas_requerimiento_productos",
        blank=True,
        null=True,
    )
    estado_workflow = models.CharField(
        max_length=20,
        choices=ESTADO_WORKFLOW_CHOICES,
        default=ESTADO_BORRADOR,
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default=SYNC_LOCAL,
    )
    sync_error = models.TextField(blank=True)
    sync_attempts = models.PositiveIntegerField(default=0)
    data_json = models.TextField(default="{}", blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cartillas_mina_revisadas",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "client_record_id"],
                name="uq_cartilla_mina_user_client_record",
            ),
        ]
        indexes = [
            models.Index(fields=["fecha_operacion"]),
            models.Index(fields=["turno"]),
            models.Index(fields=["guardia"]),
            models.Index(fields=["area"]),
            models.Index(fields=["estado_workflow"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.fecha_operacion} - {self.tipo_cartilla} - {self.user}"


class CartillaPerforacionVoladura(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="perforaciones_voladura",
    )
    row_key = models.CharField(max_length=64)
    grupo_perforacion = models.ForeignKey(
        "catalogos.GrupoPerforacion",
        on_delete=models.PROTECT,
        related_name="perforaciones_voladura",
    )
    producto = models.ForeignKey(
        "catalogos.Producto",
        on_delete=models.PROTECT,
        related_name="perforaciones_voladura",
    )
    seccion_ancho = models.DecimalField(max_digits=10, decimal_places=2)
    seccion_alto = models.DecimalField(max_digits=10, decimal_places=2)
    hora_inicio = models.TimeField()
    hora_termino = models.TimeField()
    taladros = models.PositiveIntegerField()
    labor_frente = models.ForeignKey(
        "catalogos.LaborFrente",
        on_delete=models.PROTECT,
        related_name="perforaciones_voladura",
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_perforacion_voladura_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.row_key}"


class CartillaPerforacionExplosivo(AuditModel):
    perforacion = models.ForeignKey(
        CartillaPerforacionVoladura,
        on_delete=models.CASCADE,
        related_name="explosivos",
    )
    row_key = models.CharField(max_length=64)
    explosivo = models.ForeignKey(
        "catalogos.Explosivo",
        on_delete=models.PROTECT,
        related_name="cartilla_perforacion_usos",
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    unidad_medida = models.ForeignKey(
        "catalogos.UnidadMedida",
        on_delete=models.PROTECT,
        related_name="explosivos_cartilla",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["perforacion", "row_key"],
                name="uq_perforacion_explosivo_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.perforacion} - {self.explosivo}"


class CartillaPerforacionInsumo(AuditModel):
    perforacion = models.ForeignKey(
        CartillaPerforacionVoladura,
        on_delete=models.CASCADE,
        related_name="insumos",
    )
    row_key = models.CharField(max_length=64)
    insumo = models.ForeignKey(
        "catalogos.InsumoAccesorio",
        on_delete=models.PROTECT,
        related_name="cartilla_perforacion_usos",
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    unidad_medida = models.ForeignKey(
        "catalogos.UnidadMedida",
        on_delete=models.PROTECT,
        related_name="insumos_cartilla",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["perforacion", "row_key"],
                name="uq_perforacion_insumo_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.perforacion} - {self.insumo}"


class CartillaExtraccionAcarreo(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="extracciones_acarreo",
    )
    row_key = models.CharField(max_length=64)
    producto = models.ForeignKey(
        "catalogos.Producto",
        on_delete=models.PROTECT,
        related_name="extracciones_acarreo",
        blank=True,
        null=True,
    )
    origen_texto = models.CharField(max_length=200, blank=True)
    destino_texto = models.CharField(max_length=200, blank=True)
    toneladas = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
    )
    viajes = models.PositiveIntegerField(blank=True, null=True)
    equipo = models.ForeignKey(
        "catalogos.Equipo",
        on_delete=models.PROTECT,
        related_name="extracciones_acarreo",
        blank=True,
        null=True,
    )
    operador = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="extracciones_acarreo",
        blank=True,
        null=True,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_extraccion_acarreo_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.row_key}"


class CartillaPersonal(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="personal",
    )
    row_key = models.CharField(max_length=64)
    trabajador = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="cartillas_personal",
    )
    cargo = models.ForeignKey(
        "catalogos.Cargo",
        on_delete=models.PROTECT,
        related_name="cartillas_personal",
        blank=True,
        null=True,
    )
    empresa = models.ForeignKey(
        "catalogos.Empresa",
        on_delete=models.PROTECT,
        related_name="cartillas_personal",
        blank=True,
        null=True,
    )
    hora_ingreso = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    epp = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_cartilla_personal_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.trabajador}"


class CartillaEquipo(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="equipos",
    )
    row_key = models.CharField(max_length=64)
    equipo = models.ForeignKey(
        "catalogos.Equipo",
        on_delete=models.PROTECT,
        related_name="cartillas_equipo",
    )
    codigo_equipo_snapshot = models.CharField(max_length=50, blank=True)
    operador = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="cartillas_equipo_operador",
        blank=True,
        null=True,
    )
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    horometro_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    horometro_final = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    combustible = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    total_horas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_cartilla_equipo_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.equipo}"


class CartillaAvance(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="avances",
    )
    row_key = models.CharField(max_length=64)
    labor_frente = models.ForeignKey(
        "catalogos.LaborFrente",
        on_delete=models.PROTECT,
        related_name="cartillas_avance",
        blank=True,
        null=True,
    )
    tipo = models.CharField(max_length=100, blank=True)
    meta = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True)
    avance_dia = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
    )
    acumulado = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
    )
    condiciones_frente = models.TextField(blank=True)
    actividades = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_cartilla_avance_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.row_key}"


class CartillaAccionCorrectiva(AuditModel):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="acciones_correctivas",
    )
    row_key = models.CharField(max_length=64)
    descripcion = models.TextField()
    responsable = models.ForeignKey(
        "catalogos.Trabajador",
        on_delete=models.PROTECT,
        related_name="acciones_correctivas",
        blank=True,
        null=True,
    )
    plazo = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_accion_correctiva_row",
            ),
        ]
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.row_key}"


class CartillaRequerimientoProductoDetalle(AuditModel):
    SECCION_HERRAMIENTAS = "herramientas_otros"
    SECCION_EPP = "equipo_proteccion_personal"

    SECCION_CHOICES = [
        (SECCION_HERRAMIENTAS, "Herramientas y/o otros"),
        (SECCION_EPP, "Equipo de proteccion personal"),
    ]

    PRIORIDAD_BAJA = "BAJA"
    PRIORIDAD_ALTA = "ALTA"

    PRIORIDAD_CHOICES = [
        (PRIORIDAD_BAJA, "Baja"),
        (PRIORIDAD_ALTA, "Alta"),
    ]

    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="requerimiento_productos",
    )
    row_key = models.CharField(max_length=64)
    seccion = models.CharField(max_length=40, choices=SECCION_CHOICES)
    fecha = models.DateField()
    rubro = models.ForeignKey(
        "catalogos.RequerimientoRubro",
        on_delete=models.PROTECT,
        related_name="requerimientos_cartilla",
    )
    producto = models.ForeignKey(
        "catalogos.RequerimientoProducto",
        on_delete=models.PROTECT,
        related_name="requerimientos_cartilla",
    )
    descripcion = models.TextField(blank=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    unidad_medida = models.ForeignKey(
        "catalogos.UnidadMedida",
        on_delete=models.PROTECT,
        related_name="requerimientos_productos",
    )
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default=PRIORIDAD_BAJA,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "row_key"],
                name="uq_req_producto_cartilla_row",
            ),
        ]
        indexes = [
            models.Index(fields=["seccion"]),
            models.Index(fields=["fecha"]),
            models.Index(fields=["rubro"]),
            models.Index(fields=["producto"]),
            models.Index(fields=["prioridad"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.seccion} - {self.producto}"


class CartillaWorkflowLog(models.Model):
    cartilla = models.ForeignKey(
        CartillaOperacionMina,
        on_delete=models.CASCADE,
        related_name="workflow_logs",
    )
    from_state = models.CharField(max_length=20, blank=True)
    to_state = models.CharField(max_length=20)
    action = models.CharField(max_length=100)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cartilla_mina_workflow_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["to_state"]),
        ]

    def __str__(self) -> str:
        return f"{self.cartilla} - {self.action} - {self.to_state}"

# Create your models here.
