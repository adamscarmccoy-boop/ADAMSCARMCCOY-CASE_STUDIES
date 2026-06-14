import json
import os

NOTEBOOK_PATH = "antigravity_horn_audit.ipynb"

if not os.path.exists(NOTEBOOK_PATH):
    print(f"Error: {NOTEBOOK_PATH} not found.")
    exit(1)

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

markdown_source = [
    "# 🎮 Band of Five: Interactive Stem Mastering RPG\n",
    "Run the code cell below to initialize the Infinite Studio session. \n",
    "Work with **The Conductor, Composer, Sound Engineer, Guardian, and Trickster DJ** to master each stem step-by-step. \n",
    "Provide text feedback to adjust the virtual pedalboard settings, or type **'YES'** to approve and advance to the next stem!"
]

code_source = [
    "import sys\n",
    "import os\n",
    "# Ensure project root is in Python path\n",
    "sys.path.insert(0, r\"c:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\")\n",
    "\n",
    "from app.music_game import initialize_game, process_game_input\n",
    "\n",
    "def print_studio_status(sess):\n",
    "    print(\"=\" * 80)\n",
    "    print(f\"\ud83c\udfb5 INFINITE STUDIO SESSION: {sess.track_title}\")\n",
    "    if not sess.game_over:\n",
    "        current = sess.stems[sess.current_stem_index]\n",
    "        print(f\"\ud83c\udf9a\ufe0f Mastering Stem: '{current.name}' ({current.stem_type.upper()}) [{sess.current_stem_index + 1}/{len(sess.stems)}]\")\n",
    "    else:\n",
    "        print(\"\ud83c\udfc6 SESSION MASTERING COMPLETE!\")\n",
    "    print(\"=\" * 80)\n",
    "    \n",
    "    for log in sess.stage_logs:\n",
    "        print(f\"\\n{log['character']}: {log['message']}\")\n",
    "    print(\"-\" * 80)\n",
    "    if not sess.game_over:\n",
    "        print(\"\ud83d\udcac Actions: Type 'YES' to approve, or type adjustments (e.g. 'boost vocals', 'cut low end').\")\n",
    "\n",
    "# 1. Initialize the game session\n",
    "stems_dir = r\"C:\\Users\\adams\\Downloads\\GIRL NAME DREAM -  i need that Stems\"\n",
    "game = initialize_game(\"GIRL NAME DREAM - i need that\", stems_dir)\n",
    "print_studio_status(game)\n"
]

interactive_cell_source = [
    "# Run this cell repeatedly to submit your actions and see the Band's response!\n",
    "# Change the action variable below to submit input:\n",
    "action = \"YES\"\n",
    "\n",
    "game = process_game_input(game, action)\n",
    "print_studio_status(game)\n"
]

# Create cells
md_cell = {
    "cell_type": "markdown",
    "id": "game_title_md",
    "metadata": {},
    "source": markdown_source
}

init_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "game_init_code",
    "metadata": {},
    "outputs": [],
    "source": code_source
}

play_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "game_play_code",
    "metadata": {},
    "outputs": [],
    "source": interactive_cell_source
}

# Append
nb["cells"].append(md_cell)
nb["cells"].append(init_cell)
nb["cells"].append(play_cell)

with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Notebook successfully updated with the interactive Band of Five RPG game cells!")
