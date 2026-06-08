#version 330 core

in vec2 TexCoord;
in vec3 FragPos;
in vec3 Normal; // CORRIGIDO: Era vec, agora é vec3

out vec4 FragColor;

uniform sampler2D u_texture;
uniform int u_use_solid_color;
uniform vec4 u_solid_color;

//variaveis de iluminação
uniform int u_use_lighting;
uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 lightColor;
uniform float ambientStrength;

void main(){
    
    vec4 baseColor;

    // CORRIGIDO: Era u_solid_color, agora é u_use_solid_color
    if(u_use_solid_color == 1){ 
        baseColor = u_solid_color;
    }else{
        baseColor = texture(u_texture, TexCoord);
    }

    // Interface 2d, cursor ou sombra, não usa cálculo de luz
    if(u_use_lighting == 0){
        FragColor = baseColor;
        return;
    }

    // 1° ambiente
    vec3 ambient = ambientStrength * lightColor;

    // 2° Difusa
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos); // CORRIGIDO: Era vec, agora é vec3
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;

    // 3° Especular (Brilho do Material)
    float specularStrength = 0.3;
    float shininess = 16.0;
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    
    // CORRIGIDO: Faltava o * entre spec e lightColor
    vec3 specular = specularStrength * spec * lightColor; 

    vec3 result = (ambient + diffuse + specular) * baseColor.rgb;
    FragColor = vec4(result, baseColor.a);
}