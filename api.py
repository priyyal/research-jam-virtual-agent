from flask import Flask, request, jsonify
from main import Game
import multiprocessing

app = Flask(__name__)

game_process = None

# --- Function must be top-level (not inside route) ---
def run_game(width, height, num_levels, participant_id):
	game = Game(width, height, num_levels=num_levels, participant_id=participant_id)
	game.run()


@app.route('/')
def home():
	return jsonify({"message": "Game API is running!"})

@app.route('/start_game', methods=['POST'])
def start_game():
	global game_process

	# If a game is already running, don't start another
	if game_process is not None and game_process.is_alive():
		return jsonify({"error": "A game is already running"}), 400

	data = request.get_json() or {}
	width = data.get("width", 800)
	height = data.get("height", 800)
	num_levels = data.get("num_levels", 3)
	participant_id = data.get("participant_id", "UNKNOWN")

	# Start the game as a separate process
	game_process = multiprocessing.Process(
		target=run_game,
		args=(width, height, num_levels, participant_id)
	)
	game_process.start()

	return jsonify({"status": "Game launched successfully!"}), 200

@app.route('/get_status', methods=['GET'])
def get_status():
	return jsonify({"message": "Status tracking coming next."})

if __name__ == '__main__':
	multiprocessing.set_start_method("spawn")  # Required on macOS
	app.run(host='0.0.0.0', port=4000)
