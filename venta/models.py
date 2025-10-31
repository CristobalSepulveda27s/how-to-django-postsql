from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse

class Producto(models.Model):
    nombre = models.CharField(max_length=120, db_index=True, verbose_name="Nombre")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.sku})"
    
    def get_absolute_url(self):
        return reverse('producto_detail', kwargs={'pk': self.pk})
    
    def puede_vender(self, cantidad):
        """Verifica si hay stock suficiente para vender"""
        return self.activo and self.stock >= cantidad

class Cliente(models.Model):
    nombre = models.CharField(max_length=120, verbose_name="Nombre completo")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('cliente_detail', kwargs={'pk': self.pk})

class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de venta")
    anulada = models.BooleanField(default=False, verbose_name="Anulada")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Venta #{self.pk} — {self.cliente}"
    
    @property
    def total(self):
        """Calcula el total sumando todos los detalles"""
        return sum(d.subtotal for d in self.detalles.all())
    
    @property
    def cantidad_items(self):
        """Retorna la cantidad total de items en la venta"""
        return sum(d.cantidad for d in self.detalles.all())
    
    def anular(self):
        """Método para anular la venta y liberar stock"""
        if not self.anulada:
            # Liberar stock de los productos
            for detalle in self.detalles.all():
                detalle.producto.stock += detalle.cantidad
                detalle.producto.save()
            self.anulada = True
            self.save()

class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta, 
        related_name='detalles', 
        on_delete=models.CASCADE,
        verbose_name="Venta"
    )
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio unitario"
    )
    
    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"
    
    def __str__(self):
        return f"{self.producto} x{self.cantidad}"
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def save(self, *args, **kwargs):
        """Antes de guardar, actualizar el stock del producto"""
        if self.pk:  # Si es una actualización
            detalle_anterior = DetalleVenta.objects.get(pk=self.pk)
            diferencia = self.cantidad - detalle_anterior.cantidad
            self.producto.stock -= diferencia
        else:  # Si es nuevo
            self.producto.stock -= self.cantidad
        
        self.producto.save()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Al eliminar, devolver el stock al producto"""
        self.producto.stock += self.cantidad
        self.producto.save()
        super().delete(*args, **kwargs)