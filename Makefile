VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
SCRIPT = Trabalho_Vigas_Grupo_Pagerunk.py

all: run

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install customtkinter matplotlib Pillow

run:
	@if [ ! -d "$(VENV)" ]; then $(MAKE) setup; fi
	$(PYTHON) $(SCRIPT)

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +

reinstall: clean setup
