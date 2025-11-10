from flask import Flask, request, jsonify, render_template_string
from main import Game
import multiprocessing
import os

app = Flask(__name__)

current_process = None
counter_file = "data/participant_counter.txt"

# Ensure counter exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(counter_file):
	with open(counter_file, "w") as f:
		f.write("1")


def next_participant_id():
	with open(counter_file, "r+") as f:
		value = int(f.read().strip())
		new_value = value + 1
		f.seek(0)
		f.write(str(new_value))
		f.truncate()
	return f"P-{value:05d}"   # Format: P-00001


def run_game(width, height, num_levels, participant_id):
	game = Game(width, height, num_levels=num_levels, participant_id=participant_id)
	game.run()


@app.route('/ui')
def ui():
	return render_template_string("""
    <html>
      <body style="font-family:Arial; padding:40px;">
        <h2>Experiment Control Panel</h2>

        <label>Number of Hallways:</label>
        <input id="levels" type="number" value="3" min="1" max="10"><br><br>

        <button onclick="startGame()">Start Session</button>
        <button onclick="stopGame()" style="color:red; margin-left:20px;">STOP GAME</button>

        <script>
        function startGame() {
          const levels = document.getElementById('levels').value;
          fetch('/start_game', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({num_levels: parseInt(levels)})
          })
          .then(r=>r.json())
          .then(d=>alert("Started Participant: " + d.participant_id));
        }

        function stopGame() {
          fetch('/stop_game', {method:'POST'})
          .then(r=>r.json())
          .then(d=>alert(d.status));
        }
        </script>
      </body>
    </html>
    """)


@app.route('/start_game', methods=['POST'])
def start_game():
	global current_process

	if current_process and current_process.is_alive():
		return jsonify({"error": "A session is already running"}), 400

	data = request.get_json() or {}
	num_levels = data.get("num_levels", 3)

	participant_id = next_participant_id()

	current_process = multiprocessing.Process(
		target=run_game,
		args=(800, 800, num_levels, participant_id)
	)
	current_process.start()

	return jsonify({"status": "Game started", "participant_id": participant_id}), 200


@app.route('/stop_game', methods=['POST'])
def stop_game():
	global current_process
	if current_process and current_process.is_alive():
		current_process.terminate()
		current_process.join()
		current_process = None
		return jsonify({"status": "Game stopped"}), 200
	return jsonify({"status": "No game running"}), 400


if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")
	app.run(host='0.0.0.0', port=4000)
