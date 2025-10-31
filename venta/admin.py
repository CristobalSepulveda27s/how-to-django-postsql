from django.contrib import admin
from .models import Producto, Cliente, Venta, DetalleVenta

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    autocomplete_fields = ['producto']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'sku', 'precio', 'stock', 'activo']
    list_editable = ['precio', 'stock', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'sku']
    ordering = ['nombre']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email']
    search_fields = ['nombre']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'fecha', 'anulada', 'total']
    list_filter = ['anulada', 'fecha']
    inlines = [DetalleVentaInline]
    autocomplete_fields = ['cliente']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Al editar
            return ['fecha']
        return []

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    autocomplete_fields = ['producto']