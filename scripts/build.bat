python -m pip install -r requirements.txt
python -m PyInstaller --onefile --noconsole --clean --add-data "layout;layout" --add-data "api;api" --icon=layout\resources\logo.ico --collect-all "pyreadline3" --collect-all "sqlite3" --collect-all "Cryptodome" --collect-all "PIL" --name=3DS-RPC app.py
