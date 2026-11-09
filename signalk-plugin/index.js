// signalk-seastate: a measured sea state in Signal K from the heave a boat already has.
//
// A B&G / Simrad / Lowrance Precision-9 compass (and other motion-sensing compasses) puts heave
// on NMEA 2000 as PGN 127252 at 10 Hz. Signal K has a path for it, environment.heave, but the
// NMEA 2000 converter has no mapping for that PGN, and nothing anywhere turns heave into a wave
// height. This plugin does both:
//
//   environment.heave                     m     the compass's heave (optional, rate-limited)
//   environment.waves.significantHeight   m     Hs = 4 sqrt(m0), last ~20 min, every ~102 s
//   environment.waves.period              s     Tp, spectral peak; null when there is no clear peak
//   environment.waves.meanPeriod          s     Tz = sqrt(m0/m2); null with Tp
//   environment.waves.underway            bool  the boat moved during the window (periods are
//                                               then Doppler-shifted); needs SOG in Signal K
//
// The environment.waves.* paths are proposed, not in the specification; they are the ones the
// WaveHat sensor sends (../firmware/README.md), named after the Weather API's
// waveSignificantHeight and wavePeriod.
//
// Input: PGN 127252 as canboatjs decodes it (the server's 'N2KAnalyzerOut' event), or any Signal K
// path that already carries heave. The maths is seastate.js.
//
// Written 9 Nov 2026 against the canboat field names and the Signal K plugin API; the maths is
// tested (test/), the plugin has not yet run on a server with a real compass.

'use strict'

const { SeaState } = require('./seastate')

const KN = 0.514444

