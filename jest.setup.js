// Jest setup file
// Mock WebGPU globals for testing in Node environment

global.navigator = global.navigator || {};
global.navigator.gpu = undefined; // WebGPU not available in test environment

global.WebGLRenderingContext = global.WebGLRenderingContext || function() {};
global.WebAssembly = global.WebAssembly || {};
