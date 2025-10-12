from sqlmodel import Session,delete
from database import engine, init_db
from models import Visita
from datetime import date

init_db()

# visitas = [
#     Visita(vendedor_id=1, cliente="Clínica San Lucas", direccion="Av. Libertad 123",
#            fecha=date(2025, 6, 15), hora="10:00", lat=-34.60, lng=-58.38),
#     Visita(vendedor_id=1, cliente="Hospital Santa María", direccion="Calle Salud 45",
#            fecha=date(2025, 6, 15), hora="11:30", lat=-34.61, lng=-58.39),
#     Visita(vendedor_id=1, cliente="Consultorio Dr. Ramírez", direccion="Calle Sol 89",
#            fecha=date(2025, 6, 15), hora="13:00", lat=-34.63, lng=-58.40),
# ]
visitas = [
    # Día 1 - 10 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Fundación Santa Fe de Bogotá",
        direccion="Carrera 7 #117-15, Usaquén, Bogotá",
        fecha=date(2025, 10, 10),
        hora="09:00",
        lat=4.69546,
        lng=-74.03281
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica del Country",
        direccion="Carrera 16 #82-32, Chapinero, Bogotá",
        fecha=date(2025, 10, 10),
        hora="11:00",
        lat=4.6680624,
        lng=-74.0568885
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital Universitario San Ignacio",
        direccion="Carrera 7 #40-62, Chapinero, Bogotá",
        fecha=date(2025, 10, 10),
        hora="13:00",
        lat=4.62842,
        lng=-74.06417
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Reina Sofía",
        direccion="Calle 127 #20-71, Usaquén, Bogotá",
        fecha=date(2025, 10, 10),
        hora="15:30",
        lat=4.707713,
        lng=-74.046708
    ),

    # Día 2 - 11 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Clínica Universidad de La Sabana",
        direccion="Autopista Norte km 21, Chía (zona metropolitana de Bogotá)",
        fecha=date(2025, 10, 11),
        hora="09:00",
        lat=4.867019,
        lng=-74.041611
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Marly",
        direccion="Carrera 13 #49-90, Chapinero, Bogotá",
        fecha=date(2025, 10, 11),
        hora="11:00",
        lat=4.639958,
        lng=-74.065481
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital Central de la Policía Nacional",
        direccion="Avenida Caracas #66-00, Chapinero, Bogotá",
        fecha=date(2025, 10, 11),
        hora="13:30",
        lat=4.652655,
        lng=-74.073751
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Shaio",
        direccion="Avenida Suba #116-20, Suba, Bogotá",
        fecha=date(2025, 10, 11),
        hora="16:00",
        lat=4.706317,
        lng=-74.070743
    ),

    # Día 3 - 12 de octubre de 2025
    Visita(
        vendedor_id=1,
        cliente="Clínica de Occidente",
        direccion="Avenida de las Américas #71C-29, Kennedy, Bogotá",
        fecha=date(2025, 10, 12),
        hora="09:00",
        lat=4.626998,
        lng=-74.117929
    ),
    Visita(
        vendedor_id=1,
        cliente="Hospital de Suba",
        direccion="Calle 145 #91-19, Suba, Bogotá",
        fecha=date(2025, 10, 12),
        hora="11:00",
        lat=4.7483,
        lng=-74.0863
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Colombia",
        direccion="Carrera 23 #56-60, Teusaquillo, Bogotá",
        fecha=date(2025, 10, 12),
        hora="13:30",
        lat=4.6432,
        lng=-74.0914
    ),
    Visita(
        vendedor_id=1,
        cliente="Clínica Los Nogales",
        direccion="Carrera 25 #78-25, Barrios Unidos, Bogotá",
        fecha=date(2025, 10, 12),
        hora="15:30",
        lat=4.6663,
        lng=-74.0758
    ),
]

with Session(engine) as session:
    session.exec(delete(Visita))
    session.commit()

    session.add_all(visitas)
    session.commit()
    print("✅ Datos iniciales cargados.")