module.exports = function (app) {
  const plugin = {
    id: 'signalk-seastate',
    name: 'Sea state from heave',
    description: 'Significant wave height and period from NMEA 2000 heave (PGN 127252, e.g. a Precision-9 compass) or any heave path'
  }

  let unsubscribes = []
  let timers = []

  plugin.schema = {
    type: 'object',
    properties: {
      input: {
        type: 'string',
        title: 'Heave comes from',
        enum: ['n2k', 'path'],
        enumNames: ['NMEA 2000 PGN 127252 (Precision-9 and similar)', 'A Signal K path'],
        default: 'n2k'
      },
      n2kSource: {
        type: 'number',
        title: 'NMEA 2000 source address to follow (leave empty: the first one heard)'
      },
      inputPath: {
        type: 'string',
        title: 'Signal K path carrying heave in metres (when the input is a path)',
        default: 'environment.heave'
      },
      inputSource: {
        type: 'string',
        title: 'Only this $source for the path (leave empty: any)'
      },
      publishHeave: {
        type: 'boolean',
        title: 'Also publish the NMEA 2000 heave as environment.heave',
        default: true
      },
      heaveRateHz: {
        type: 'number',
        title: 'Rate for environment.heave, Hz',
        default: 2
      },
      outputPrefix: {
        type: 'string',
        title: 'Path prefix for the results',
        default: 'environment.waves'
      },
      underwaySpeedKn: {
        type: 'number',
        title: 'Underway above this speed over ground, knots',
        default: 1.5
      }
    }
  }

  plugin.start = function (options) {
    const opt = Object.assign({
      input: 'n2k',
      inputPath: 'environment.heave',
      publishHeave: true,
      heaveRateHz: 2,
      outputPrefix: 'environment.waves',
      underwaySpeedKn: 1.5
    }, options)
    const now = opt._now || (() => Date.now())
    const sea = new SeaState(opt.seastate)
    const prefix = opt.outputPrefix
    let metaSent = false
    let followSrc = Number.isFinite(opt.n2kSource) ? opt.n2kSource : null
    let followMs = 0
    let lastHeaveOut = 0
    let received = 0

    // SOG sampled once a second, kept for as long as the window spans.
    const sog = []
    const windowS = (sea.cfg.nfft + (sea.cfg.windowSegments - 1) * sea.cfg.hop) / sea.cfg.fs
    const sampleSog = () => {
      const v = app.getSelfPath('navigation.speedOverGround.value')
      if (typeof v === 'number' && Number.isFinite(v)) sog.push({ t: now(), v })
      while (sog.length && now() - sog[0].t > windowS * 1000) sog.shift()
    }
    if (!opt._noTimers) timers.push(setInterval(sampleSog, 1000))
    plugin._sampleSog = sampleSog

    // The firmware's rule (lib/underway): the mean SOG was above the limit, or SOG was above it
    // for more than a quarter of the window. null when there has been no SOG.
    const underway = () => {
      if (sog.length < 30) return null
      const limit = opt.underwaySpeedKn * KN
      let sum = 0; let above = 0
      for (const s of sog) {
        sum += s.v
        if (s.v > limit) above++
      }
      return sum / sog.length > limit || above / sog.length > 0.25
    }

    const meta = () => [
      { path: `${prefix}.significantHeight`, value: { units: 'm', displayName: 'Significant wave height', description: 'Hs = 4 sqrt(m0) of the vessel\'s heave, 0.04-0.5 Hz, last ~20 min' } },
      { path: `${prefix}.period`, value: { units: 's', displayName: 'Wave peak period', description: 'Tp: period of the heave spectrum\'s peak, last ~20 min; null with no clear peak' } },
      { path: `${prefix}.meanPeriod`, value: { units: 's', displayName: 'Wave mean period', description: 'Tz = sqrt(m0/m2), zero-crossing period, last ~20 min' } },
      { path: `${prefix}.underway`, value: { displayName: 'Waves measured underway', description: 'True if the vessel moved during the window: the periods are then Doppler-shifted' } }
    ]

    const publish = (st) => {
      const values = [
        { path: `${prefix}.significantHeight`, value: round(st.hs, 3) },
        { path: `${prefix}.period`, value: st.periodsValid ? round(st.tp, 2) : null },
        { path: `${prefix}.meanPeriod`, value: st.periodsValid ? round(st.tz, 2) : null }
      ]
      const uw = underway()
      if (uw !== null) values.push({ path: `${prefix}.underway`, value: uw })
      const update = { values }
      if (!metaSent) {
        update.meta = meta()
        metaSent = true
      }
      app.handleMessage(plugin.id, { updates: [update] })
      app.setPluginStatus(st.periodsValid
        ? `Hs ${st.hs.toFixed(2)} m, Tp ${st.tp.toFixed(1)} s, Tz ${st.tz.toFixed(1)} s (${st.segments} segments)`
        : `Hs ${st.hs.toFixed(2)} m, no clear wave period (${st.segments} segments)`)
    }

    const onHeave = (h) => {
      received++
      const st = sea.push(now(), h)
      if (st) publish(st)
    }

    if (opt.input === 'path') {
      const bus = app.streambundle.getSelfBus(opt.inputPath)
      unsubscribes.push(bus.onValue((d) => {
        if (opt.inputSource && d.$source !== opt.inputSource) return
        if (d.$source === plugin.id) return // never our own output
        if (typeof d.value === 'number') onHeave(d.value)
      }))
    } else {
      const listener = (msg) => {
        if (!msg || msg.pgn !== 127252 || !msg.fields) return
        const h = msg.fields.Heave !== undefined ? msg.fields.Heave : msg.fields.heave
        if (typeof h !== 'number' || !Number.isFinite(h)) return
        // One compass at a time: follow the first source, move on after 5 s of silence.
        const t = now()
        if (followSrc !== null && msg.src !== followSrc) {
          if (Number.isFinite(opt.n2kSource) || t - followMs < 5000) return
        }
        followSrc = msg.src
        followMs = t
        onHeave(h)
        if (opt.publishHeave && t - lastHeaveOut >= 1000 / opt.heaveRateHz) {
          lastHeaveOut = t
          app.handleMessage(plugin.id, { updates: [{ values: [{ path: 'environment.heave', value: round(h, 3) }] }] })
        }
      }
      app.on('N2KAnalyzerOut', listener)
      unsubscribes.push(() => app.removeListener('N2KAnalyzerOut', listener))
    }

    const status = () => {
      if (sea.stats) return
      if (received === 0) {
        app.setPluginStatus(opt.input === 'path'
          ? `Waiting for heave on ${opt.inputPath}`
          : 'Waiting for NMEA 2000 PGN 127252 (heave)')
      } else {
        app.setPluginStatus(`Collecting: first result in about ${Math.ceil(sea.secondsToFirst() / 60)} min` +
          (followSrc !== null && opt.input !== 'path' ? ` (heave from N2K source ${followSrc})` : ''))
      }
    }
    status()
    if (!opt._noTimers) timers.push(setInterval(status, 10000))
    plugin._sea = sea
  }

  plugin.stop = function () {
    unsubscribes.forEach((f) => f())
    unsubscribes = []
    timers.forEach(clearInterval)
    timers = []
  }

  return plugin
}

function round (v, digits) {
  const f = Math.pow(10, digits)
  return Math.round(v * f) / f
}
