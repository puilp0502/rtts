const path = require('path');
const webpack = require('webpack');
const config = {
    entry: {
        index: './index.js',
        app: './app.js',
        vendor: './vendor.js'
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        publicPath: '/static/dist/',
        filename: '[name].bundle.js'
    },
    module: {
        loaders: [
            { test: /\.(njk|nunjucks)$/,
                loader: 'nunjucks-loader'
            },
            { test: /\.css$/, loader: "style!css" },
            { test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader:"url-loader?limit=10000&mimetype=application/font-woff" },
            { test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: "file" }
        ]
    },
    plugins: [
        new webpack.optimize.CommonsChunkPlugin(/* chunkName= */"vendor", /* filename= */"vendor.bundle.js"),
    ]
};

module.exports = config;
