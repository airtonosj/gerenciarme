from gui import App
from setup_db import setup

if __name__ == "__main__":
    setup()  # Configura o banco de dados (cria DB e tabelas)
    app = App()
    app.mainloop()