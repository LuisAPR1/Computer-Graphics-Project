#version 120
#ifdef GL_ES
precision mediump float;
#endif

varying vec3 lightVec;
varying vec2 texCoord;

float rings(vec2 uv) {
    // Create rings by using the distance from the center
    float dist = length(uv - vec2(0.5));
    // Create multiple rings by multiplying the distance
    float rings = sin(dist * 20.0) * 0.5 + 0.5;
    return rings;
}

void main(void)
{
    vec3 darkBrown = vec3(0.4, 0.2, 0.05);
    vec3 lightBrown = vec3(0.7, 0.4, 0.1);

    // Create ring pattern
    float ringPattern = rings(texCoord);
    
    // Mix between dark and light brown based on the ring pattern
    vec3 color = mix(darkBrown, lightBrown, ringPattern);

    // Add some noise to make it look more natural
    float noise = fract(sin(dot(texCoord, vec2(12.9898, 78.233))) * 43758.5453);
    color = mix(color, color * 0.9, noise * 0.2);

    vec3 N = normalize(lightVec);
    float diff = max(dot(N, vec3(0.0, 0.0, 1.0)), 0.0);

    vec3 finalColor = color * diff;

    gl_FragColor = vec4(finalColor, 1.0);
}
