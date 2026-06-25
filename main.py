from gui import App
from setup_db import setup

if __name__ == "__main__":
    if not setup():
        raise SystemExit(1)
    app = App()
    app.mainloop()
