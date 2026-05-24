#version 330 core
out vec4 FragColor;

in vec2 TexCoord;

uniform sampler2D u_texture;

// Novas variaveis que controlam o feedback visual do Python
uniform int u_use_solid_color;
uniform vec4 u_solid_color;

void main() {
    if (u_use_solid_color == 1) {
        // Se ativado, ignora a textura e usa a cor pura enviada pelo Python (Ex: Branco, Verde, Amarelo)
        FragColor = u_solid_color;
    } else {
        // Comportamento original para os modelos 3D e tabuleiro
        FragColor = texture(u_texture, TexCoord);
    }
}