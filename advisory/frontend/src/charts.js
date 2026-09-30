import {
  BaselineSeries, CandlestickSeries, HistogramSeries, LineSeries, LineStyle, createChart, createSeriesMarkers,
} from "lightweight-charts";
import { alpha, token } from "./util.js";

function baseChart(container, height) {
  return createChart(container, {
    height,
    autoSize: true,
    localization: { locale: "en-IN" }, // Indian date/number format, independent of the browser's language
    layout: {
      background: { color: token("--ts-white") },
      textColor: token("--ts-gray-600"),
      fontFamily: token("--font-primary"),
      fontSize: 11,
      panes: { separatorColor: token("--ts-gray-200") },
    },
    grid: { vertLines: { color: token("--ts-gray-100") }, horzLines: { color: token("--ts-gray-100") } },
    rightPriceScale: { borderColor: token("--ts-gray-200") },
    timeScale: { borderColor: token("--ts-gray-200") },
  });
}

const quiet = { lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false };

/** Legend colours shared by the chart and its HTML legend. */
export const lineColors = () => ({
  sma20: token("--ts-yellow"), sma50: token("--ts-blue"), sma200: token("--ts-navy"),
  rsi: token("--ts-blue"), macd: token("--ts-blue"), signal: token("--ts-yellow"),
});

/**
 * Price candles with 20/50/200-DMA, plus RSI(14) and MACD(12,26,9) in their own panes.
 * If `call` is given, its entry / target / stop-loss lines and entry/exit markers are drawn too.
 */
export function indicatorChart(container, data, call = null) {
  const chart = baseChart(container, 460);
  const green = token("--ts-green"), red = token("--ts-red"), navy = token("--ts-navy");
  const colors = lineColors();
  const levels = call ? [call.entry, call.target, call.stop_loss] : [];

  const candles = chart.addSeries(CandlestickSeries, {
    upColor: green, downColor: red, wickUpColor: green, wickDownColor: red, borderVisible: false,
    // Stretch the price axis so target and stop loss stay on screen, not just the candles.
    autoscaleInfoProvider: (original) => {
      const r = original();
      if (r && levels.length) {
        r.priceRange.minValue = Math.min(r.priceRange.minValue, ...levels);
        r.priceRange.maxValue = Math.max(r.priceRange.maxValue, ...levels);
      }
      return r;
    },
  });
  candles.setData(data.bars.map((b) => ({ time: b.date, open: b.open, high: b.high, low: b.low, close: b.close })));
  for (const k of ["sma20", "sma50", "sma200"]) chart.addSeries(LineSeries, { ...quiet, color: colors[k] }).setData(data[k]);

  if (call) {
    const line = (price, color, title, style = LineStyle.Solid) =>
      candles.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title });
    line(call.entry, navy, "Entry", LineStyle.Dashed);
    line(call.target, token("--ts-green-text"), "Target");
    line(call.stop_loss, red, "SL");
    const markers = [{ time: call.issued_on, position: "belowBar", color: token("--ts-blue"), shape: "arrowUp", text: "BUY" }];
    if (call.closed_on) {
      markers.push({
        time: call.closed_on, position: "aboveBar", shape: "circle", text: "Exit",
        color: call.status === "TARGET_HIT" ? green : call.status === "SL_HIT" ? red : navy,
      });
    }
    createSeriesMarkers(candles, markers);
  }

  // Pane 1: RSI with 70 / 30 guide lines.
  const rsi = chart.addSeries(LineSeries, { ...quiet, lastValueVisible: true, color: colors.rsi }, 1);
  rsi.setData(data.rsi);
  for (const level of [70, 30]) {
    rsi.createPriceLine({ price: level, color: token("--ts-gray-400"), lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: false });
  }

  // Pane 2: MACD histogram + MACD and signal lines.
  chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false }, 2)
    .setData(data.macd_hist.map((p) => ({ ...p, color: alpha(p.value >= 0 ? green : red, 0.5) })));
  chart.addSeries(LineSeries, { ...quiet, color: colors.macd }, 2).setData(data.macd);
  chart.addSeries(LineSeries, { ...quiet, color: colors.signal }, 2).setData(data.macd_signal);

  const panes = chart.panes();
  panes[0].setStretchFactor(3);
  panes[1].setStretchFactor(1);
  panes[2].setStretchFactor(1);
  chart.timeScale().fitContent();
  return chart;
}

/** Cumulative P&L: green above zero, red below. */
export function equityChart(container, points) {
  const chart = baseChart(container, 260);
  const green = token("--ts-green"), red = token("--ts-red");
  const series = chart.addSeries(BaselineSeries, {
    baseValue: { type: "price", price: 0 },
    topLineColor: green, topFillColor1: alpha(green, 0.28), topFillColor2: alpha(green, 0.04),
    bottomLineColor: red, bottomFillColor1: alpha(red, 0.04), bottomFillColor2: alpha(red, 0.28),
    lineWidth: 2,
    priceFormat: { type: "custom", formatter: (v) => "₹" + Math.round(v).toLocaleString("en-IN") },
  });
  series.setData(points);
  chart.timeScale().fitContent();
  return chart;
}

/** Small inline SVG trend line for market cards (lighter than a full chart). */
export function sparkline(values, up) {
  const w = 120, h = 36, min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  const pts = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 2 - ((v - min) / span) * (h - 4)).toFixed(1)}`);
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.setAttribute("class", "spark");
  svg.setAttribute("aria-hidden", "true");
  const line = document.createElementNS(ns, "polyline");
  line.setAttribute("points", pts.join(" "));
  line.setAttribute("fill", "none");
  line.setAttribute("stroke", token(up ? "--ts-green" : "--ts-red"));
  line.setAttribute("stroke-width", "1.5");
  line.setAttribute("stroke-linejoin", "round");
  svg.append(line);
  return svg;
}
