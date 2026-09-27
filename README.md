# Labelsoft

A lightweight, fast, and feature-rich Python annotation tool built with PyQt5. This tool is specifically designed to effortlessly create datasets for **Instance Segmentation (Polygons)** and **Object Detection (Bounding Boxes)**. It saves annotations in an intuitive and widely compatible JSON format, making it incredibly easy to integrate into modern computer vision pipelines.

## ✨ Key Features

- **Direct Folder Access (No strict hierarchies):** Just open any folder containing your images. The application reads images directly and saves the `.json` files right next to them—no need for separate `images` or `labels` subdirectories!
- **Dynamic Class Detection:** No more maintaining messy `classes.txt` files. The tool dynamically scans your existing `.json` files and detects your project's classes instantly. 
- **Smart Class Memory:** The annotator remembers the last class you used, greatly accelerating the speed of repetitive, sequential labeling.
- **Dual Drawing Modes:** 
  - **Polygon (W):** Click around objects to create precise segmentation masks.
  - **Bounding Box (B):** Use an intuitive 2-click system (Click once to set the first corner, move your mouse, and click again to complete the box).
- **Advanced Edit Mode (E):**
  - Click on a shape's center to freely drag and move the entire annotation.
  - Drag the corner handles of a bounding box to resize it.
  - Drag the vertices of a polygon to reshape it.
  - Right-click any shape to quickly change its class label.
  - Press `Delete` to remove the selected annotation.
- **Real-World Dimension Calculator:** 
  - Open the **⚙️ Kamera Ayarları (Camera Settings)** from the toolbar to input your camera's Height, FOV, and Resolution. 
  - The status bar at the bottom will **live-calculate** the real-world dimensions (in cm) and pixel size (in px) of your shape while you are drawing or selecting it!
- **Crosshair Guides:** Full-screen vertical and horizontal crosshairs that follow your mouse cursor to help with precise point alignment.
- **Auto-Fit & Easy Navigation:** Every new image automatically scales to fit your screen perfectly. Easily pan around large images using convenient scroll shortcuts. Navigate seamlessly with `A` (Prev) and `D` (Next) keys.
- **Undo Support:** Press `Ctrl+Z` to undo the last drawn point while creating a polygon.
- **Safe Deletion:** Click the Trash icon in the toolbar to safely delete an image **and** its corresponding `.json` label file from your disk. Doing so will instantly re-scan your dataset and automatically remove any classes that are no longer in use, keeping your workspace perfectly clean.

## 🚀 Prerequisites

Make sure you have Python 3 installed. The only requirement is `PyQt5`.

```bash
pip install PyQt5
```

## 🛠️ Usage

1. **Start the Application:**
   ```bash
   python3 main.py
   ```

2. **Select Dataset Directory:**
   Click the **📂 Klasör Seç (Select Folder)** button.
   Choose the folder where your images are located. The application will scan for images and existing annotations immediately.

3. **Annotate Your Images:**
   - Use the toolbar or shortcuts (`W`, `B`, `E`) to switch between drawing and editing modes. The application defaults to the Bounding Box mode.
   - For **Polygons**, click around the object. Clicking near the first point (turns green) completes the polygon.
   - For **Bounding Boxes**, left-click once to start, move your mouse, and left-click again to complete.
   - Upon completing a shape, a smart dialog will appear with your last-used class pre-selected, allowing you to breeze through repetitive labeling.

## ⌨️ Shortcuts & Mouse Controls

| Input | Action |
| --- | --- |
| `W` | Switch to Polygon Draw Mode |
| `B` | Switch to Bounding Box Draw Mode |
| `E` | Switch to Edit Mode |
| `A` | Previous Image |
| `D` | Next Image |
| `Ctrl + Z` | Undo the last point (While drawing a polygon) |
| `Delete` | Delete the selected annotation (In Edit Mode) |
| `Right Click` | Change the class of the clicked annotation (In Edit Mode) |
| `Esc` | Cancel current drawing |
| **Middle Scroll Wheel** | Zoom In / Out |
| **Ctrl + Scroll** | Vertical Pan (Up / Down) |
| **Shift + Scroll** | Horizontal Pan (Left / Right) |
| **Middle Click & Drag** | Free Pan / Move around the image |

## 📁 Output Structure Example

When you annotate images, your folder will naturally look like this:

```text
my_dataset/
├── img1.jpg
├── img1.json         
├── img2.jpg
└── img2.json
```
