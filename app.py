import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import db
from models import Unidad

# NOTA: Ya no necesitamos google_creds ni gspread

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_super_secreta_varela')
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- 1. NUEVA LÓGICA: Carga de Excel (.xlsx) ---
@app.route('/admin/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No se subió ningún archivo", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Nombre de archivo vacío", 400

    if file:
        try:
            # Leemos el Excel usando Pandas
            # dtype=str asegura que todo se lea como texto (evita problemas con números/fechas)
            df = pd.read_excel(file, dtype=str)
            
            # Reemplazar valores NaN (vacíos de Excel) por string vacío ""
            df = df.fillna("")
            
            # Limpiar DB actual para evitar duplicados
            db.session.query(Unidad).delete()
            
            # Iterar sobre las filas del Excel
            for index, row in df.iterrows():
                # Convertimos la fila a diccionario
                data = row.to_dict()
                
                # Definimos columnas fijas (Las mismas 17 de antes)
                # IMPORTANTE: Los encabezados en tu Excel deben ser exactos (Mayúsculas)
                fixed_keys = ['ID', 'TIPO', 'MARCA', 'MODELO', 'DOMINIO', 'AÑO', 'ESTADO', 
                              'FOTO_URL', 'AREA', 'MOTOR', 'CHASIS', 'PATRIMONIO', 
                              'CHOFER', 'LEGAJO', 'DNI', 'FECHA_ALTA', 'NFC_KEY']
                
                # Todo lo que no sea fijo, va al JSONB
                detalles = {k: v for k, v in data.items() if k not in fixed_keys and v != ""}
                
                nueva_unidad = Unidad(
                    id=str(data.get('ID')),
                    tipo=data.get('TIPO'),
                    marca=data.get('MARCA'),
                    modelo=data.get('MODELO'),
                    dominio=data.get('DOMINIO'),
                    anio=int(data.get('AÑO')) if data.get('AÑO').isdigit() else 0,
                    estado=data.get('ESTADO'),
                    foto_url=data.get('FOTO_URL'),
                    area=data.get('AREA'),
                    motor=data.get('MOTOR'),
                    chasis=data.get('CHASIS'),
                    patrimonio=data.get('PATRIMONIO'),
                    chofer=data.get('CHOFER'),
                    legajo=data.get('LEGAJO'),
                    dni=data.get('DNI'),
                    fecha_alta=data.get('FECHA_ALTA'),
                    nfc_key=str(data.get('NFC_KEY')),
                    detalles_tecnicos=detalles
                )
                db.session.add(nueva_unidad)
            
            db.session.commit()
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            return f"Error procesando el Excel: {str(e)}", 500

# --- 2. Rutas del Sistema (IGUAL QUE ANTES) ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    unidades = Unidad.query.all()
    total = len(unidades)
    activos = Unidad.query.filter_by(estado='ACTIVA').count()
    inactivos = Unidad.query.filter_by(estado='INACTIVA').count()
    operatividad = round((activos / total * 100), 1) if total > 0 else 0
    
    return render_template('dashboard.html', 
                           unidades=unidades, 
                           stats={'total': total, 'activos': activos, 'inactivos': inactivos, 'oper': operatividad})

@app.route('/ficha/<unidad_id>')
def ficha_tecnica(unidad_id):
    unidad = Unidad.query.get_or_404(unidad_id)
    return render_template('ficha.html', u=unidad)

@app.route('/api/validate-nfc', methods=['POST'])
def validate_nfc():
    data = request.json
    nfc_input = data.get('nfc_key')
    unidad = Unidad.query.filter_by(nfc_key=nfc_input).first()
    if unidad:
        return jsonify({'success': True, 'msg': f'Acceso Permitido: {unidad.marca} {unidad.modelo}', 'id': unidad.id})
    else:
        return jsonify({'success': False, 'msg': 'Llave NFC no reconocida'}), 403

@app.route('/setup/create-db')
def create_tables():
    db.create_all()
    return "Tablas creadas en PostgreSQL"

# --- AGREGAR AL FINAL DE app.py (Antes del __main__) ---

# Ruta para ver el Taller
@app.route('/taller')
def taller():
    unidad_id = request.args.get('id')
    unidad = None
    if unidad_id:
        # Busca por ID o por Dominio (Patente)
        unidad = Unidad.query.filter(
            (Unidad.id == unidad_id) | (Unidad.dominio == unidad_id)
        ).first()
    return render_template('taller.html', unidad=unidad)

# Ruta para procesar el cambio de estado (Solo funciona si viene con NFC)
@app.route('/taller/cambiar_estado', methods=['POST'])
def cambiar_estado():
    unidad_id = request.form.get('unidad_id')
    nuevo_estado = request.form.get('nuevo_estado')
    justificacion = request.form.get('justificacion')
    nfc_auth = request.form.get('nfc_autorizante')

    # Validación de Seguridad Backend:
    # Si alguien intenta enviar el form sin haber pasado por el modal NFC,
    # el campo nfc_autorizante estará vacío.
    if not nfc_auth:
        flash('ERROR DE SEGURIDAD: Se requiere validación física NFC.', 'error')
        return redirect(url_for('taller', id=unidad_id))

    unidad = Unidad.query.get(unidad_id)
    if unidad:
        unidad.estado = nuevo_estado
        # Aquí podrías guardar la 'justificacion' en una tabla de historial de eventos
        # Por ahora, actualizamos el estado y guardamos en DB
        db.session.commit()
        # Usamos flash (necesitas configurar secret_key) o un print simple
        print(f"Estado actualizado por {nfc_auth}: {justificacion}")
        
    return redirect(url_for('taller', id=unidad_id))

if __name__ == '__main__':

    app.run(debug=True)

