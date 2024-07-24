# Image Renaming CLI App

## Introduction

Have you ever downloaded a bunch of images and their file names make no sense, making it difficult to find what you're looking for? What if I told you that you could use a local AI solution to help rename images based on their descriptions? This Python CLI app does just that!

This CLI app converts WebP images to JPEG, generates descriptive keywords using AI, and renames the images based on those keywords.

## Getting Started

### Prerequisites

- Python (make sure it's installed on your system)
- [Ollama](https://ollama.com/) (make sure it's installed on your system)
- [Poetry](https://python-poetry.org/docs/) (for managing Python dependencies)
- [pipx](https://pipx.pypa.io/stable/installation/) (for installing Python CLI applications globally)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Tedfulk/ollama-rename-img.git
```

2. Navigate to the project directory:

```bash
cd ollama-rename-img
```

3. Install Poetry if you haven't already:

```bash
pipx install poetry
```

4. Activate the shell:

```bash
poetry shell
```

5. Install the project dependencies using Poetry:

```bash
poetry install
```

6. Verify the installation:

```bash
which rename
```

### Required Packages

- Ollama: Open-source technology that allows us to pull large language models from the community. In this project, we use `llava-phi3`, a multimodal model capable of processing images and generating text descriptions.

## CLI Usage

### Command Line Arguments

- `directory_path` (str): The path to the directory containing the images.
- `delimiter` (str): The delimiter to use between keywords in the filename. Default is `_`. Options are `_`, `-`, or ` ` (space).
- `verbose` (bool): Enable verbose output. Default is `False`.

### Basic Usage

Run the following command to process and rename images in a directory:

```bash
rename /path/to/directory -d "_" -v
```

- `/path/to/directory`: Replace with the path to your image directory.
- `-d "_"`: Use underscore as the delimiter between keywords.
- `-v`: Enable verbose output.
