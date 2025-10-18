#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de ejemplo
HU07: Consultar Cliente - Datos iniciales
"""
import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio app al path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.db import get_session, create_tables
from app.models import (
    Cliente, CompraHistorico, DevolucionHistorico, 
    ConsultaClienteLog, ProductoPreferido, EstadisticaCliente
)
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import text


async def populate_database():
    """Poblar la base de datos con datos de ejemplo"""
    print("🔄 Poblando base de datos con datos de ejemplo...")
    
    # Crear tablas primero
    await create_tables()
    
    async for session in get_session():
        try:
            # Verificar si ya hay datos
            existing_clients = await session.execute(text("SELECT COUNT(*) FROM cliente"))
            count = existing_clients.scalar()
            
            if count > 0:
                print(f"ℹ️  Base de datos ya tiene {count} clientes. Saltando población de datos.")
                return
            
            # === POBLAR CLIENTES ===
            clientes = [
                Cliente(
                    id="CLI001",
                    nit="900123456-7",
                    nombre="Farmacia San José",
                    codigo_unico="FSJ001",
                    email="contacto@farmaciasanjose.com",
                    telefono="+57-1-2345678",
                    direccion="Calle 45 #12-34",
                    ciudad="Bogotá",
                    pais="CO",
                    activo=True
                ),
                Cliente(
                    id="CLI002",
                    nit="800987654-3",
                    nombre="Droguería El Buen Pastor",
                    codigo_unico="DBP002",
                    email="ventas@elbunpastor.com",
                    telefono="+57-2-9876543",
                    direccion="Carrera 15 #67-89",
                    ciudad="Medellín",
                    pais="CO",
                    activo=True
                ),
                Cliente(
                    id="CLI003",
                    nit="700456789-1",
                    nombre="Farmatodo Zona Norte",
                    codigo_unico="FZN003",
                    email="info@farmatodo.com",
                    telefono="+57-5-4567890",
                    direccion="Avenida Norte #23-45",
                    ciudad="Barranquilla",
                    pais="CO",
                    activo=True
                ),
                Cliente(
                    id="CLI004",
                    nit="600345678-9",
                    nombre="Centro Médico Salud Total",
                    codigo_unico="CST004",
                    email="compras@saludtotal.com",
                    telefono="+57-1-3456789",
                    direccion="Calle 85 #34-56",
                    ciudad="Bogotá",
                    pais="CO",
                    activo=True
                ),
                Cliente(
                    id="CLI005",
                    nit="500234567-5",
                    nombre="Farmacia Popular",
                    codigo_unico="FPO005",
                    email="pedidos@farmapopular.com",
                    telefono="+57-4-2345678",
                    direccion="Carrera 70 #45-67",
                    ciudad="Medellín",
                    pais="CO",
                    activo=True
                )
            ]
            
            for cliente in clientes:
                session.add(cliente)
            
            await session.commit()
            print(f"✅ {len(clientes)} clientes agregados")
            
            # === POBLAR HISTORIAL DE COMPRAS ===
            compras = [
                # Cliente CLI001 - Farmacia San José (comprador frecuente de Acetaminofén)
                CompraHistorico(
                    id="COMP001", cliente_id="CLI001", orden_id="ORD2024001",
                    estado_orden="completada", producto_id="ACETA500",
                    producto_nombre="Acetaminofén 500mg x 20 tabletas",
                    categoria_producto="Analgésicos", cantidad=50,
                    precio_unitario=Decimal("1200.00"), precio_total=Decimal("60000.00"),
                    fecha_compra=date.today() - timedelta(days=25)
                ),
                CompraHistorico(
                    id="COMP002", cliente_id="CLI001", orden_id="ORD2024002",
                    estado_orden="completada", producto_id="IBUPRO400",
                    producto_nombre="Ibuprofeno 400mg x 20 cápsulas",
                    categoria_producto="Antiinflamatorios", cantidad=30,
                    precio_unitario=Decimal("1800.00"), precio_total=Decimal("54000.00"),
                    fecha_compra=date.today() - timedelta(days=30)
                ),
                CompraHistorico(
                    id="COMP003", cliente_id="CLI001", orden_id="ORD2024003",
                    estado_orden="completada", producto_id="ACETA500",
                    producto_nombre="Acetaminofén 500mg x 20 tabletas",
                    categoria_producto="Analgésicos", cantidad=75,
                    precio_unitario=Decimal("1200.00"), precio_total=Decimal("90000.00"),
                    fecha_compra=date.today() - timedelta(days=50)
                ),
                CompraHistorico(
                    id="COMP004", cliente_id="CLI001", orden_id="ORD2024004",
                    estado_orden="completada", producto_id="OMEPRA20",
                    producto_nombre="Omeprazol 20mg x 14 cápsulas",
                    categoria_producto="Gastroprotectores", cantidad=20,
                    precio_unitario=Decimal("3500.00"), precio_total=Decimal("70000.00"),
                    fecha_compra=date.today() - timedelta(days=55)
                ),
                
                # Cliente CLI002 - Droguería El Buen Pastor
                CompraHistorico(
                    id="COMP005", cliente_id="CLI002", orden_id="ORD2024005",
                    estado_orden="completada", producto_id="IBUPRO400",
                    producto_nombre="Ibuprofeno 400mg x 20 cápsulas",
                    categoria_producto="Antiinflamatorios", cantidad=40,
                    precio_unitario=Decimal("1800.00"), precio_total=Decimal("72000.00"),
                    fecha_compra=date.today() - timedelta(days=28)
                ),
                CompraHistorico(
                    id="COMP006", cliente_id="CLI002", orden_id="ORD2024006",
                    estado_orden="completada", producto_id="AMOXIC500",
                    producto_nombre="Amoxicilina 500mg x 21 cápsulas",
                    categoria_producto="Antibióticos", cantidad=15,
                    precio_unitario=Decimal("4200.00"), precio_total=Decimal("63000.00"),
                    fecha_compra=date.today() - timedelta(days=35)
                ),
                
                # Cliente CLI003 - Farmatodo Zona Norte  
                CompraHistorico(
                    id="COMP007", cliente_id="CLI003", orden_id="ORD2024007",
                    estado_orden="completada", producto_id="ACETA500",
                    producto_nombre="Acetaminofén 500mg x 20 tabletas",
                    categoria_producto="Analgésicos", cantidad=80,
                    precio_unitario=Decimal("1200.00"), precio_total=Decimal("96000.00"),
                    fecha_compra=date.today() - timedelta(days=32)
                )
            ]
            
            for compra in compras:
                session.add(compra)
            
            await session.commit()
            print(f"✅ {len(compras)} compras agregadas")
            
            # === POBLAR DEVOLUCIONES ===
            devoluciones = [
                DevolucionHistorico(
                    id="DEV001", cliente_id="CLI001", compra_id="COMP002",
                    compra_orden_id="ORD2024002", producto_id="IBUPRO400",
                    producto_nombre="Ibuprofeno 400mg x 20 cápsulas",
                    cantidad_devuelta=5,
                    motivo="Producto próximo a vencer - fecha de vencimiento muy cercana",
                    categoria_motivo="vencimiento", estado="procesada",
                    fecha_devolucion=date.today() - timedelta(days=20)
                ),
                DevolucionHistorico(
                    id="DEV002", cliente_id="CLI003", compra_id="COMP007",
                    compra_orden_id="ORD2024007", producto_id="ACETA500",
                    producto_nombre="Acetaminofén 500mg x 20 tabletas",
                    cantidad_devuelta=8,
                    motivo="Producto vencido al momento de la entrega",
                    categoria_motivo="vencimiento", estado="procesada",
                    fecha_devolucion=date.today() - timedelta(days=25)
                )
            ]
            
            for devolucion in devoluciones:
                session.add(devolucion)
                
            await session.commit()
            print(f"✅ {len(devoluciones)} devoluciones agregadas")
            
            # === POBLAR LOGS DE CONSULTA (para trazabilidad) ===
            logs = [
                ConsultaClienteLog(
                    vendedor_id="VEN001", cliente_id="CLI001",
                    tipo_consulta="busqueda_cliente", tipo_busqueda="nit",
                    termino_busqueda="900123456-7", took_ms=850,
                    cumple_sla=True,
                    metadatos={"resultado_encontrado": True, "cliente_nombre": "Farmacia San José"}
                ),
                ConsultaClienteLog(
                    vendedor_id="VEN001", cliente_id="CLI001",
                    tipo_consulta="historico_completo", took_ms=1200,
                    cumple_sla=True,
                    metadatos={"limite_meses": 12, "total_compras": 4, "total_devoluciones": 1}
                ),
                ConsultaClienteLog(
                    vendedor_id="VEN002", cliente_id="CLI003",
                    tipo_consulta="busqueda_cliente", tipo_busqueda="codigo",
                    termino_busqueda="FZN003", took_ms=400,
                    cumple_sla=True,
                    metadatos={"resultado_encontrado": True, "cliente_nombre": "Farmatodo Zona Norte"}
                )
            ]
            
            for log in logs:
                session.add(log)
            
            await session.commit()
            print(f"✅ {len(logs)} logs de consulta agregados")
            
            print("🎉 Base de datos poblada exitosamente con datos de ejemplo")
            print("\n📋 Datos disponibles para probar:")
            print("   • 5 clientes de diferentes tipos")
            print("   • 7 compras con productos variados")  
            print("   • 2 devoluciones con motivos reales")
            print("   • 3 logs de consulta para trazabilidad")
            print("\n🧪 Puedes probar los endpoints:")
            print("   • GET /api/v1/cliente/search?q=900123456-7&vendedor_id=VEN001")
            print("   • GET /api/v1/cliente/CLI001/historico?vendedor_id=VEN001")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al poblar base de datos: {e}")
            raise
        
        finally:
            await session.close()


if __name__ == "__main__":
    print("🚀 Iniciando población de base de datos...")
    
    try:
        asyncio.run(populate_database())
        print("✅ Población completada exitosamente")
    except Exception as e:
        print(f"❌ Error durante la población: {e}")
        sys.exit(1)