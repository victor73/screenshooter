var system = require("system");
var moment_inj = phantom.page.injectJs("moment.js");
var jquery_inj = phantom.page.injectJs("jquery-1.9.1.min.js");

if (moment_inj === false || jquery_inj == false) {
    console.log("Unable to inject javascript libraries.");
    phantom.exit();
}

var page = new WebPage();
var fs   = require('fs');

page.waitForSelector = function(config, callback) {
    console.log("In waitForSelector.");
    var timer = 1;

    var stop   = function(timer) {
        console.log("In stop");
        clearTimeout(timer);
        timer = 0;
    }

    //console.log(JSON.stringify(config));

    config._start = config._start || new Date();

    if (config.timeout && new Date() - config._start > config.timeout) {
        var err = 'Timed out ' + (new Date() - config._start) + 'ms';
        if (config.debug) {
             console.log(err);
        }

        if (config.error) {
             config.error();
        }

        callback(err);
    }

    console.log("Checking selector: " + config.selector);

    var visible = page.evaluate(function(selector) {
        console.log("REMOTE: " + selector);
        if ($(selector).is(':visible')) {
            return true;
        } else {
            return false;
        }
    }, config.selector);

    if (visible) {
        console.log("Selector visible!");

        if (config.debug) {
            console.log('Success ' + (new Date() - config._start) + 'ms');
        }

        if (config.hasOwnProperty('success')) {
            config.success;
        } else {
             console.log("Clearing timer.");
             stop(timer);
             timer = 0;
             callback(null);
        }
    } else {
        console.log("Selector not yet visible.");
        timer = setTimeout(page.waitForSelector, config.interval || 0, config, callback);
    }
};

page.viewportSize = { width: 1600, height: 1200 };

if (phantom.args.length !== 1) {
    console.log('Usage: screenshot.js <site.json>');
    phantom.exit();
}

var data;
var screenshot;

try {
    data = fs.read(phantom.args[0]);
    screenshot = JSON.parse(data);
} catch (e) {
    console.log(e);
}

var userAgent =  null;

var view_port  = screenshot['viewport'].split(/x/);
var output_path = screenshot['output'];
var url = screenshot['url'];

if (screenshot.hasOwnProperty('waitfor')) {
    var selector = screenshot['waitfor'];

    var config = { debug: true,
                   selector: selector,
                   interval: 500,
                   timeout: 10000,
                   //success: function() {
                      // we have what we want
                    //  console.log("Success");
                   //},
                   error: function() {
                      console.log("Looks like " + selector + " might never exist. Timed out.");
                   }
    };
}

if (screenshot.hasOwnProperty('useragent')) {
    userAgent = screenshot['useragent'];
}

if (userAgent && userAgent !== "") {
    page.settings.userAgent = userAgent;
} else {
    page.settings.userAgent = 'Screenshooter';
}

page.viewportSize = { width: view_port[0], height: view_port[1] };

page.onConsoleMessage = function(msg) {
    system.stderr.writeLine('console: ' + msg);
};

page.onLoadFinished = function (status) {
    if (screenshot.hasOwnProperty('waitfor')) {
        page.waitForSelector(config, function(err) {
            console.log("Done waiting.");

            if (err || status !== 'success') {
                if (err) {
                    console.log(err);
                }
                phantom.exit(1);
            }

            finish(phantom, page);
        });
    } else {
        finish(phantom, page);
    }
};

page.open(url);

function dirname(path) {
    return path.replace(/\\/g, '/').replace(/\/[^\/]*\/?$/, '');
}

function finish(phantom, page) {
    var dateString = moment().format("YYYY-MM-DD-h:mm:ss");
    var year = moment().format("YYYY");

    output_path = output_path.replace(new RegExp('%d', 'g'), dateString);
    output_path = output_path.replace(new RegExp('%y', 'g'), year);
    var output_dir = dirname(output_path);

    // Attempt to make any intervening directories that are necessary
    fs.makeTree(output_dir);

    page.render(output_path);

    phantom.exit();
}


