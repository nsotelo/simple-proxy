# A python proxy made from the stdlib

This is made to work with the latest versions of python, I've adapted it from [this gist](https://gist.github.com/darkwave/52842722c0c451807df4) and have tested with python 3.7 and 3.8.

It's not yet been production hardened and is very basic, but hopefully it's simple enough that you can adapt it to your needs. I've been using to give more control over the proxy used by a selenium web browser and it does what I need, although being single-threaded brings a noticeable performance impact.

## Usage

Since it's just the python stdlib, no virtual env is needed. Just clone and run `./proxy.py` or if you're feeling brave

```
curl https://raw.githubusercontent.com/alephu5/simple-proxy/master/proxy.py | python3
```

It will automatically bind to a free port on localhost and show a log message so you can try it out. I've picked a random free proxy for testing this out so can't guarantee if it'll work, but it should be obvious how to modify this.
