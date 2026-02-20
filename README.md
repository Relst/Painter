# Custom Paint Application

A custom desktop paint application built using **PyQt6** and **NumPy**.  
This project implements a fully custom UI system, a layered canvas architecture, and a proprietary session file format for saving and restoring application state across runs.

The goal of this project is to design and build a modular painting engine from scratch, including rendering, data modeling, tool architecture, and session persistence.

---

## Overview

The application consists of:

- A custom-designed UI built entirely with PyQt6
- A NumPy-backed raster canvas system
- A multi-layer rendering architecture
- A custom session file format for cross-application session persistence
- Prototype painting tools

The architecture aims to maintain a clean separation between UI and backend logic.

---

## Architecture

### UI Layer

Responsible for:
- Layout and window structure
- Tool selection
- Tool parameter controls
- Layer management UI
- Navigator window
- Visual feedback and interaction

### Backend Layer

Responsible for:
- Canvas data model
- Layer storage and compositing
- Tool execution logic
- Session serialization and deserialization
- State tracking

---

## Canvas & Data Model

The rendering system is built around NumPy-backed pixel buffers. Every instance of a file open creates a canvas, and each canvas has 1 or more layers. A layer maintains its own raster buffer and metadata.



Pixel data is stored using structured NumPy arrays to allow efficient compositing and manipulation.

---

## Custom File Format

The application defines its own session file format designed to:

- Preserve complete layer structure
- Maintain tool configuration
- Store canvas state efficiently
- Allow future extensibility
- Enable cross-application session restoration

The format is structured to separate metadata from raw raster data, allowing flexibility in versioning and future upgrades.

---

## Implemented Features

### UI

- Prototype main UI system
- Sidebar tool system
- Tool options bar
- Layers panel
- Floating navigator window
- Custom context window

### Tools (Prototype)

- Paint Brush
- Spline Paint Brush
- Eraser
- Fill Bucket

---

## TODO

- Connect backend to UI/UX, 
- Refactor backend Canvas and Layers into a simpler data model
- Remove tracking within Layers and raise it to a higher-level canvas/application controller
- Create generic Tool abstractions to simplify development of future tool implementations
- Add paralleization for drawing modes.
- Fix issues regarding mappings of tools.

---

## Dependencies

- Python 3.12
- PyQt6
- NumPy
