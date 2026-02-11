from flask import Flask, request, jsonify, render_template_string
from main import Game
import multiprocessing
import os

app = Flask(__name__)

current_process = None
current_settings = {}
counter_file = "data/participant_counter.txt"

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
	return f"P-{value:05d}"


def run_game(width, height, num_levels, participant_id,
			 time_per_hallway, enemy_speed, assistant_type,
			 round_times, wrong_penalty, seed, gender_sequence, agent_accuracy, unify_names):
	game = Game(
		width, height,
		num_levels=num_levels,
		participant_id=participant_id,
		time_per_hallway=time_per_hallway,
		enemy_speed=enemy_speed,
		assistant_type=assistant_type,
		round_times=round_times,
		wrong_penalty=wrong_penalty,
		seed=seed,
		gender_sequence=gender_sequence,
		agent_accuracy=agent_accuracy,
		unify_names=unify_names
	)
	game.run()


@app.route("/start_game", methods=["POST"])
def start_game():
	global current_process, current_settings

	if current_process and current_process.is_alive():
		return jsonify({"error": "A session is already running"}), 400

	data = request.get_json(silent=True) or {}

	# defaults
	width = 800
	height = 800
	num_levels = int(data.get("num_levels", 3))
	time_per_hallway = int(data.get("time_per_hallway", 50))
	enemy_speed = int(data.get("enemy_speed", 500))
	assistant_type = data.get("assistant_type", "mixed")

	# existing knobs
	round_times = data.get("round_times", [90, 60, 40])
	wrong_penalty = int(data.get("wrong_penalty", 5))
	seed = data.get("seed", None)

	gender_sequence = (data.get("gender_sequence") or "MFN").upper()
	agent_accuracy = int(data.get("agent_accuracy", 50))
	unify_names = bool(data.get("unify_names", True))

	allowed_sequences = {"MFN", "MNF", "FMN", "FNM", "NMF", "NFM"}
	if gender_sequence not in allowed_sequences:
		return jsonify({"error": f"gender_sequence must be one of {sorted(allowed_sequences)}"}), 400

	if agent_accuracy not in (0, 50, 100):
		return jsonify({"error": "agent_accuracy must be one of [0, 50, 100]"}), 400

	# allow overriding participant_id (optional)
	participant_id = data.get("participant_id") or next_participant_id()

	# sanitize / validate a bit
	if not isinstance(round_times, list) or len(round_times) == 0:
		return jsonify({"error": "round_times must be a non-empty list, e.g. [90,60,40]"}), 400
	round_times = [int(x) for x in round_times]

	if seed is not None:
		seed = int(seed)

	current_settings = {
		"width": width,
		"height": height,
		"num_levels": num_levels,
		"participant_id": participant_id,
		"time_per_hallway": time_per_hallway,
		"enemy_speed": enemy_speed,
		"assistant_type": assistant_type,
		"round_times": round_times,
		"wrong_penalty": wrong_penalty,
		"seed": seed,
		"gender_sequence": gender_sequence,
		"agent_accuracy": agent_accuracy,
		"unify_names": unify_names,
	}

	current_process = multiprocessing.Process(
		target=run_game,
		args=(
			width, height,
			num_levels,
			participant_id,
			time_per_hallway,
			enemy_speed,
			assistant_type,
			round_times,
			wrong_penalty,
			seed,
			gender_sequence,
			agent_accuracy,
			unify_names,
		),
	)
	current_process.start()

	return jsonify({"status": "Game started", "settings": current_settings}), 200


@app.route("/get_status", methods=["GET"])
def get_status():
	running = current_process is not None and current_process.is_alive()
	return jsonify({"running": running, "settings": current_settings or {}}), 200


@app.route("/stop_game", methods=["POST"])
def stop_game():
	global current_process
	if current_process and current_process.is_alive():
		current_process.terminate()
		current_process.join()
		current_process = None
		return jsonify({"status": "Game stopped"}), 200
	return jsonify({"status": "No game running"}), 400


if __name__ == "__main__":
	multiprocessing.set_start_method("spawn")
	app.run(host="0.0.0.0", port=4000)
