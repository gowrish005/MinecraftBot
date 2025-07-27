/**
 * Chart Enhancement Script
 * This file contains configurations to make charts look smoother and more visually appealing
 */

// Chart.js default configuration
Chart.defaults.font.family = "'Poppins', sans-serif";
Chart.defaults.color = '#9CA3AF';
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

// Enhanced common options for all charts
const enhancedChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    
    // Enhanced animation settings
    animation: {
        duration: 800,
        easing: 'easeOutQuart',
        delay: function(context) {
            return context.dataIndex * 50;
        }
    },
    
    // Smoother transitions
    transitions: {
        active: {
            animation: {
                duration: 400,
                easing: 'easeOutCubic'
            }
        }
    },
    
    // Improved interaction modes
    interaction: {
        mode: 'index',
        intersect: false,
        includeInvisible: false
    },
    
    // Enhanced tooltips
    plugins: {
        legend: {
            position: 'top',
            labels: {
                color: '#E5E7EB',
                usePointStyle: true,
                pointStyle: 'circle',
                padding: 20,
                font: {
                    size: 12,
                    weight: '500'
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.9)',
            titleColor: '#E5E7EB',
            bodyColor: '#E5E7EB',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            usePointStyle: true,
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed.y !== null) {
                        label += context.parsed.y.toFixed(1);
                    }
                    return label;
                }
            },
            animation: {
                duration: 150
            },
            // Add transition effects for tooltips
            transition: {
                duration: 200,
                easing: 'ease'
            }
        }
    },
    
    // Improved scales
    scales: {
        x: {
            grid: {
                color: 'rgba(255, 255, 255, 0.05)',
                tickLength: 8,
                tickWidth: 1
            },
            ticks: {
                color: '#9CA3AF',
                padding: 8,
                font: {
                    size: 11
                }
            },
            border: {
                color: 'rgba(255, 255, 255, 0.1)'
            }
        },
        y: {
            grid: {
                color: 'rgba(255, 255, 255, 0.05)',
                tickLength: 8,
                tickWidth: 1
            },
            ticks: {
                color: '#9CA3AF',
                padding: 8,
                font: {
                    size: 11
                },
                // Add this for smoother y-axis
                count: 6,
                stepSize: undefined
            },
            border: {
                color: 'rgba(255, 255, 255, 0.1)'
            }
        }
    },
      // Enhance elements
    elements: {
        line: {
            tension: 0.5, // Increases the smoothness of the line (higher value = smoother curve)
            borderWidth: 2.5,
            borderCapStyle: 'round',
            borderJoinStyle: 'round',
            capBezierPoints: true,
            fill: true
        },
        point: {
            radius: 4, // Normal point size
            hoverRadius: 6, // Point size on hover
            hitRadius: 30, // Sensitivity zone around points
            pointStyle: 'circle',
            borderWidth: 2,
            hoverBorderWidth: 2,
            hoverBackgroundColor: 'transparent'
        }
    }
};

// Function to apply enhanced options to a chart
function enhanceChart(chart) {
    // Deep merge default options with any existing chart options
    const mergedOptions = _.merge({}, enhancedChartOptions, chart.options);
    chart.options = mergedOptions;
    
    // Enhanced dataset default settings
    chart.data.datasets.forEach(dataset => {
        // Only apply to line charts
        if (chart.config.type === 'line') {            // Add cubic interpolation for smoother curves
            dataset.cubicInterpolationMode = 'monotone';
            
            // Set enhanced tension if not already specified
            if (dataset.tension === undefined) {
                dataset.tension = 0.5;
            }
            
            // Enhance the line drawing with better behaviors
            dataset.stepped = false; // Ensure smooth line, not stepped
            dataset.spanGaps = true; // Bridge null data gaps
            
            // Enhance fill options
            if (dataset.fill === true) {
                dataset.fill = {
                    target: 'origin',
                    above: dataset.backgroundColor || 'rgba(255, 255, 255, 0.1)'
                };
            }
            
            // Enhance point styling
            dataset.pointHoverBackgroundColor = dataset.borderColor;
            
            // Add subtle shadow to the line
            dataset.borderWidth = 2;
            dataset.borderColor = dataset.borderColor;
            dataset.backgroundColor = dataset.backgroundColor;
        }
    });
    
    // Update the chart with new options
    chart.update();
}

// Function to apply smoothing to chart data
function smoothChartData(data, smoothingFactor = 0.2) {
    if (!data || data.length <= 2) return data;
    
    const smoothedData = [data[0]]; // Keep the first point unchanged
    
    for (let i = 1; i < data.length - 1; i++) {
        // Calculate the smoothed value using Exponential Moving Average
        const previous = smoothedData[i - 1];
        const current = data[i];
        const smoothed = previous * (1 - smoothingFactor) + current * smoothingFactor;
        smoothedData.push(smoothed);
    }
    
    smoothedData.push(data[data.length - 1]); // Keep the last point unchanged
    
    return smoothedData;
}

// Function to enhance all charts on the page
function enhanceAllCharts() {
    try {
        // Get all registered charts
        const charts = Object.values(Chart.instances);
        
        // Apply enhanced options to each chart
        charts.forEach(chart => {
            // Ensure chart stability by enforcing consistent dimensions
            if (chart.canvas) {
                // Force maintainAspectRatio to true
                chart.options.maintainAspectRatio = true;
                chart.options.aspectRatio = chart.options.aspectRatio || 2;
                
                // Set responsive to true but with controlled dimensions
                chart.options.responsive = true;
                
                // Set a maximum size to prevent infinite growth
                chart.options.maxWidth = 1200;
                chart.options.maxHeight = 400;
                
                // Force chart to redraw at correct size
                chart.resize();
            }
            
            enhanceChart(chart);
            
            // Apply data smoothing to line charts
            if (chart.config.type === 'line') {
                chart.data.datasets.forEach(dataset => {
                    if (dataset.data && dataset.data.length > 3) {
                        // Apply light smoothing effect to make lines more natural
                        const smoothingFactor = 0.2; // Reduced for more stability
                        dataset.data = smoothChartData(dataset.data, smoothingFactor);
                    }
                });
            }
            
            // Use none mode to prevent animation-triggered resize issues
            chart.update('none');
        });
    } catch (error) {
        console.error("Error enhancing charts:", error);
    }
}

// Apply enhanced options when charts are initialized
document.addEventListener('DOMContentLoaded', function() {
    // Load dependencies
    const loadDependencies = async () => {
        // Load lodash
        await new Promise((resolve) => {
            const lodashScript = document.createElement('script');
            lodashScript.src = 'https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js';
            lodashScript.onload = resolve;
            document.head.appendChild(lodashScript);
        });
        
        // Wait for charts to initialize
        setTimeout(enhanceAllCharts, 150);
    };
    
    loadDependencies();
      // Re-enhance charts when window is resized, with proper debouncing
    let resizeTimer;
    window.addEventListener('resize', function() {
        // Clear and reset size on resize start to prevent cumulative growth
        Object.values(Chart.instances).forEach(chart => {
            if (chart.canvas) {
                // Reset any inline styles that might cause growth
                chart.canvas.style.height = '300px';
                chart.canvas.style.width = '100%';
            }
        });
        
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Force charts to redraw at proper size
            Object.values(Chart.instances).forEach(chart => {
                if (chart.canvas) {
                    chart.resize();
                    chart.update('none');
                }
            });
            
            // Then apply enhancements
            enhanceAllCharts();
        }, 250);
    });
});
