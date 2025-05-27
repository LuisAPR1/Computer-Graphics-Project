#ifdef GL_ES
precision mediump float;
#endif

varying vec3 lightVec;
varying vec2 texCoord;

void main(void)
{
    // Cores
    vec3 yellow = vec3(1.0, 0.84, 0.0);
    vec3 blackColor = vec3(0.0, 0.0, 0.0);

    // Largura da risca
    float stripeWidth = 0.2;

    // Determinar cor base (risca no centro)
    float dist = abs(texCoord.x - 0.5);
    vec3 baseColor = dist < stripeWidth * 0.5 ? blackColor : yellow;

    // Iluminação simples (difusa)
    vec3 N = normalize(lightVec);
    float diffuse = max(dot(N, vec3(0.0, 0.0, 1.0)), 0.0);

    vec3 finalColor = baseColor * diffuse;

    gl_FragColor = vec4(finalColor, 1.0);
}
