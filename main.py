import sys

def main():
    if "--gui" in sys.argv:
        from quicksave.gui.tray import main as gui_main
        gui_main()
    else:
        from quicksave.core.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()