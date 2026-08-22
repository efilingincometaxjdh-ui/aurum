using System;
using System.Text.Json;
using cAlgo.API;

namespace cAlgo.Robots
{
    // Read-only market-data bridge. This cBot never places, modifies, or closes orders.
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class AurumMarketBridge : Robot
    {
        [Parameter("Aurum Endpoint", DefaultValue = "http://127.0.0.1:8000/api/market-data/ctrader-cbot")]
        public string AurumEndpoint { get; set; }

        [Parameter("Ingest Token", DefaultValue = "")]
        public string IngestToken { get; set; }

        [Parameter("Poll Seconds", DefaultValue = 5, MinValue = 1)]
        public int PollSeconds { get; set; }

        [Parameter("Historical Bars", DefaultValue = 250, MinValue = 50, MaxValue = 2000)]
        public int HistoricalBars { get; set; }

        private DateTime _lastSentOpenTime = DateTime.MinValue;
        private bool _initialised;

        protected override void OnStart()
        {
            Print("AurumMarketBridge started: {0} {1}", SymbolName, TimeFrame.ShortName);
            Print("Endpoint: {0}", AurumEndpoint);
            Print("Read-only mode: no trading operations are available.");

            Timer.Start(TimeSpan.FromSeconds(PollSeconds));
            SendLatestClosedBar();
        }

        protected override void OnTimer()
        {
            SendLatestClosedBar();
        }

        protected override void OnStop()
        {
            Timer.Stop();
            Print("AurumMarketBridge stopped.");
        }

        private void SendLatestClosedBar()
        {
            // The last index is the currently forming bar. Only transmit completed bars.
            if (Bars.Count < 3)
            {
                Print("Waiting for sufficient bars. Count={0}", Bars.Count);
                return;
            }

            var index = Bars.Count - 2;
            var openTime = Bars.OpenTimes[index];

            if (_initialised && openTime <= _lastSentOpenTime)
                return;

            var payload = new MarketBarPayload
            {
                SchemaVersion = 1,
                Provider = "ctrader_cbot",
                Symbol = SymbolName,
                Timeframe = TimeFrame.ShortName,
                Timestamp = openTime.ToUniversalTime(),
                Open = Bars.OpenPrices[index],
                High = Bars.HighPrices[index],
                Low = Bars.LowPrices[index],
                Close = Bars.ClosePrices[index],
                TickVolume = Bars.TickVolumes[index],
                Digits = Symbol.Digits
            };

            var json = JsonSerializer.Serialize(payload);
            var request = new HttpRequest(new Uri(AurumEndpoint));
            request.Method = HttpMethod.Post;
            request.Body = json;
            request.Headers.Add("Content-Type", "application/json");

            if (!string.IsNullOrWhiteSpace(IngestToken))
                request.Headers.Add("X-Aurum-Ingest-Token", IngestToken);

            Http.SendAsync(request, response =>
            {
                if (response.IsSuccessful)
                {
                    _lastSentOpenTime = openTime;
                    _initialised = true;
                    Print("Aurum accepted {0} {1} close={2}", SymbolName, TimeFrame.ShortName, payload.Close);
                }
                else
                {
                    Print("Aurum rejected {0} {1}: HTTP failure. Body={2}", SymbolName, TimeFrame.ShortName, response.Body);
                }
            });
        }

        private sealed class MarketBarPayload
        {
            public int SchemaVersion { get; set; }
            public string Provider { get; set; }
            public string Symbol { get; set; }
            public string Timeframe { get; set; }
            public DateTime Timestamp { get; set; }
            public double Open { get; set; }
            public double High { get; set; }
            public double Low { get; set; }
            public double Close { get; set; }
            public long TickVolume { get; set; }
            public int Digits { get; set; }
        }
    }
}
