from pathlib import Path
import matplotlib.pyplot as plt
from PyQt6.QtGui import QIcon




def get_icon():

    base_path = Path(__file__).resolve().parent.parent

    icon_path = base_path / "random_bloke_new.png"
    if not icon_path.exists():
        icon_path = base_path / "Paint.png"

    img = plt.imread(icon_path)
    plt.imshow(img)
    plt.show()
    return QIcon(icon_path.resolve().as_posix())
