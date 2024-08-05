import matplotlib.pyplot as plt

# Morandi color list in RGB
COLOR_LIST = [
    (194, 166, 159),  # Pale Taupe
    (171, 205, 239),  # Light Blue
    (194, 178, 128),  # Khaki
    (242, 215, 213),  # Misty Rose
    (204, 204, 255),  # Lavender
    (200, 202, 167),  # Pale Goldenrod
    (180, 144, 125),  # Tan
    (150, 143, 132),  # Dark Gray
    (206, 179, 139),  # Burly Wood
    (160, 159, 153),  # Light Slate Gray
    (158, 175, 163),  # Dark Sea Green
    (175, 167, 191),  # Thistle
    (224, 224, 224),  # Gainsboro
    (192, 192, 192),  # Silver
    (230, 159, 125),  # Peach
    (255, 182, 193),  # Light Pink
    (139, 121, 94),   # Umber
    (169, 196, 176),  # Dark Moss Green
    (144, 175, 197),  # Cadet Blue
    (188, 170, 164)   # Rosy Brown
]
# Plotting the colors
plt.figure(figsize=(10, 2))
plt.imshow([COLOR_LIST], aspect='auto')
plt.axis('off')
plt.title('Morandi Color Palette')
plt.show()

