from database import db
from sqlalchemy.dialects.postgresql import JSONB

class Unidad(db.Model):
    __tablename__ = 'unidades'

    # Columnas Fijas (1-17 según especificación)
    id = db.Column(db.String(50), primary_key=True) # ID Municipal
    tipo = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    dominio = db.Column(db.String(20))
    anio = db.Column(db.Integer)
    estado = db.Column(db.String(50)) # ACTIVA / INACTIVA / TALLER
    foto_url = db.Column(db.Text)
    area = db.Column(db.String(100))
    motor = db.Column(db.String(100))
    chasis = db.Column(db.String(100))
    patrimonio = db.Column(db.String(100))
    chofer = db.Column(db.String(100))
    legajo = db.Column(db.String(50))
    dni = db.Column(db.String(20))
    fecha_alta = db.Column(db.String(20))
    nfc_key = db.Column(db.String(100), unique=True) # Llave de acceso

    # Lógica Dinámica: Aquí van la columna 18 en adelante (Altura, CV, etc.)
    detalles_tecnicos = db.Column(JSONB)

    def to_dict(self):
        return {
            'id': self.id,
            'marca': self.marca,
            'modelo': self.modelo,
            'estado': self.estado,
            'nfc_key': self.nfc_key
        }