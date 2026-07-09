from django.db import models

from core.models import AuditModel


class CatalogoBase(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class Area(CatalogoBase):
    pass


class Guardia(CatalogoBase):
    pass


class Turno(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cruza_medianoche = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class Clima(CatalogoBase):
    pass


class Empresa(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    ruc = models.CharField(max_length=20, blank=True)
    razon_social = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.razon_social}"


class Cargo(CatalogoBase):
    pass


class Trabajador(AuditModel):
    codigo = models.CharField(max_length=50, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    cargo = models.ForeignKey(
        Cargo,
        on_delete=models.PROTECT,
        related_name="trabajadores",
        blank=True,
        null=True,
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="trabajadores",
        blank=True,
        null=True,
    )
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    es_ingeniero_minero = models.BooleanField(default=False)
    es_supervisor = models.BooleanField(default=False)
    es_operador = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["dni"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.apellidos}, {self.nombres}"


class Zona(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    letra = models.CharField(max_length=10)
    nombre = models.CharField(max_length=150, blank=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return self.nombre or self.letra


class Nivel(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    numero = models.IntegerField()
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"Nivel {self.numero}"


class Labor(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT,
        related_name="labores",
        blank=True,
        null=True,
    )
    nivel = models.ForeignKey(
        Nivel,
        on_delete=models.PROTECT,
        related_name="labores",
        blank=True,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.titulo}"


class LaborFrente(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    labor = models.ForeignKey(
        Labor,
        on_delete=models.PROTECT,
        related_name="frentes",
    )
    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT,
        related_name="frentes",
        blank=True,
        null=True,
    )
    nivel = models.ForeignKey(
        Nivel,
        on_delete=models.PROTECT,
        related_name="frentes",
        blank=True,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.titulo}"


class GrupoPerforacion(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class GrupoPerforacionIntegrante(AuditModel):
    grupo = models.ForeignKey(
        GrupoPerforacion,
        on_delete=models.CASCADE,
        related_name="integrantes",
    )
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name="grupos_perforacion",
    )
    rol_en_grupo = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["grupo", "trabajador"],
                name="uq_grupo_perforacion_trabajador",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.grupo} - {self.trabajador}"


class Producto(CatalogoBase):
    pass


class UnidadMedida(CatalogoBase):
    pass


class Sucursal(CatalogoBase):
    pass


class RequerimientoRubro(CatalogoBase):
    pass


class RequerimientoProducto(AuditModel):
    SECCION_HERRAMIENTAS = "herramientas_otros"
    SECCION_EPP = "equipo_proteccion_personal"

    SECCION_CHOICES = [
        (SECCION_HERRAMIENTAS, "Herramientas y/o otros"),
        (SECCION_EPP, "Equipo de proteccion personal"),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    seccion = models.CharField(max_length=40, choices=SECCION_CHOICES)
    rubro = models.ForeignKey(
        RequerimientoRubro,
        on_delete=models.PROTECT,
        related_name="productos_requerimiento",
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="productos_requerimiento",
        blank=True,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["seccion"]),
            models.Index(fields=["rubro"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class Explosivo(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="explosivos",
    )
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class InsumoAccesorio(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        on_delete=models.PROTECT,
        related_name="insumos_accesorios",
    )
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class Equipo(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=100, blank=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="equipos",
        blank=True,
        null=True,
    )
    descripcion = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

# Create your models here.
