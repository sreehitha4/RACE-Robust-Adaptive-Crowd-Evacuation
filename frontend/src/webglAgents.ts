import type { Agent } from "./contract.ts";
import type { View } from "./render.ts";

/** WebGL2 instanced point-sprite renderer for agent bodies; Canvas retains map/trails/predictions. */
export class WebGLAgentRenderer {
  private gl: WebGL2RenderingContext;
  private program: WebGLProgram;
  private buffer: WebGLBuffer;
  private resolution: WebGLUniformLocation;
  private position: number;
  private size: number;
  private color: number;

  private canvas: HTMLCanvasElement;

constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const gl = canvas.getContext("webgl2", { alpha: true, antialias: true, powerPreference: "high-performance" });
    if (!gl) throw new Error("WebGL2 is unavailable");
    this.gl = gl;
    const vertex = `#version 300 es
      in vec2 a_position; in float a_size; in vec4 a_color;
      uniform vec2 u_resolution; out vec4 v_color;
      void main(){ vec2 clip=(a_position/u_resolution)*2.0-1.0; gl_Position=vec4(clip.x,-clip.y,0.0,1.0); gl_PointSize=a_size; v_color=a_color; }`;
    const fragment = `#version 300 es
      precision mediump float; in vec4 v_color; out vec4 outColor;
      void main(){ vec2 p=gl_PointCoord-vec2(0.5); if(dot(p,p)>0.25) discard; outColor=v_color; }`;
    this.program = this.link(vertex, fragment);
    const buffer = gl.createBuffer();
    if (!buffer) throw new Error("Unable to allocate WebGL buffer");
    this.buffer = buffer;
    this.resolution = gl.getUniformLocation(this.program, "u_resolution")!;
    this.position = gl.getAttribLocation(this.program, "a_position");
    this.size = gl.getAttribLocation(this.program, "a_size");
    this.color = gl.getAttribLocation(this.program, "a_color");
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  }

  private shader(type: number, source: string): WebGLShader {
    const shader = this.gl.createShader(type);
    if (!shader) throw new Error("Unable to allocate WebGL shader");
    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);
    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) throw new Error(this.gl.getShaderInfoLog(shader) || "WebGL shader compile failed");
    return shader;
  }

  private link(vertex: string, fragment: string): WebGLProgram {
    const program = this.gl.createProgram();
    if (!program) throw new Error("Unable to allocate WebGL program");
    this.gl.attachShader(program, this.shader(this.gl.VERTEX_SHADER, vertex));
    this.gl.attachShader(program, this.shader(this.gl.FRAGMENT_SHADER, fragment));
    this.gl.linkProgram(program);
    if (!this.gl.getProgramParameter(program, this.gl.LINK_STATUS)) throw new Error(this.gl.getProgramInfoLog(program) || "WebGL program link failed");
    return program;
  }

  draw(agents: Agent[], view: View, width: number, height: number, dpr: number, selected: Agent["id"] | null) {
    const gl = this.gl;
    const pixelWidth = Math.max(1, Math.round(width * dpr));
    const pixelHeight = Math.max(1, Math.round(height * dpr));
    if (this.canvas.width !== pixelWidth || this.canvas.height !== pixelHeight) {
      this.canvas.width = pixelWidth;
      this.canvas.height = pixelHeight;
    }
    gl.viewport(0, 0, pixelWidth, pixelHeight);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    if (!agents.length) return;
    // x, y, point size, r, g, b, a; one interleaved upload per animation frame.
    const data = new Float32Array(agents.length * 7);
    const radius = Math.max(3, 0.25 * view.scale) * dpr;
    agents.forEach((agent, index) => {
      const offset = index * 7;
      data[offset] = view.ox + agent.x * view.scale;
      data[offset + 1] = view.oy + (view.height - agent.y) * view.scale;
      data[offset + 2] = radius * 2;
      const isSelected = agent.id === selected;
      const rgba = isSelected ? [1, 0.48, 0.1, 1] : agent.state === "waiting" ? [1, 0.35, 0.21, 1] : agent.state === "walking" ? [0.965, 0.906, 0.812, 1] : [0.66, 0.61, 0.55, 1];
      data.set(rgba, offset + 3);
    });
    gl.useProgram(this.program);
    gl.uniform2f(this.resolution, width, height);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
    const stride = 7 * Float32Array.BYTES_PER_ELEMENT;
    gl.enableVertexAttribArray(this.position);
    gl.vertexAttribPointer(this.position, 2, gl.FLOAT, false, stride, 0);
    gl.enableVertexAttribArray(this.size);
    gl.vertexAttribPointer(this.size, 1, gl.FLOAT, false, stride, 2 * Float32Array.BYTES_PER_ELEMENT);
    gl.enableVertexAttribArray(this.color);
    gl.vertexAttribPointer(this.color, 4, gl.FLOAT, false, stride, 3 * Float32Array.BYTES_PER_ELEMENT);
    gl.drawArrays(gl.POINTS, 0, agents.length);
  }

  dispose() {
    this.gl.deleteBuffer(this.buffer);
    this.gl.deleteProgram(this.program);
  }
}
