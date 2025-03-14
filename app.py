import eventlet
eventlet.monkey_patch()  # 🔹 Aplica el parche antes de importar Flask

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import random

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
    return [[columnas['B'][i], columnas['I'][i], columnas['N'][i], columnas['G'][i], columnas['O'][i]] for i in
            range(5)]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("🔍 Datos recibidos en POST:", request.form)  # Depuración

        num_jugadores = int(request.form.get("num_jugadores", 1))
        modo_juego = request.form.get("modo_juego", "linea_horizontal")

        session.clear()  # Borra datos antiguos antes de iniciar un nuevo juego
        session['modo_juego'] = modo_juego
        session['jugadores'] = {f"Jugador {i + 1}": generar_carton() for i in range(num_jugadores)}
        session['bolas'] = list(range(1, 76))
        random.shuffle(session['bolas'])
        session.modified = True

        print("Jugadores y cartones:", session['jugadores'])  # Depuración
        return render_template("index.html", jugadores=session['jugadores'])
    return render_template("inicio.html")

@socketio.on('extraer_numero')
def extraer_numero():
    with app.app_context():  # Asegura el contexto de Flask
        if 'bolas' in session and session['bolas']:
            numero = session['bolas'].pop(0)

            jugadores = session.get('jugadores', {})
            for jugador, carton in jugadores.items():
                for fila in carton:
                    for i in range(5):
                        if fila[i] == numero:
                            fila[i] = "X"

            session['jugadores'] = jugadores
            session.modified = True

            emit("numero_extraido", {"numero": numero}, broadcast=True)

        verificar_ganador()  # 💡 Mueve esta línea FUERA del bloque "with"


@socketio.on('verificar_ganador')
def verificar_ganador():
    jugadores = session.get('jugadores', {})
    modo_juego = session.get('modo_juego', "linea_horizontal")  # Obtener el modo de juego seleccionado

    for jugador, carton in jugadores.items():
        if verificar_carton(carton, modo_juego):
            emit("ganador", {"ganador": jugador}, broadcast=True)
            return

# Función para verificar si un cartón ha ganado
def verificar_carton(carton, modo):
    print("Verificando cartón:", carton, "Modo de juego:", modo)  # Depuración en la terminal

    if modo == "linea_horizontal":
        for i in range(5):
            if all(cell == "X" for cell in carton[i]):
                return True
    elif modo == "linea_vertical":
        for i in range(5):
            if all(carton[j][i] == "X" for j in range(5)):
                return True
    elif modo == "diagonal":
        if all(carton[i][i] == "X" for i in range(5)) or all(carton[i][4 - i] == "X" for i in range(5)):
            return True
    elif modo == "carton_completo":
        if all(all(cell == "X" for cell in row) for row in carton):
            return True

    return False

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, use_reloader=False)






