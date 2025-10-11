from sqlmodel import Session,delete
from database import engine, init_db
from models import Visita
from datetime import date

init_db()

visitas = [
    Visita(vendedor_id=1, cliente="Clínica San Lucas", direccion="Av. Libertad 123",
           fecha=date(2025, 6, 15), hora="10:00", lat=-34.60, lng=-58.38),
    Visita(vendedor_id=1, cliente="Hospital Santa María", direccion="Calle Salud 45",
           fecha=date(2025, 6, 15), hora="11:30", lat=-34.61, lng=-58.39),
    Visita(vendedor_id=1, cliente="Consultorio Dr. Ramírez", direccion="Calle Sol 89",
           fecha=date(2025, 6, 15), hora="13:00", lat=-34.63, lng=-58.40),
]

with Session(engine) as session:
    session.exec(delete(Visita))
    session.commit()

    session.add_all(visitas)
    session.commit()
    print("✅ Datos iniciales cargados.")