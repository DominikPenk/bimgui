//--vertex
uniform mat4 u_ViewProjectionMatrix;

in vec3 position;
in float arcLength;

out float v_ArcLength;

void main()
{
    v_ArcLength = arcLength;
    gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0f);
}

//--fragment
uniform float u_Scale;

in float v_ArcLength;

void main()
{
    if (step(sin(v_ArcLength * u_Scale), 0.5) == 1) discard;
    gl_FragColor = vec4(1.0, 0.0, 1.0, 1.0);
}