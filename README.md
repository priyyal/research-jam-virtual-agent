# Research Jam: Virtual Agent Trust Game

An experimental **Pac-Man–style trust game** built with Python + Pygame.  
The game is used to study how **agent appearance (male / female / neutral)** influences whether players **trust or ignore advice** when making fast decisions.

---

## 🎮 Gameplay (prototype)
1. Navigate a simple Pac-Man–like maze.
2. Enter a hallway with two doors (left/right).
3. A randomized **agent** (sprite: male, female, or neutral) appears and advises a door.
4. You decide:
    - Correct → no health loss.
    - Wrong → health/poison penalty.
5. Repeat across multiple agents and levels.

**Planned mechanics:**
- Variable hallway pause time
- “Peek” briefly behind doors
- Agents that sometimes lie (configurable %)
- Audio-based “threat” to increase time pressure
- Logging of decisions, reaction time, health changes

---

## ⚙️ Tech
- Python ≥ 3.12
- [Pygame](https://www.pygame.org/) ≥ 2.6

---

## 🚀 Setup & Run
```bash
# create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# install deps
pip install -U pip
pip install -e .

# run the game
python main.py
