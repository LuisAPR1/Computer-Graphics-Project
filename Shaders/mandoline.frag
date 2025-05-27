#version 120
#ifdef GL_ES
precision mediump float;
#endif

varying vec3 lightVec;
varying vec3 eyeVec;
varying vec2 texCoord;
varying vec3 tangent;

float circle(vec2 uv, vec2 center, float radius) {
    // retorna valor suavizado para buraco circular
    return smoothstep(radius, radius - 0.01, distance(uv, center));
}

float stripe(float x, float spacing, float width) {
    // retorna valor suavizado para risca vertical centrada num padrão espaçado
    float modPos = mod(x, spacing);
    return smoothstep(width, 0.0, abs(modPos - spacing/2.0));
}

void main(void)
{
    // Darker wood color
    vec3 woodLight = vec3(0.4, 0.25, 0.1);
    vec3 holeColor = vec3(0.02);
    vec3 stringColor = vec3(0.3);

    // Buraco deslocado para esquerda e cima e metade do tamanho
    float hole = circle(texCoord, vec2(0.4, 0.6), 0.075);

    float numStrings = 6.0;
    float spacing = 1.0 / numStrings;
    float width = 0.01;
    float strings = 0.0;

    float x = texCoord.x;

    for (float i = 0.0; i < 6.0; i += 1.0) {
        strings += stripe(x, spacing, width);
        x -= spacing;
    }

    strings = clamp(strings, 0.0, 1.0);

    vec3 color = woodLight;
    color = mix(color, holeColor, hole);
    color = mix(color, stringColor, strings);

    vec3 N = normalize(lightVec);
    float diff = max(dot(N, vec3(0.0, 0.0, 1.0)), 0.0);
    
    // Reduce overall brightness
    diff = diff * 0.7;

    gl_FragColor = vec4(color * diff, 1.0);
}
