#version 330 core
out vec4 FragColor;

// Recebe do Vertex Shader para manter o contrato correto, 
// mas não vamos usar para amostrar nenhuma imagem.
in vec2 TexCoord; 

// Recebe a cor sólida (R, G, B) vinda do código do seu Tabuleiro
uniform vec3 u_color; 

void main() {
    // Pinta o quadrado do tabuleiro com a cor pura
    FragColor = vec4(u_color, 1.0);
}