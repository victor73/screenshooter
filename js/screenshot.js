phantom.page.injectJs("moment.js");

var page = new WebPage();
var fs   = require('fs');

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


if (screenshot.hasOwnProperty('useragent')) {
    userAgent = screenshot['useragent'];
}

if (userAgent && userAgent !== "") {
    page.settings.userAgent = userAgent;
} else {
    page.settings.userAgent = 'Screenshooter';
}

page.viewportSize = { width: view_port[0], height: view_port[1] };

page.onLoadFinished = function (status) {
    if (status !== 'success') {
        phantom.exit(1);
    }
    var dateString = moment().format("YYYY-MM-DD-h:mm:ss");
    var year = moment().format("YYYY");

    output_path = output_path.replace(new RegExp('%d', 'g'), dateString);
    output_path = output_path.replace(new RegExp('%y', 'g'), year);
    var output_dir = dirname(output_path);

    // Attempt to make any intervening directories that are necessary
    fs.makeTree(output_dir);

    page.render(output_path);
    phantom.exit();
};

page.open(url);

function dirname(path) {
  return path.replace(/\\/g, '/').replace(/\/[^\/]*\/?$/, '');
}
