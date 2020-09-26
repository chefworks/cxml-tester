# cXML Tester
[![Build Status](https://img.shields.io/github/workflow/status/chefworks/cxml-tester/ci-tests)](https://github.com/chefworks/cxml-tester)

cXML Tester is a [cXML]((http://xml.cxml.org/current/cXMLReferenceGuide.pdf)) data posting tool for 
testing [Procurement PunchOut](https://en.wikipedia.org/wiki/CXML) vendor implementations.

## Features
- Compared to using plain `curl`, the cXML Tester web UI makes it somewhat easier to edit the cXML data before posting
and inspect results.
- XDEBUG session initiation (usefule for debugging local end-points written in PHP)

----
![Screenshot](p6t/static/img/screenshot-1.png)
----

see [cXML Reference Guide](http://xml.cxml.org/current/cXMLReferenceGuide.pdf) for general
infromation about the cXML protocol and syntax

## Running locally
### Requirements
- make
- python3
- docker

### Run

```
make init
make run
```

Then go to http://localhost:8080


## Running using docker

```
docker run -d -p 8080:8080 chefworks/cxml-tester
```
