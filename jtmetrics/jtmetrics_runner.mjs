import { calculateMetrics } from 'jtmetrics'
import fs from 'fs'
import path from 'path'
import zlib from 'zlib'

const [codePathArg, ignoreArg, rawOut] = process.argv.slice(2)
const codePath = path.resolve(codePathArg)
const ignore = ignoreArg && ignoreArg !== '-' ? path.resolve(ignoreArg) : undefined

// Metrics that embed AST nodes; the nodes are reduced to their non-AST fields
const FUNC_METRICS = ['functions-per-file', 'function-coupling']
const CLASS_METRICS = ['classes-per-file', 'class-coupling']
const KEEP = ['type', 'kind', 'static', 'async', 'generator', 'computed']

function obj (r) { return r && typeof r === 'object' ? r : {} }

// Node name, flags and fan-in/fan-out maps, without the AST
function slim (n) {
  if (!n || typeof n !== 'object') return n
  const o = {}
  const name = (n.key && (n.key.name ?? n.key.value)) ?? (n.id && n.id.name)
  if (name !== undefined) o.name = name
  for (const k of KEEP) if (k in n) o[k] = n[k]
  for (const k of Object.keys(n)) if (k.startsWith('fan')) o[k] = n[k]
  return o
}

// Paths relative to the package, with forward slashes
function rel (s) {
  if (typeof s !== 'string' || !s.includes(codePath)) return s
  if (s.startsWith(codePath)) return path.relative(codePath, s).split(path.sep).join('/')
  return s.split(codePath + path.sep).join('')
}

function relAll (x) {
  if (Array.isArray(x)) return x.map(relAll)
  if (x && typeof x === 'object') {
    return Object.fromEntries(Object.entries(x).map(([k, v]) => [rel(k), relAll(v)]))
  }
  return rel(x)
}

// Run JTMetrics
const res = await calculateMetrics({ codePath, metricsIgnoreFilePath: ignore })
const get = id => obj(res[id] && res[id].result)

// Package summary
const files = Array.isArray(res.files && res.files.result) ? res.files.result : []
const lines = get('lines-per-file')
const funcs = get('functions-per-file')
const classes = get('classes-per-file')
const coupling = get('file-coupling')
const instab = get('import-instability')

let nonEmpty = 0; let nFunctions = 0; let nClasses = 0
let edges = 0; let coupledFiles = 0; let instSum = 0; let instN = 0
for (const f of files) {
  nonEmpty += (lines[f] && lines[f].nonEmpty) || 0
  nFunctions += Object.keys(obj(funcs[f])).length
  nClasses += Object.keys(obj(classes[f])).length
  const c = obj(coupling[f])
  const out = Array.isArray(c.fanOut) ? c.fanOut.length : 0
  const inn = Array.isArray(c.fanIn) ? c.fanIn.length : 0
  edges += out
  if (out + inn > 0) coupledFiles += 1
  const i = obj(instab[f])
  if ((i.afferent || 0) + (i.efferent || 0) > 0) { instSum += i.instability; instN += 1 }
}
const errors = obj(res.errors)
const count = k => (Array.isArray(errors[k]) ? errors[k].length : 0)

const summary = {
  n_files: files.length,
  lines_non_empty: nonEmpty,
  n_functions: nFunctions,
  n_classes: nClasses,
  internal_edges: edges,
  coupled_files: coupledFiles,
  mean_instability: instN ? instSum / instN : null,
  parse_errors: count('parse'),
  file_errors: count('file'),
  traverse_errors: count('traverse'),
  metric_errors: count('metric')
}

// Per-file metrics without AST nodes, gzipped if the path ends in .gz
if (rawOut) {
  const raw = {}
  for (const [id, v] of Object.entries(res)) {
    if (id === 'errors') { raw.errors = v; continue }
    const r = obj(v && v.result)
    if (FUNC_METRICS.includes(id)) {
      raw[id] = Object.fromEntries(Object.entries(r).map(([f, fns]) =>
        [f, Object.fromEntries(Object.entries(obj(fns)).map(([fn, n]) => [fn, slim(n)]))]))
    } else if (CLASS_METRICS.includes(id)) {
      raw[id] = Object.fromEntries(Object.entries(r).map(([f, cls]) =>
        [f, Object.fromEntries(Object.entries(obj(cls)).map(([c, ms]) =>
          [c, Array.isArray(ms) ? ms.map(slim) : slim(ms)]))]))
    } else {
      raw[id] = v && v.result
    }
  }
  const text = JSON.stringify(relAll(raw))
  fs.writeFileSync(rawOut, rawOut.endsWith('.gz') ? zlib.gzipSync(text) : text)
}

process.stdout.write(JSON.stringify(summary) + '\n')
