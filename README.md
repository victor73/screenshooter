# screenshooter
Simple tool to take snapshots of websites for archival purposes. Python and Phantomjs. Modified from phantomjs-screenshots.

## Example Job File

  {
     "output":    "/path/to/my/screenshots/example.com/%y/example-%d.png",
     "viewport":  "1280x1024",
     "url":       "http://example.com",
     "useragent": "screenshooter",
     "waitfor":   "ul#ext-gen25",
     "timeout":   "15"
  }

### output

The output path to specifying where the image will be saved to. The %y token
is replaced with the 4 digit year, and the %d token is replace with the ISO
formatted date (YYYY-MM-DD). Required.

### viewport

The dimensions of the image to capture. Optional.

### url

The URL to capture. Required.

### useragent

The useragent to use when requesting the webpage. Some websites behave
differently with different browsers/clients. This allows the developer
to have fine control of that.

### waitfor

A DOM element that the . This is useful when website retrieve content
asynchronously via AJAX. If the screenshot is taken immediately when
the page has loaded, some elements or content might not be visible yet.
This config will make the browser wait for a particular DOM selector
to become visible before the screenshot is taken. Optional.

### timeout

The number of seconds to wait for the page to load. Optional.
