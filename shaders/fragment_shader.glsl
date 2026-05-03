#version 330 core

in vec3 Normal;
out vec4 FragColor;

uniform vec3 u_color; // Cor enviada pelo set_tile_color[cite: 2]

void main() {
    // Luz direcional vindo do "sol" (simulando o céu do Ceará)
    vec3 lightDir = normalize(vec3(1.0, 1.0, 0.5));
    float diff = dot(normalize(Normal), lightDir);

    // MECÂNICA DE CEL-SHADING: Quantização da luz[cite: 2]
    // Em vez de degradê, criamos "degraus" de iluminação
    float intensity;
    if (diff > 0.8) intensity = 1.0;
    else if (diff > 0.4) intensity = 0.7;
    else intensity = 0.3;

    // Aplica a intensidade à cor definida no board.py
    vec3 result = u_color * intensity;
    FragColor = vec4(result, 1.0);
}