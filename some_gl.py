import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
import math
from PIL import Image
import requests
from io import BytesIO
import os

# --- Pygame and OpenGL Initialization ---
pygame.init()
width, height = 800, 600
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Combined Bump Mapping and Environment Mapping Cube")

glViewport(0, 0, width, height)
glMatrixMode(GL_PROJECTION)
gluPerspective(45, (width / height), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glEnable(GL_DEPTH_TEST)
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glEnable(GL_COLOR_MATERIAL)
glShadeModel(GL_SMOOTH)

# --- Texture Loading Functions ---

def load_texture(path):
    """
    Downloads and loads a texture from a URL or a local file.
    Returns a fallback texture if the load fails.
    The function checks if the path starts with "http:" to determine if it's a URL.
    """
    try:
        if path.startswith("http:"):
            print(f"Loading texture from URL: {path}")
            response = requests.get(path)
            img = Image.open(BytesIO(response.content))
        else:
            print(f"Loading texture from local file: {path}")
            img = Image.open(path)
            
        img = img.convert("RGBA")
        img_data = np.array(img, dtype=np.uint8).tobytes()
        width, height = img.size
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, 
                     GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        
        return texture
    except Exception as e:
        print(f"Failed to load texture from {path}: {e}, using fallback.")
        # Create a simple colored fallback
        fallback = np.zeros((256, 256, 4), dtype=np.uint8)
        fallback[:, :, 0] = 255 # Red
        fallback[:, :, 3] = 255 # Alpha
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_RGBA, GL_UNSIGNED_BYTE, fallback)
        return texture


def load_env_texture(path):
    """
    Loads an environment map (matcap) texture from a URL.
    This function is kept separate as matcaps are typically square and not loaded locally.
    Returns a fallback texture if the download fails.
    """
    try:
        if path.startswith("https:"):
            print(f"Loading texture from URL: {path}")
            response = requests.get(path)
            img = Image.open(BytesIO(response.content))
        else:
            print(f"Loading texture from local file: {path}")
            img = Image.open(path)
        #response = requests.get(url)
        #img = Image.open(BytesIO(response.content))
        img = img.convert("RGB").resize((512, 512))
        img_data = np.array(img, dtype=np.uint8)
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 512, 512, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        return texture
    except Exception as e:
        print(f"Failed to load environment texture from URL: {e}, using fallback.")
        fallback = np.zeros((512, 512, 3), dtype=np.uint8)
        for y in range(512):
            for x in range(512):
                fallback[y, x] = [x // 2, y // 2, 128]
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 512, 512, 0, GL_RGB, GL_UNSIGNED_BYTE, fallback)
        return texture


# --- Cube Data ---
# A simpler way to define vertices, normals, and texture coordinates
# to make it easier to add tangents and bitangents.
cube_faces = {
    'front': (
        np.array([[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], dtype=np.float32),
        np.array([0, 0, 1], dtype=np.float32),
        np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    ),
    'back': (
        np.array([[-1, -1, -1], [-1, 1, -1], [1, 1, -1], [1, -1, -1]], dtype=np.float32),
        np.array([0, 0, -1], dtype=np.float32),
        np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.float32)
    ),
    'top': (
        np.array([[-1, 1, -1], [-1, 1, 1], [1, 1, 1], [1, 1, -1]], dtype=np.float32),
        np.array([0, 1, 0], dtype=np.float32),
        np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.float32)
    ),
    'bottom': (
        np.array([[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]], dtype=np.float32),
        np.array([0, -1, 0], dtype=np.float32),
        np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    ),
    'right': (
        np.array([[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]], dtype=np.float32),
        np.array([1, 0, 0], dtype=np.float32),
        np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.float32)
    ),
    'left': (
        np.array([[-1, -1, -1], [-1, -1, 1], [-1, 1, 1], [-1, 1, -1]], dtype=np.float32),
        np.array([-1, 0, 0], dtype=np.float32),
        np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    )
}

# --- Load Textures ---
env_texture = load_env_texture(
#     "https://images.unsplash.com/photo-1626908013943-df94de54984c?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=512&h=512&q=80"
 "texture_uns.jpg"
)

# Textures and normal maps for individual faces (using placeholder URLs)
face_color_textures = [
    load_texture("texture_uns.png"),     # Top face
    load_texture("texture_uns.png"),  # Bottom face
    load_texture("1_stop_starting.png"),   # Front face
    load_texture("2.cross.png"),   # Right face
    load_texture("2.png"),     # Left face
    load_texture("3_all.png")    # Back face
]



# --- Rendering Functions ---

