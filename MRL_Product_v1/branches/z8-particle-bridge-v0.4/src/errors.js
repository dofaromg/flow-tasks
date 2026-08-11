export class BridgeError extends Error {
  constructor(message, { code = "BRIDGE_ERROR", status = 400, details } = {}) {
    super(message);
    this.name = "BridgeError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export class DependencyError extends BridgeError {
  constructor(message, details) {
    super(message, { code: "DEPENDENCY_MISSING", status: 503, details });
    this.name = "DependencyError";
  }
}
