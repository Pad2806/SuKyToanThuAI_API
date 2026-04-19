// Shared bar chart used in AdminDashboard and AdminAnalytics

export default function Chart({ data }) {
  const max = Math.max(...data.map((d) => d.v));

  return (
    <div className="chart-bars">
      {data.map((d, i) => (
        <div key={i} className="chart-bar-wrap">
          <div
            className="chart-bar"
            style={{ height: `${(d.v / max) * 100}%` }}
          />
          <span className="chart-bar__label">{d.l}</span>
        </div>
      ))}
    </div>
  );
}
