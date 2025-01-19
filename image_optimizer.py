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
    print("Welcome to the Image Optimizer!")
    print("To exit the program, press Ctrl+C at any time.")
    
    while True:
        try:
            while True:
                directory = input("\nEnter the path to the images folder: ")
                if not os.path.isdir(directory):
                    print(f"Error: Folder {directory} does not exist. Please try again.")
                    continue
                break

            max_width = int(input("Enter maximum width (default 800): ") or 800)
            max_height = int(input("Enter maximum height (default 800): ") or 800)
            quality = int(input("Enter quality (1-100, default 85): ") or 85)
            convert_to_webp = input("Convert to webp (yes/no, default yes): ").lower() == 'yes' if input("Convert to webp (yes/no, default yes): ") else True

            image_count = 0
            for filename in os.listdir(directory):
                if is_image_file(filename):
                    image_count += 1
                    input_image_path = os.path.join(directory, filename)
                    output_image_path = os.path.join(directory, f"optimized_{filename}")
                    optimize_image(input_image_path, output_image_path, max_width, max_height, quality, convert_to_webp)
            
            print(f"\nOptimized {image_count} images in folder {directory}")
            print("You can now enter another folder path.")

        except KeyboardInterrupt:
            print("\n\nProgram terminated by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Please try again.")
            continue

if __name__ == "__main__":
    main()
