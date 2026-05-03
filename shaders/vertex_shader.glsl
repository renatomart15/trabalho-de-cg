#version 330 core

layout (location = 0) in vec3 aPos;   // Posição do vértice (do VBO)
layout (location = 1) in vec3 aNormal; // Direção da face (para iluminação)

uniform mat4 model;      // Matriz que posiciona o tile no grid
uniform mat4 view;       // Matriz da câmera
uniform mat4 projection; // Matriz de perspectiva/isométrica

out vec3 Normal; // Passa a normal para o Fragment Shader

void main() {
    // Calcula a posição final do vértice no espaço 3D
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    Normal = mat3(transpose(inverse(model))) * aNormal; 
}