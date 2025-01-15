import subprocess
import sys

watch = "--watch" in sys.argv
if watch:
    # Start tailwind in watch mode
    css = subprocess.Popen(["./tailwindcss", "-i", "styles/input.css", "-o", "styles/output.css", "--watch"])
    try:
        subprocess.run(["uv", "run", "main.py"])
    finally:
        css.terminate()
else:
    # Build CSS once and run
    subprocess.run(["./tailwindcss", "-i", "styles/input.css", "-o", "styles/output.css"])
    subprocess.run(["uv", "run", "main.py"]) 