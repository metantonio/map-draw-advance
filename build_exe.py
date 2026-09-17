import os
import sys
import subprocess

def build():
    print("=======================================================")
    print("INICIANDO COMPILACION DE MAP DRAW ADVANCE WEB APP (.EXE)")
    print("=======================================================")

    python_exe = sys.executable
    venv_python = os.path.abspath(os.path.join(".venv", "Scripts", "python.exe"))
    if os.path.exists(venv_python):
        try:
            import PyInstaller
        except ImportError:
            python_exe = venv_python

    print(f"Usando interprete Python: {python_exe}")

    datas = []
    if os.path.exists("templates"):
        datas.append(("templates", "templates"))
    if os.path.exists("static"):
        datas.append(("static", "static"))
    if os.path.exists("escala-color.jpg"):
        datas.append(("escala-color.jpg", "."))
    if os.path.exists("portada.jpg"):
        datas.append(("portada.jpg", "."))
    if os.path.exists("icons"):
        datas.append(("icons", "icons"))
    if os.path.exists("projects"):
        datas.append(("projects", "projects"))
    if os.path.exists("data.xls"):
        datas.append(("data.xls", "."))
    if os.path.exists("data.xlsx"):
        datas.append(("data.xlsx", "."))

    cmd = [
        python_exe, "-m", "PyInstaller",
        "--name=MapDrawAdvance",
        "--onefile",
        "--console",
        "--clean",
    ]

    hidden_imports = [
        "flask",
        "werkzeug",
        "jinja2",
        "folium",
        "folium.plugins",
        "branca",
        "branca.element",
        "pandas",
        "openpyxl",
        "xlrd",
        "pyproj",
        "mpu",
        "matplotlib",
        "numpy",
        "geocoder",
        "functions",
        "eqa2utm",
        "distAndAngle",
        "scaletemplate",
        "main",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.extend(["--collect-data", "folium"])
    cmd.extend(["--collect-data", "branca"])

    for src, dest in datas:
        cmd.extend(["--add-data", f"{src};{dest}"])

    cmd.append("server.py")

    print("\nEjecutando PyInstaller para server.py:\n", " ".join(cmd))

    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.abspath(os.path.join("dist", "MapDrawAdvance.exe"))
        print("\n=======================================================")
        print("COMPILACION EXITOSA CON INTERFAZ WEB NAVEGADOR")
        print(f"Ejecutable disponible en: {exe_path}")
        print("=======================================================")
    else:
        print("\nError durante la compilacion de server.py con PyInstaller.")

if __name__ == "__main__":
    build()