def set_metallic_material():
    """Set up material properties for a metallic surface."""
    glMaterialfv(GL_FRONT, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.3, 0.3, 0.3, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.9, 0.9, 0.9, 1.0))
    glMaterialf(GL_FRONT, GL_SHININESS, 128.0)
    glMaterialfv(GL_FRONT, GL_EMISSION, (0.1, 0.1, 0.1, 1.0))


def draw_cube_textured_faces():
    """Draw the cube with a different color texture on each face."""
    glEnable(GL_TEXTURE_2D)
    
    # Set up a non-metallic material for this mode
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.2, 0.2, 0.2, 1.0))
    glMaterialf(GL_FRONT, GL_SHININESS, 30.0)
    glMaterialfv(GL_FRONT, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

    face_keys = list(cube_faces.keys())
    for i in range(6):
        glBindTexture(GL_TEXTURE_2D, face_color_textures[i])
        vertices, normal, tex_coords = cube_faces[face_keys[i]]
        glBegin(GL_QUADS)
        for j in range(4):
            glTexCoord2fv(tex_coords[j])
            glNormal3fv(normal)
            glVertex3fv(vertices[j])
        glEnd()
    glDisable(GL_TEXTURE_2D)


def draw_cube_shiny_and_textured():
    """
    Draw the cube with both a base color texture and an environment map for a shiny look.
    This uses multi-texturing to blend the two effects correctly.
    """
    set_metallic_material()
    
    # Configure texture unit 0 for the base color texture
    glActiveTexture(GL_TEXTURE0)
    glEnable(GL_TEXTURE_2D)
    # The primary texture is modulated with the lighting color
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    
    # Configure texture unit 1 for the environment map
    glActiveTexture(GL_TEXTURE1)
    glEnable(GL_TEXTURE_2D)
    # Set up texture coordinate generation for sphere mapping
    glEnable(GL_TEXTURE_GEN_S)
    glEnable(GL_TEXTURE_GEN_T)
    glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
    glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
    glBindTexture(GL_TEXTURE_2D, env_texture)

    # Set up the texture environment to combine texture units
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
    glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_MODULATE)
    glTexEnvi(GL_TEXTURE_ENV, GL_SOURCE0_RGB, GL_PREVIOUS)
    glTexEnvi(GL_TEXTURE_ENV, GL_SOURCE1_RGB, GL_TEXTURE)
    
    face_keys = list(cube_faces.keys())
    for i in range(6):
        # Bind the color texture for the current face to texture unit 0
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, face_color_textures[i])
        
        vertices, normal, tex_coords = cube_faces[face_keys[i]]
        glBegin(GL_QUADS)
        for j in range(4):
            glMultiTexCoord2fv(GL_TEXTURE0, tex_coords[j])
            glNormal3fv(normal)
            glVertex3fv(vertices[j])
        glEnd()
    
    # Clean up state to avoid conflicts with other rendering modes
    glDisable(GL_TEXTURE_GEN_S)
    glDisable(GL_TEXTURE_GEN_T)
    
    glActiveTexture(GL_TEXTURE1)
    glDisable(GL_TEXTURE_2D)
    
    glActiveTexture(GL_TEXTURE0)
    glDisable(GL_TEXTURE_2D)


# --- Main Loop ---
clock = pygame.time.Clock()
rotation_x, rotation_y, rotation_z = 0, 0, 0
rotation_speed = 0.5
distance = -5.0
use_combined_effect = False  # Start with textured faces

# Set up lighting
glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Toggle between rendering modes
            elif event.key == pygame.K_t:
                use_combined_effect = not use_combined_effect
                print("Rendering mode toggled:", "Combined Shiny/Textured" if use_combined_effect else "Textured Faces")
            # Adjust rotation speed
            elif event.key == pygame.K_UP:
                rotation_speed += 0.5
            elif event.key == pygame.K_DOWN:
                rotation_speed -= 0.5
            # Toggle between fast and slow rotation
            elif event.key == pygame.K_SPACE:
                if rotation_speed == 0:
                    rotation_speed = 0.5 
                else:
                    rotation_speed = 0
            elif event.key == pygame.K_r:
                rotation_speed = 15.0 if rotation_speed <= 10.0 else 0.5
            # Adjust camera distance
            elif event.key == pygame.K_w:
                distance += 0.5
            elif event.key == pygame.K_s:
                distance -= 0.5
            
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Position the camera
    glTranslatef(0, 0, distance)
    
    # Apply a fixed initial rotation for a better view
    glRotatef(100, 1, 0, 0)

    # Rotate the cube
    rotation_x += rotation_speed * 0.7
    rotation_y += rotation_speed
    rotation_z += rotation_speed * 0.3
    glRotatef(rotation_z, 0, 0, 1)

    if use_combined_effect:
        draw_cube_shiny_and_textured()
    else:
        draw_cube_textured_faces()
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

