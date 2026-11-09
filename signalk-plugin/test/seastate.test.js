'use strict'

const test = require('node:test')
const assert = require('node:assert')
const { EventEmitter } = require('node:events')
const { SeaState } = require('../seastate')
const makePlugin = require('../index')

// A deterministic generator, so the jitter and noise are the same every run.
function rng (seed) {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 4294967296
  }
}

// Feeds heave(t) at 10 Hz with +-20 ms of jitter for `seconds`; returns the last result.
function run (sea, heave, seconds, seed = 1, t0 = 1e6) {
  const r = rng(seed)
  let last = null
  for (let i = 0; i < seconds * 10; i++) {
    const t = t0 + i * 100 + (r() - 0.5) * 40
    const st = sea.push(t, heave(t / 1000))
    if (st) last = st
  }
  return last
}

const near = (a, b, tol, what) => assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} not within ${tol} of ${b}`)

test('a single 0.50 m, 8 s swell: Hs 1.414 m, Tp and Tz 8 s', () => {
  const st = run(new SeaState(), (t) => 0.5 * Math.sin(2 * Math.PI * t / 8), 25 * 60)
  near(st.hs, 4 * 0.5 / Math.SQRT2, 0.03, 'Hs')
  near(st.tp, 8, 0.15, 'Tp')
  near(st.tz, 8, 0.25, 'Tz')
  assert.strictEqual(st.segments, 11)
  assert.ok(st.periodsValid)
})

test('first result after about 10 minutes, none before', () => {
  const sea = new SeaState()
  assert.strictEqual(run(sea, (t) => 0.3 * Math.sin(2 * Math.PI * t / 6), 9 * 60), null)
  assert.ok(sea.secondsToFirst() > 0 && sea.secondsToFirst() < 120)
  // 512 + 4 x 256 samples at 2.5 Hz = 614 s; the sixth segment would come at 717 s
  const st = run(sea, (t) => 0.3 * Math.sin(2 * Math.PI * t / 6), 2 * 60, 2, 1e6 + 9 * 60 * 1000)
  assert.ok(st && st.segments === 5, `segments ${st && st.segments}`)
})

test('a mixed sea: Hs from the summed variance, Tp at the bigger component', () => {
  // 0.6 m at 10 s swell, 0.25 m at 4 s wind sea, 0.1 m at 2.5 s chop
  const comps = [[0.6, 10, 0.3], [0.25, 4, 1.1], [0.1, 2.5, 2.0]]
  const m0 = comps.reduce((s, [a]) => s + a * a / 2, 0)
  const st = run(new SeaState(), (t) => comps.reduce((s, [a, T, ph]) => s + a * Math.sin(2 * Math.PI * t / T + ph), 0), 25 * 60)
  near(st.hs, 4 * Math.sqrt(m0), 0.04 * 4 * Math.sqrt(m0), 'Hs')
  near(st.tp, 10, 0.3, 'Tp')
  assert.ok(st.tz < 10 && st.tz > 4, `Tz ${st.tz} between the components`)
})

test('short 2.5 s chop is not lost to the 0.4 s averaging', () => {
  const st = run(new SeaState(), (t) => 0.2 * Math.sin(2 * Math.PI * t / 2.5), 25 * 60)
  near(st.hs, 4 * 0.2 / Math.SQRT2, 0.03, 'Hs')
  near(st.tp, 2.5, 0.05, 'Tp')
})

test('flat calm: a height near zero and no period', () => {
  const r = rng(7)
  const st = run(new SeaState(), () => (r() - 0.5) * 0.02, 25 * 60)
  assert.ok(st.hs < 0.05, `Hs ${st.hs}`)
  assert.strictEqual(st.periodsValid, false)
})

test('a slow drift outside the band does not read as waves', () => {
  // a 2-minute 0.3 m wander (a compass's heave filter settling) under a 0.2 m, 6 s sea
  const st = run(new SeaState(), (t) => 0.3 * Math.sin(2 * Math.PI * t / 120) + 0.2 * Math.sin(2 * Math.PI * t / 6), 25 * 60)
  near(st.hs, 4 * 0.2 / Math.SQRT2, 0.04, 'Hs')
  near(st.tp, 6, 0.15, 'Tp')
})

test('a gap in the input starts the window again', () => {
  const sea = new SeaState()
  const wave = (t) => 0.5 * Math.sin(2 * Math.PI * t / 8)
  assert.ok(run(sea, wave, 12 * 60))
  sea.push(1e6 + 12 * 60 * 1000 + 60000, 0.1) // a minute of silence
  assert.strictEqual(sea.stats, null)
  assert.strictEqual(sea.resets, 1)
})

// A stand-in for the Signal K server: enough of the plugin API to drive the plugin.
function fakeApp () {
  const app = new EventEmitter()
  app.deltas = []
  app.status = ''
  app.sog = undefined
  app.handleMessage = (id, delta) => app.deltas.push({ id, delta })
  app.setPluginStatus = (s) => { app.status = s }
  app.getSelfPath = (p) => (p === 'navigation.speedOverGround.value' ? app.sog : undefined)
  app.valuesOf = (path) => app.deltas.flatMap((d) => d.delta.updates.flatMap((u) => u.values)).filter((v) => v.path === path).map((v) => v.value)
  return app
}

test('plugin: PGN 127252 in, environment.heave and environment.waves.* out', () => {
  const app = fakeApp()
  const plugin = makePlugin(app)
  let clock = 5e6
  plugin.start({ _now: () => clock, _noTimers: true })
  assert.match(app.status, /Waiting for NMEA 2000 PGN 127252/)
  app.sog = 0.1
  for (let i = 0; i < 25 * 60 * 10; i++) {
    clock += 100
    const h = 0.5 * Math.sin(2 * Math.PI * (clock / 1000) / 8)
    app.emit('N2KAnalyzerOut', { pgn: 127252, src: 35, fields: { SID: 0, Heave: h, Delay: 0 } })
    app.emit('N2KAnalyzerOut', { pgn: 127252, src: 77, fields: { Heave: 9.0 } }) // a second source: ignored
    app.emit('N2KAnalyzerOut', { pgn: 127257, src: 35, fields: { Roll: 0.1 } }) // another PGN: ignored
    if (i % 10 === 0) plugin._sampleSog()
  }
  const hs = app.valuesOf('environment.waves.significantHeight')
  assert.ok(hs.length >= 5)
  near(hs[hs.length - 1], 1.414, 0.03, 'Hs')
  near(app.valuesOf('environment.waves.period').pop(), 8, 0.15, 'Tp')
  assert.strictEqual(app.valuesOf('environment.waves.underway').pop(), false)
  const heave = app.valuesOf('environment.heave')
  near(heave.length, 25 * 60 * 2, 5, 'environment.heave at 2 Hz')
  assert.ok(Math.max(...heave) <= 0.5)
  // metadata goes out once, with the first result
  const metas = app.deltas.flatMap((d) => d.delta.updates).filter((u) => u.meta)
  assert.strictEqual(metas.length, 1)
  assert.strictEqual(metas[0].meta[0].value.units, 'm')
  assert.match(app.status, /Hs 1\.4\d m, Tp 8\.\d s/)
  plugin.stop()
  assert.strictEqual(app.listenerCount('N2KAnalyzerOut'), 0)
})

test('plugin: camelCase canboat fields, underway when the boat is moving, null periods in a calm', () => {
  const app = fakeApp()
  const plugin = makePlugin(app)
  let clock = 5e6
  const r = rng(3)
  plugin.start({ _now: () => clock, _noTimers: true })
  app.sog = 3.0
  for (let i = 0; i < 12 * 60 * 10; i++) {
    clock += 100
    app.emit('N2KAnalyzerOut', { pgn: 127252, src: 35, fields: { heave: (r() - 0.5) * 0.02 } })
    if (i % 10 === 0) plugin._sampleSog()
  }
  assert.ok(app.valuesOf('environment.waves.significantHeight').pop() < 0.05)
  assert.strictEqual(app.valuesOf('environment.waves.period').pop(), null)
  assert.strictEqual(app.valuesOf('environment.waves.meanPeriod').pop(), null)
  assert.strictEqual(app.valuesOf('environment.waves.underway').pop(), true)
  plugin.stop()
})

test('plugin: a Signal K path as the input, ignoring its own output', () => {
  const app = fakeApp()
  const handlers = []
  app.streambundle = { getSelfBus: (path) => ({ onValue: (f) => { handlers.push({ path, f }); return () => handlers.pop() } }) }
  const plugin = makePlugin(app)
  let clock = 5e6
  plugin.start({ input: 'path', inputPath: 'environment.heave', inputSource: 'wavehat', _now: () => clock, _noTimers: true })
  assert.strictEqual(handlers[0].path, 'environment.heave')
  for (let i = 0; i < 12 * 60 * 4; i++) {
    clock += 250
    handlers[0].f({ value: 0.4 * Math.sin(2 * Math.PI * (clock / 1000) / 7), $source: 'wavehat' })
    handlers[0].f({ value: 5, $source: 'something-else' })
  }
  near(app.valuesOf('environment.waves.significantHeight').pop(), 4 * 0.4 / Math.SQRT2, 0.03, 'Hs')
  assert.strictEqual(app.valuesOf('environment.heave').length, 0)
  plugin.stop()
  assert.strictEqual(handlers.length, 0)
})
