import { BaselineSeries, CandlestickSeries, LineStyle, createChart, createSeriesMarkers } from "lightweight-charts";
import { alpha, token } from "./util.js";

function baseChart(container, height) {
  return createChart(container, {
    height,
    autoSize: true,
    localization: { locale: "en-IN" }, // Indian date/number format, independent of the browser's language
    layout: {
      background: { color: token("--ts-white") },
      textColor: token("--ts-gray-600"),
      fontFamily: token("--ts-font"),
      fontSize: 11,
    },
    grid: { vertLines: { color: token("--ts-gray-100") }, horzLines: { color: token("--ts-gray-100") } },
    rightPriceScale: { borderColor: token("--ts-hairline") },
    timeScale: { borderColor: token("--ts-hairline") },
  });
}

/** Daily candles with the call's entry, target and stop-loss lines, and entry/exit markers. */
export function callChart(container, call, bars) {
  const chart = baseChart(container, 280);
  const green = token("--ts-green"), red = token("--ts-red"), navy = token("--ts-navy");
  const levels = [call.entry, call.target, call.stop_loss];
  const series = chart.addSeries(CandlestickSeries, {
    upColor: green, downColor: red, wickUpColor: green, wickDownColor: red, borderVisible: false,
    // Stretch the price axis so target and stop loss are always on screen, not just the candles.
    autoscaleInfoProvider: (original) => {
      const r = original();
      if (!r) return r;
      r.priceRange.minValue = Math.min(r.priceRange.minValue, ...levels);
      r.priceRange.maxValue = Math.max(r.priceRange.maxValue, ...levels);
      return r;
    },
  });
  series.setData(bars.map((b) => ({ time: b.date, open: b.open, high: b.high, low: b.low, close: b.close })));

  const line = (price, color, title, style = LineStyle.Solid) =>
    series.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title });
  line(call.entry, navy, "Entry", LineStyle.Dashed);
  line(call.target, token("--ts-green-text"), "Target");
  line(call.stop_loss, red, "SL");

  const sell = call.action === "SELL";
  const markers = [{
    time: call.issued_on, position: sell ? "aboveBar" : "belowBar", color: token("--ts-blue"),
    shape: sell ? "arrowDown" : "arrowUp", text: call.action,
  }];
  if (call.closed_on) {
    markers.push({
      time: call.closed_on, position: "aboveBar", shape: "circle",
      color: call.status === "TARGET_HIT" ? green : call.status === "SL_HIT" ? red : navy,
      text: "Exit",
    });
  }
  createSeriesMarkers(series, markers);
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
