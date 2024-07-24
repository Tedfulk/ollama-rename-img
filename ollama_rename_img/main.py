import base64
import json
import logging
import os
from pathlib import Path
from typing import List

import ollama
import typer
from PIL import Image
from pydantic import BaseModel, Field
from tqdm import tqdm


class ImageClassification(BaseModel):
    keywords: List[str] = Field(..., description="Keywords of the image.")

    def keywords_to_string_with_delimiter(self, delimiter: str = "_") -> str:
        """
        Convert keywords to a string with the specified delimiter.

        Args:
            delimiter (str): The delimiter to use between keywords.
                            Must be underscore '_', dash '-', or space ' '.
                            Defaults to underscore '_'.

        Returns:
            str: A string of keywords joined by the specified delimiter.

        Raises:
            ValueError: If an invalid delimiter is provided.
        """
        if delimiter not in ["_", "-", " "]:
            raise ValueError("Delimiter must be underscore '_', dash '-', or space ' '")
        cleaned_keywords = [
            keyword.replace(" ", delimiter)
            for keyword in self.keywords
            if not any(char.isdigit() for char in keyword)
        ]
        limited_keywords = delimiter.join(cleaned_keywords[:5])
        return limited_keywords


def convert_webp_to_jpeg(file_path):
    """
    Check if the given file is a WebP image and convert it to a JPG file.

    Parameters:
    - file_path: str - The path to the file to be checked and converted.

    Returns:
    - str - The path to the converted JPG file, or an error message.
    """
    # Check if the file extension is .webp
    if not file_path.lower().endswith(".webp"):
        return "The file is not a WebP image based on its extension."

    try:
        # Attempt to open the image to confirm it's a valid WebP file
        with Image.open(file_path) as img:
            # Define the new file name with a .jpeg extension
            new_file_path = os.path.splitext(file_path)[0] + ".jpeg"

            # Convert and save the image as a JPG file
            img.convert("RGB").save(new_file_path, "JPEG")

            return new_file_path
    except IOError:
        return "Failed to open or process the file. Please ensure it is a valid WebP image."


app = typer.Typer()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def configure_logging(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    if verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)


def convert_files_to_jpeg(directory_path: Path) -> List[Path]:
    converted_list = []
    for file in directory_path.iterdir():
        if file.is_file() and file.suffix.lower() == ".webp":
            jpeg_file_path = convert_webp_to_jpeg(str(file))
            converted_list.append(Path(jpeg_file_path))
    return converted_list


def generate_keywords(image_path: Path) -> dict:
    with image_path.open("rb") as img_file:
        base64_string = base64.b64encode(img_file.read()).decode("utf-8")

    response = ollama.chat(
        model="llava-phi3",
        messages=[
            {
                "role": "user",
                "content": "Describe the image as 4 keywords. Output in JSON format. Use the following schema: { keywords: List[str] }.",
                "images": [base64_string],
            },
        ],
    )
    return response


def process_image(
    directory_path: Path,
    converted_files: List[Path],
    webp_files: List[Path],
    delimiter: str,
) -> None:
    for file in tqdm(converted_files, desc="Processing images", unit="image"):
        if file.name == ".DS_Store":
            continue

        try:
            response = generate_keywords(file)
            resp = (
                response["message"]["content"]
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            keywords = json.loads(resp)
            image_classification = ImageClassification(**keywords)
            new_file_name = image_classification.keywords_to_string_with_delimiter(
                delimiter
            )
            new_file_path = directory_path / f"{new_file_name}{file.suffix}"

            file.rename(new_file_path)
            logger.info(f"Renamed {file.name} to {new_file_path.name}")

            # Find the corresponding WebP file
            webp_file = next((w for w in webp_files if w.stem == file.stem), None)
            if webp_file:
                webp_file.unlink()
                webp_files.remove(webp_file)
                logger.info(f"Removed original WebP file: {webp_file}")
            else:
                logger.warning(f"No corresponding WebP file found for {file.name}")

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response for {file}")
        except Exception as e:
            logger.error(f"Error processing {file}: {str(e)}")

    # Check if there are any remaining WebP files
    for remaining_webp in webp_files:
        logger.warning(f"Unprocessed WebP file: {remaining_webp}")


@app.command(help="Rename image files in a directory based on their content.")
def process_dir(
    directory_path: str,
    delimiter: str = typer.Option(
        "_",
        "--delimiter",
        "-d",
        help="Delimiter for keywords in filename. Choose '_', '-', or ' ' (space). Default is '_'.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """
    Rename images in a directory based on their content using AI-generated keywords.

    Args:
        directory_path (str): The path to the directory containing the images.
        delimiter (str): The delimiter to use between keywords in the filename. Default is '_'.
    """
    if delimiter not in ["_", "-", " "]:
        raise typer.BadParameter("Delimiter must be '_', '-', or ' ' (space).")

    dir_path = Path(directory_path)
    configure_logging(verbose)

    webp_files = list(dir_path.glob("*.webp"))
    logger.info(f"Found {len(webp_files)} WebP files")

    converted_jpg_files = convert_files_to_jpeg(dir_path)
    logger.info(f"Converted {len(converted_jpg_files)} files to JPEG")

    if not converted_jpg_files:
        logger.warning("No JPEG files to process. Exiting.")
        return

    process_image(dir_path, converted_jpg_files, webp_files, delimiter)
