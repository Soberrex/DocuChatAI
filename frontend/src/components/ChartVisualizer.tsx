import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell,
} from 'recharts';

interface ChartVisualizerProps {
    data: any;
    title?: string;
    type?: 'bar' | 'line' | 'pie';
}

const COLORS = ['#E05A2B', '#F59E0B', '#22C55E', '#3B82F6', '#8B5CF6', '#EC4899'];

const ChartVisualizer = ({ data, title, type = 'bar' }: ChartVisualizerProps) => {
    if (!data || !data.data || data.data.length === 0) return null;
    const chartData = data.data;
    const dataKeys = Object.keys(chartData[0]).filter((k) => k !== 'name');
    const tip = { backgroundColor: '#1A1A1A', borderColor: '#1F1F1F', borderRadius: '8px', color: '#FFF', fontSize: '12px' };

    const renderChart = () => {
        switch (type) {
            case 'line':
                return (
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                        <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
                        <YAxis stroke="#6B7280" fontSize={12} />
                        <Tooltip contentStyle={tip} />
                        <Legend />
                        {dataKeys.map((k, i) => <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} />)}
                    </LineChart>
                );
            case 'pie':
                return (
                    <PieChart>
                        <Pie data={chartData} cx="50%" cy="50%" outerRadius={80} dataKey={dataKeys[0]}
                            label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}>
                            {chartData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={tip} />
                    </PieChart>
                );
            default:
                return (
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                        <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
                        <YAxis stroke="#6B7280" fontSize={12} />
                        <Tooltip contentStyle={tip} />
                        <Legend />
                        {dataKeys.map((k, i) => <Bar key={k} dataKey={k} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />)}
                    </BarChart>
                );
        }
    };

    return (
        <div className="my-3 p-4 bg-card border border-edge rounded-xl overflow-hidden">
            {title && <p className="text-sm font-semibold text-primary text-center mb-3">{title}</p>}
            <ResponsiveContainer width="100%" height={280}>{renderChart()}</ResponsiveContainer>
        </div>
    );
};

export default ChartVisualizer;
