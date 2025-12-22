# Image Optimizer

Narzędzie do wsadowej optymalizacji obrazów z GUI.

## Szybki Start

### Gotowe Aplikacje (bez instalacji)

1. Pobierz z folderu `dist/`:
   - **macOS ARM:** `image_optimizer.app` (M1/M2/M3)
   - **Windows x64:** `image_optimizer.exe`
2. Kliknij dwukrotnie i uruchom
3. Wybierz folder LUB pojedynczy plik obrazu

**macOS:** Przy pierwszym uruchomieniu: prawy klik → Otwórz → Otwórz  
**Windows:** Windows Defender może ostrzegać - kliknij "Więcej informacji" → "Uruchom mimo to"

---

## Budowanie

### macOS
```bash
./build_macos.sh
```
Wynik: `dist/image_optimizer.app`

### Windows
```cmd
build_windows.bat
```
Wynik: `dist\image_optimizer.exe`

---

## Funkcje

- **Pojedyncze pliki** lub **wsadowe przetwarzanie** folderów
- **Presety rozdzielczości:** HD, Full HD, 2K, 4K, Custom, Original
- **Kadrowanie** do wybranych wymiarów
- **Kompresja** z regulowaną jakością (1-100)
- **Konwersja formatów:** JPEG, PNG, WebP
- **Drag & Drop** dla plików i folderów
- **Obsługa formatów:**
  - JPG/JPEG
  - PNG (z przezroczystością)
  - WebP (z przezroczystością)
  - HEIC/HEIF (zdjęcia z iPhone)
  - GIF, BMP, TIFF
- **Rekursywne przetwarzanie** podfolderów
- **Automatyczny motyw** jasny/ciemny

---

## Wymagania

**Gotowe aplikacje:** macOS 11+ lub Windows 10+

**Budowanie:**
- Python 3.8+
- Zależności: `pip install -r requirements.txt`

---

## Autor

Piotr Proszowski