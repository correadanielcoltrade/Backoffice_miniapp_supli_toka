"""Crea automaticamente el registro de inventario al crear un producto."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.catalog.models import Product

from .models import Inventory


@receiver(post_save, sender=Product)
def create_inventory_for_product(sender, instance, created, **kwargs):
    if created:
        Inventory.objects.get_or_create(product=instance)
