import eventlet
eventlet.monkey_patch()  # Aplica el parche antes de importar Flask

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import random
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "bingo_secret"
socketio = SocketIO(app)

# Función para generar un cartón de Bingo
def generar_carton():
    columnas = {
        'B': random.sample(range(1, 16), 5),
        'I': random.sample(range(16, 31), 5),
        'N': random.sample(range(31, 46), 5),
        'G': random.sample(range(46, 61), 5),
        'O': random.sample(range(61, 76), 5)
    }
    columnas['N'][2] = "X"  # Espacio libre en el centro
    return [list(columnas[col]) for col in ['B', 'I', 'N', 'G', 'O']]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombres_jugadores = request.form.get("nombres_jugadores", "")
        modo_juego = request.form.get("modo_juego", "linea_horizontal")

        # Dividir los nombres por comas y limpiar espacios
        nombres_jugadores = [nombre.strip() for nombre in nombres_jugadores.split(',') if nombre.strip()]
        num_jugadores = len(nombres_jugadores)

        session.clear()  # Borra datos antiguos antes de iniciar un nuevo juego
        session['modo_juego'] = modo_juego
        session['jugadores'] = {nombres_jugadores[i]: generar_carton() for i in range(num_jugadores)}
        session['bolas'] = list(range(1, 76))
        random.shuffle(session['bolas'])

        logging.info("Jugadores y cartones: %s", session['jugadores'])
        return render_template("index.html", jugadores=session['jugadores'])
    return render_template("inicio.html")

@socketio.on('extraer_numero')
def extraer_numero():
    if 'bolas' in session and session['bolas']:
        numero = session['bolas'].pop(0)
        marcar_numero_en_cartones(numero)
        emit("numero_extraido", {"numero": numero}, broadcast=True)
        verificar_ganador()  # Verificar ganador después de extraer el número
    else:
        emit("numero_extraido", {"numero": None}, broadcast=True)

def marcar_numero_en_cartones(numero):
    for jugador, carton in session.get('jugadores', {}).items():
        for fila in carton:
            for i in range(5):
                if fila[i] == numero:
                    fila[i] = "X"

@socketio.on('verificar_ganador')
def verificar_ganador():
    jugadores = session.get('jugadores', {})
    modo_juego = session.get('modo_juego', "linea_horizontal")

    for jugador, carton in jugadores.items():
        if verificar_carton(carton, modo_juego):
            emit("ganador", {"ganador": jugador}, broadcast=True)
            return

def verificar_carton(carton, modo):
    if modo == "linea_horizontal":
        return any(all(cell == "X" for cell in fila) for fila in carton)
    elif modo == "linea_vertical":
        return any(all(carton[j][i] == "X" for j in range(5)) for i in range(5))
    elif modo == "diagonal":
        return (all(carton[i][i] == "X" for i in range(5)) or
                all(carton[i][4 - i] == "X" for i in range(5)))
    elif modo == "carton_completo":
        return all(all(cell == "X" for cell in fila) for fila in carton)
    return False

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, use_reloader=False)













