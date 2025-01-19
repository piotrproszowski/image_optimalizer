from PIL import Image, UnidentifiedImageError
import os
import sys

def optimize_image(input_path, output_path, max_width, max_height, quality, convert_to_webp=False):
    """
    Optimize the image by resizing and optionally converting to webp format.

    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the optimized image.
        max_width (int): Maximum width of the optimized image.
        max_height (int): Maximum height of the optimized image.
        quality (int): Quality of the optimized image (1-100).
        convert_to_webp (bool): Flag to convert image to webp format.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with Image.open(input_path) as img:
            # Resize image while maintaining aspect ratio
            img.thumbnail((max_width, max_height))
            
            # Change format to webp if required
            if convert_to_webp:
                output_path = os.path.splitext(output_path)[0] + ".webp"
            
            # Save the optimized image
            img.save(output_path, optimize=True, quality=quality)
    except FileNotFoundError:
        print(f"Error: The file {input_path} was not found.")
    except UnidentifiedImageError:
        print(f"Error: The file {input_path} is not a valid image.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def is_image_file(filename):
    """
    Check if a file is an image based on its extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file is an image, False otherwise.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    return os.path.splitext(filename)[1].lower() in image_extensions

def main():
    while True:
        directory = input("Podaj ścieżkę do folderu ze zdjęciami: ")
        if not os.path.isdir(directory):
            print(f"Błąd: Folder {directory} nie istnieje. Spróbuj ponownie.")
            continue
        break

    max_width = int(input("Podaj maksymalną szerokość (domyślnie 800): ") or 800)
    max_height = int(input("Podaj maksymalną wysokość (domyślnie 800): ") or 800)
    quality = int(input("Podaj jakość (1-100, domyślnie 85): ") or 85)
    convert_to_webp = input("Konwertować do webp (tak/nie, domyślnie tak): ").lower() == 'tak' if input("Konwertować do webp (tak/nie, domyślnie tak): ") else True

    for filename in os.listdir(directory):
        if is_image_file(filename):
            input_image_path = os.path.join(directory, filename)
            output_image_path = os.path.join(directory, f"optimized_{filename}")
            optimize_image(input_image_path, output_image_path, max_width, max_height, quality, convert_to_webp)

if __name__ == "__main__":
    main()
