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
    Visita(
        vendedor_id=1,
        cliente="Fundación Santa Fe de Bogotá",
        direccion="Carrera 7 #117-15, Usaquén, Bogotá",
        fecha=date(2025, 6, 15),
        hora="10:00",
        lat=4.69546,
        lng=-74.03281
    ),  # coords FSFB (Usaquén)
    Visita(
        vendedor_id=1,
        cliente="Clínica del Country",
        direccion="Carrera 16 #82-32, Chapinero, Bogotá",
        fecha=date(2025, 6, 15),
        hora="11:30",
        lat=4.6680624,
        lng=-74.0568885
    ),  # coords Clínica del Country
    Visita(
        vendedor_id=1,
        cliente="Hospital Universitario San Ignacio",
        direccion="Carrera 7 #40-62, Chapinero, Bogotá",
        fecha=date(2025, 6, 15),
        hora="13:00",
        lat=4.62842,
        lng=-74.06417
    ),  # coords HUSI (Javeriana)
]

with Session(engine) as session:
    session.exec(delete(Visita))
    session.commit()

    session.add_all(visitas)
    session.commit()
    print("✅ Datos iniciales cargados.")