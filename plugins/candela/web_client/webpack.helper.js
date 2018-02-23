var path = require('path');

module.exports = function (config) {
    var candelaDir = path.resolve(path.dirname(require.resolve('candela')));

    config.module.rules.push({
        resource: {
            test: new RegExp(candelaDir + '.*.js$'),
            include: [candelaDir]
        },
        use: [
            {
                loader: 'babel-loader',
                options: {
                    presets: ['env']
                }
            }
        ]
    });

    return config;
};
