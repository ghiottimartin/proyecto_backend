# Generated by Django 3.2.4 on 2021-10-19 20:17

from django.db import migrations

from django.db import migrations
import datetime


def agregar_productos(apps, schema_editor):
    Categoria = apps.get_model('producto', 'Categoria')
    Producto = apps.get_model('producto', 'Producto')

    bebidas = Categoria(nombre='Bebidas')
    bebidas.save()

    hamburguesas = Categoria(nombre='Hamburguesas')
    hamburguesas.save()

    cervezas = Categoria(nombre='Cervezas')
    cervezas.save()

    lomitos = Categoria(nombre='Lomitos')
    lomitos.save()

    panaderia = Categoria(nombre='Panaderia')
    panaderia.save()

    pizzas = Categoria(nombre='Pizzas')
    pizzas.save()

    agua = Producto(categoria=bebidas, nombre='Agua sin gas 0.5L', compra_directa=True, venta_directa=True, stock=0,
        costo_vigente=200, precio_vigente=250,
        imagen='producto/agua-sin-gas.jpg', imagen_nombre='agua-sin-gas.jpg',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    agua.save()

    cervezaSF = Producto(categoria=cervezas, nombre='Cerveza Santa Fe 473ml', compra_directa=True, venta_directa=True, stock=0,
        costo_vigente=100, precio_vigente=150,
        imagen='producto/cerveza-santa-fe.jpg', imagen_nombre='cerveza-santa-fe.jpg',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    cervezaSF.save()

    cervezaStella = Producto(categoria=cervezas, nombre='Cerveza Stella 473ml', compra_directa=True, venta_directa=True,
        stock=0,
        costo_vigente=150, precio_vigente=200,
        imagen='producto/cerveza-stella.png', imagen_nombre='cerveza-stella.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    cervezaStella.save()

    cocaCola = Producto(categoria=bebidas, nombre='Coca Cola 500ml', compra_directa=True, venta_directa=True,
        stock=0,
        costo_vigente=150, precio_vigente=200,
        imagen='producto/coca-cola.jpg', imagen_nombre='coca-cola.jpg',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    cocaCola.save()

    fanta = Producto(categoria=bebidas, nombre='Fanta 500ml', compra_directa=True, venta_directa=True,
        stock=0,
        costo_vigente=100, precio_vigente=180,
        imagen='producto/fanta.png', imagen_nombre='fanta.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    fanta.save()

    hamburguesa = Producto(categoria=hamburguesas, nombre='Hamburguesa completa', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=500, precio_vigente=600,
        imagen='producto/hamburguesa.png', imagen_nombre='hamburguesa.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    hamburguesa.save()

    lomito = Producto(categoria=lomitos, nombre='Lomito simple', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=650,
        imagen='producto/lomito.png', imagen_nombre='lomito.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    lomito.save()

    lomitoPapas = Producto(categoria=lomitos, nombre='Lomito con papas', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=650, precio_vigente=750,
        imagen='producto/lomito_papas.png', imagen_nombre='lomito_papas.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    lomitoPapas.save()

    pizza4Quesos = Producto(categoria=pizzas, nombre='Pizza 4 Quesos', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=500, precio_vigente=550,
        imagen='producto/pizza-4-quesos.png', imagen_nombre='pizza-4-quesos.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizza4Quesos.save()

    pizzaCalabresa = Producto(categoria=pizzas, nombre='Pizza Calabresa', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=600,
        imagen='producto/pizza-calabresa.png', imagen_nombre='pizza-calabresa.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizzaCalabresa.save()

    pizzaEspecial = Producto(categoria=pizzas, nombre='Pizza Especial', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=600,
        imagen='producto/pizza-especial.png', imagen_nombre='pizza-especial.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizzaEspecial.save()

    pizzaFugazeta = Producto(categoria=pizzas, nombre='Pizza Fugazeta', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=600,
        imagen='producto/pizza-fugazeta.jfif', imagen_nombre='pizza-fugazeta.jfif',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizzaFugazeta.save()

    pizzaMuzarella = Producto(categoria=pizzas, nombre='Pizza Muzarella', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=600,
        imagen='producto/pizza-muzarella.png', imagen_nombre='pizza-muzarella.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizzaMuzarella.save()

    pizzaPollo = Producto(categoria=pizzas, nombre='Pizza Pollo', compra_directa=False, venta_directa=True,
        stock=0,
        costo_vigente=550, precio_vigente=600,
        imagen='producto/pizza-pollo.png', imagen_nombre='pizza-pollo.png',
        auditoria_creado_fecha=datetime.datetime.now(),
        auditoria_modificado_fecha=datetime.datetime.now()
    )
    pizzaPollo.save()


def borrar_productos(apps, schema_editor):
    Producto = apps.get_model('producto', 'Producto')
    Producto.objects.all().delete()

    Categoria = apps.get_model('producto', 'Categoria')
    Categoria.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0002_movimientostock'),
    ]

    operations = [
        migrations.RunPython(agregar_productos, borrar_productos),
    ]