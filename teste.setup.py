import glfw
from OpenGL.GL import *
import numpy as np

# Tenta iniciar o GLFW
if not glfw.init():
    print("Erro ao iniciar o GLFW!")
else:
    print("✅ GLFW instalado e funcionando!")

# Verifica a versão do NumPy
print(f"✅ NumPy versão: {np.__version__}")

# Verifica se o OpenGL está acessível
print("✅ PyOpenGL pronto para uso!")

glfw.terminate()