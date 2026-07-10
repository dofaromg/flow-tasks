#!/usr/bin/env python3
"""
Generate a TypeScript MetaEnv API client from the OpenAPI spec.
Usage: python3 generate_metaenv_client.py [--output /path/to/output.ts]
"""
import json
import yaml
import sys
import os
import argparse

def load_spec(spec_path):
    with open(spec_path, 'r') as f:
        content = f.read()
    try:
        return yaml.safe_load(content)
    except:
        return json.loads(content)

def ts_type_from_schema(schema, indent=2):
    if not schema:
        return 'unknown'
    t = schema.get('type', 'any')
    if '$ref' in schema:
        return schema['$ref'].split('/')[-1]
    if t == 'string':
        if 'enum' in schema:
            return ' | '.join(f'"{v}"' for v in schema['enum'])
        return 'string'
    if t == 'integer' or t == 'number':
        return 'number'
    if t == 'boolean':
        return 'boolean'
    if t == 'array':
        item_type = ts_type_from_schema(schema.get('items', {}), indent)
        return f'{item_type}[]'
    if t == 'object':
        props = schema.get('properties', {})
        if not props:
            return 'Record<string, unknown>'
        lines = []
        required = schema.get('required', [])
        for name, prop in props.items():
            opt = '' if name in required else '?'
            pt = ts_type_from_schema(prop, indent + 2)
            lines.append(f'{" " * indent}{name}{opt}: {pt};')
        return '{\n' + '\n'.join(lines) + f'\n{" " * (indent - 2)}}}'
    return 'unknown'

def generate_client(spec):
    lines = []
    lines.append('// Auto-generated MetaEnv API Client')
    lines.append(f'// From: {spec["info"]["title"]} {spec["info"]["version"]}')
    lines.append('')
    lines.append('type MetaEnvConfig = {')
    lines.append('  baseUrl: string;')
    lines.append('  headers?: Record<string, string>;')
    lines.append('};')
    lines.append('')

    # Generate type interfaces from schemas
    schemas = spec.get('components', {}).get('schemas', {})
    for name, schema in schemas.items():
        ts = ts_type_from_schema(schema, 2)
        lines.append(f'export type {name} = {ts};')
        lines.append('')

    # Generate client class
    lines.append('export class MetaEnvClient {')
    lines.append('  private baseUrl: string;')
    lines.append('  private headers: Record<string, string>;')
    lines.append('')
    lines.append('  constructor(config: MetaEnvConfig) {')
    lines.append('    this.baseUrl = config.baseUrl.replace(/\\/$/, "");')
    lines.append('    this.headers = { "Content-Type": "application/json", ...config.headers };')
    lines.append('  }')
    lines.append('')
    lines.append('  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {')
    lines.append('    const res = await fetch(`${this.baseUrl}${path}`, {')
    lines.append('      method,')
    lines.append('      headers: this.headers,')
    lines.append('      body: body ? JSON.stringify(body) : undefined,')
    lines.append('    });')
    lines.append('    if (!res.ok) throw new Error(`MetaEnv ${method} ${path}: ${res.status}`);')
    lines.append('    return res.json() as T;')
    lines.append('  }')
    lines.append('')

    # Generate methods from paths
    for path, methods in spec.get('paths', {}).items():
        for method, op in methods.items():
            if method in ('parameters', 'servers'):
                continue
            op_id = op.get('operationId', path.replace('/', '_'))
            summary = op.get('summary', '')
            fn_name = op_id[0].lower() + op_id[1:]

            # Determine request/response types
            req_schema = None
            req_type = 'void'
            if 'requestBody' in op:
                content = op['requestBody'].get('content', {})
                if 'application/json' in content:
                    s = content['application/json'].get('schema', {})
                    if '$ref' in s:
                        req_type = s['$ref'].split('/')[-1]
                    else:
                        req_type = 'Record<string, unknown>'

            res_schema = op.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema', {})
            if '$ref' in res_schema:
                res_type = res_schema['$ref'].split('/')[-1]
            elif res_schema:
                res_type = 'Record<string, unknown>'
            else:
                res_type = 'void'

            lines.append(f'  /** {summary} */')
            if method == 'get':
                lines.append(f'  async {fn_name}(params?: Record<string, string>): Promise<{res_type}> {{')
                lines.append(f'    const qs = params ? "?" + new URLSearchParams(params).toString() : "";')
                lines.append(f'    return this.request<{res_type}>("GET", `{path}${{qs}}`);')
            else:
                if req_type != 'void':
                    lines.append(f'  async {fn_name}(body: {req_type}): Promise<{res_type}> {{')
                    lines.append(f'    return this.request<{res_type}>("{method.upper()}", "{path}", body);')
                else:
                    lines.append(f'  async {fn_name}(): Promise<{res_type}> {{')
                    lines.append(f'    return this.request<{res_type}>("{method.upper()}", "{path}");')
            lines.append('  }')
            lines.append('')

    lines.append('}')
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate MetaEnv TS client')
    parser.add_argument('--spec', default=os.path.join(os.path.dirname(__file__), '..', 'references', 'metaenv_openapi.yaml'))
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    spec = load_spec(args.spec)
    code = generate_client(spec)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(code)
        print(f'✅ Generated: {args.output}')
    else:
        print(code)

if __name__ == '__main__':
    main()
