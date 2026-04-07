import {
  LineChart, Line, BarChart, Bar, RadarChart, Radar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts'

export default function ChartDisplay({ chart }) {
  if (!chart || !chart.data) return null

  const chartType = chart.type
  const data = chart.data.datasets && chart.data.labels
    ? transformChartData(chart)
    : chart.data

  const commonProps = {
    width: 100,
    height: 250,
    margin: { top: 5, right: 30, left: 0, bottom: 5 },
  }

  const ChartComponent = {
    line: () => (
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99, 102, 241, 0.1)" />
          <XAxis dataKey="name" stroke="rgba(241, 245, 249, 0.5)" style={{ fontSize: '12px' }} />
          <YAxis stroke="rgba(241, 245, 249, 0.5)" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgb(51, 65, 85)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'rgb(241, 245, 249)' }}
          />
          <Legend />
          {chart.data.datasets?.map((dataset, i) => (
            <Line
              key={i}
              type="monotone"
              dataKey={dataset.label}
              stroke={dataset.borderColor || '#6366f1'}
              strokeWidth={2}
              dot={{ fill: dataset.borderColor, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    ),

    bar: () => (
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(99, 102, 241, 0.1)" />
          <XAxis dataKey="name" stroke="rgba(241, 245, 249, 0.5)" style={{ fontSize: '12px' }} />
          <YAxis stroke="rgba(241, 245, 249, 0.5)" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgb(51, 65, 85)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'rgb(241, 245, 249)' }}
          />
          <Legend />
          {chart.data.datasets?.map((dataset, i) => (
            <Bar
              key={i}
              dataKey={dataset.label}
              fill={dataset.backgroundColor || '#6366f1'}
              radius={[8, 8, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    ),

    radar: () => (
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={data}>
          <PolarAngleAxis dataKey="name" stroke="rgba(241, 245, 249, 0.5)" style={{ fontSize: '12px' }} />
          <PolarRadiusAxis stroke="rgba(241, 245, 249, 0.3)" />
          <Radar name={chart.data.datasets?.[0]?.label} dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgb(51, 65, 85)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: 'rgb(241, 245, 249)' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    ),
  }

  return (
    <div className="w-full bg-dark-bg-secondary rounded-lg p-4 border border-dark-border">
      {ChartComponent[chartType] ? (
        ChartComponent[chartType]()
      ) : (
        <div className="text-center text-dark-text-muted">Unsupported chart type</div>
      )}
    </div>
  )
}

// Helper function to transform Chart.js format to Recharts format
function transformChartData(chart) {
  const labels = chart.data.labels || []
  const datasets = chart.data.datasets || []

  if (chart.type === 'line' || chart.type === 'bar') {
    return labels.map((label, i) => {
      const item = { name: label }
      datasets.forEach(dataset => {
        item[dataset.label] = dataset.data[i] || 0
      })
      return item
    })
  }

  if (chart.type === 'radar') {
    return labels.map((label, i) => ({
      name: label,
      value: datasets[0]?.data[i] || 0,
    }))
  }

  return []
}
